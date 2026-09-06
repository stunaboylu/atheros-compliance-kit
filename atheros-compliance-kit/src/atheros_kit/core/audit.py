"""Immutable, hash-chained audit trail (ISO/IEC 42001 §9.1 traceability).

Every event is appended to a JSONL file with a SHA-256 digest that chains to the
previous entry, so removing, reordering, or editing an entry is detectable.

Two properties here are load-bearing and were each a real defect once:

1. **The chain head is read from the file, under the lock — never from a module
   global.** A global is per-process state describing a file that several
   processes share; it starts at GENESIS on every import, so each worker begins a
   fresh chain in the middle of an existing one.
2. **The writer and the verifier hash exactly the same field set** —
   `_chained_payload`, one definition used by both. When they disagreed, every
   line of every ledger verified as tampered, which means the check returned the
   same answer for an intact file as for a forged one and could distinguish
   neither.
"""
from __future__ import annotations

import hashlib
import json
import os
import threading
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterator

from . import i18n
from .errors import LedgerViolation

try:  # POSIX advisory locking; absent on Windows.
    import fcntl
except ImportError:  # pragma: no cover - platform dependent
    fcntl = None  # type: ignore[assignment]

GENESIS = "GENESIS"
DEFAULT_AUDIT_FILE = Path(os.environ.get("ATHEROS_AUDIT_FILE", ".atheros/audit_trail.jsonl"))

# Guards the read-modify-append against other threads in THIS process. The file
# lock guards it against other processes. Both are needed: a file lock is
# advisory per open file description and does not serialise threads sharing one.
_LOCAL_LOCK = threading.Lock()


def _sha256(payload: dict[str, Any], prev: str) -> str:
    return hashlib.sha256(
        (json.dumps(payload, sort_keys=True, ensure_ascii=False) + prev).encode("utf-8")
    ).hexdigest()


def _chained_payload(entry: dict[str, Any]) -> dict[str, Any]:
    """The fields the digest covers: the event, without the chain fields."""
    return {k: v for k, v in entry.items() if k not in ("hash", "previous_hash")}


def _lock(fh, exclusive: bool = True) -> None:
    if fcntl is not None:
        fcntl.flock(fh.fileno(), fcntl.LOCK_EX if exclusive else fcntl.LOCK_SH)


def _unlock(fh) -> None:
    if fcntl is not None:
        fcntl.flock(fh.fileno(), fcntl.LOCK_UN)


def _last_hash(fh) -> str:
    """Digest of the final entry on disk, or GENESIS for an empty file.

    Walks backwards over an 8 KiB tail rather than reading the whole ledger:
    this runs on every append and the file only ever grows.
    """
    fh.seek(0, os.SEEK_END)
    size = fh.tell()
    if size == 0:
        return GENESIS
    block = min(8192, size)
    fh.seek(size - block)
    tail = fh.read().decode("utf-8", errors="replace").strip().splitlines()
    for raw in reversed(tail):
        if raw.strip():
            try:
                return json.loads(raw)["hash"]
            except (json.JSONDecodeError, KeyError):
                continue
    # The tail held no parseable entry — re-read from the start rather than guess.
    fh.seek(0)
    last = GENESIS
    for raw in fh.read().decode("utf-8", errors="replace").splitlines():
        if raw.strip():
            try:
                last = json.loads(raw)["hash"]
            except (json.JSONDecodeError, KeyError):
                continue
    return last


class AuditTrail:
    """An append-only, hash-chained event log.

    Instantiate per file. The default instance (`default_trail()`) is what the
    modules use when a caller does not pass one.
    """

    #: ISO/IEC 42001 clause each event class evidences. Written onto the entry so
    #: an auditor reading the raw JSONL does not need this source file.
    CLAUSES = {
        "guard": "8.3 — Operational controls / AI system operation",
        "rag": "8.4 — Data for AI systems (and Art. 10 EU AI Act)",
        "euact": "6.1.2 — AI risk assessment",
        "vendor": "8.5 — Third-party and customer relationships",
        "cicd": "9.1 — Monitoring, measurement, analysis and evaluation",
        "core": "9.1 — Monitoring, measurement, analysis and evaluation",
    }

    def __init__(self, path: str | Path | None = None):
        self.path = Path(path) if path is not None else DEFAULT_AUDIT_FILE

    # ── write ────────────────────────────────────────────────────────────────
    def log(
        self,
        module: str,
        event_type: str,
        payload: dict[str, Any],
        *,
        session_id: str | None = None,
    ) -> dict[str, Any]:
        """Append one immutable entry and return it (with `hash`/`previous_hash`).

        `payload` must already be redacted: the ledger records entity CLASSES and
        counts, never detected values. A compliance ledger that stores the PII it
        found is the failure it exists to prevent.
        """
        entry: dict[str, Any] = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "session_id": session_id or "-",
            "module": module,
            "event_type": event_type,
            "iso_42001_clause": self.CLAUSES.get(module, self.CLAUSES["core"]),
            "payload": payload,
        }
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with _LOCAL_LOCK:
            with self.path.open("a+b") as fh:
                _lock(fh)
                try:
                    prev = _last_hash(fh)
                    entry["hash"] = _sha256(_chained_payload(entry), prev)
                    entry["previous_hash"] = prev
                    fh.seek(0, os.SEEK_END)
                    fh.write((json.dumps(entry, ensure_ascii=False) + "\n").encode("utf-8"))
                    fh.flush()
                    os.fsync(fh.fileno())
                finally:
                    _unlock(fh)
        return entry

    # ── read ─────────────────────────────────────────────────────────────────
    def entries(self) -> Iterator[dict[str, Any]]:
        if not self.path.exists():
            return iter(())

        def _gen() -> Iterator[dict[str, Any]]:
            with self.path.open("r", encoding="utf-8") as fh:
                _lock(fh, exclusive=False)
                try:
                    for raw in fh:
                        if raw.strip():
                            yield json.loads(raw)
                finally:
                    _unlock(fh)

        return _gen()

    def verify_chain(self, *, raise_on_violation: bool = False,
                     locale: str = "en") -> tuple[bool, list[str]]:
        """Recompute every digest. Returns `(intact, violations)`.

        A malformed line is a violation, not an exception: a ledger that cannot
        be parsed is exactly the state this check exists to report.
        """
        violations: list[str] = []
        prev = GENESIS
        if not self.path.exists():
            return True, []
        with self.path.open("r", encoding="utf-8") as fh:
            _lock(fh, exclusive=False)
            try:
                for lineno, raw in enumerate(fh, start=1):
                    if not raw.strip():
                        continue
                    try:
                        entry = json.loads(raw)
                    except json.JSONDecodeError as exc:
                        violations.append(
                            i18n.ui("chain.unparseable", locale, line=lineno, detail=exc.msg))
                        prev = "<unparseable>"
                        continue
                    stored_hash = entry.get("hash", "")
                    stored_prev = entry.get("previous_hash", "")
                    if stored_prev != prev:
                        violations.append(i18n.ui(
                            "chain.mismatch", locale, line=lineno,
                            expected=prev[:12], got=(stored_prev or "∅")[:12]))
                    recomputed = _sha256(_chained_payload(entry), stored_prev)
                    if recomputed != stored_hash:
                        violations.append(i18n.ui(
                            "chain.altered", locale, line=lineno,
                            stored=(stored_hash or "∅")[:12], recomputed=recomputed[:12]))
                    prev = stored_hash
            finally:
                _unlock(fh)
        intact = not violations
        if not intact and raise_on_violation:
            raise LedgerViolation(f"{len(violations)} chain violation(s): {violations[0]}")
        return intact, violations


_DEFAULT: AuditTrail | None = None


def default_trail() -> AuditTrail:
    """Process-wide trail at the configured path. Cheap; safe to call per event."""
    global _DEFAULT
    if _DEFAULT is None:
        _DEFAULT = AuditTrail()
    return _DEFAULT


def set_default_trail(trail: AuditTrail) -> None:
    global _DEFAULT
    _DEFAULT = trail


def new_session_id() -> str:
    return uuid.uuid4().hex[:16]
