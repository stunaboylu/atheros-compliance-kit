"""The audit chain is the product's tamper-evidence claim. These tests are the
claim's only proof, so they check the two failure modes that made the chain
useless in the predecessor system: a per-process chain head, and a writer that
hashes a different field set than the verifier."""
import json

import pytest

from atheros_kit.core.audit import GENESIS, AuditTrail
from atheros_kit.core.errors import LedgerViolation


def test_empty_trail_verifies(tmp_path):
    assert AuditTrail(tmp_path / "a.jsonl").verify_chain() == (True, [])


def test_chain_links_and_verifies(isolated_trail):
    first = isolated_trail.log("guard", "e1", {"n": 1})
    second = isolated_trail.log("guard", "e2", {"n": 2})
    assert first["previous_hash"] == GENESIS
    assert second["previous_hash"] == first["hash"]
    assert isolated_trail.verify_chain() == (True, [])


def test_tampered_payload_is_detected(isolated_trail):
    isolated_trail.log("rag", "audit", {"score": 42})
    isolated_trail.log("rag", "audit", {"score": 43})
    lines = isolated_trail.path.read_text().strip().splitlines()
    entry = json.loads(lines[0])
    entry["payload"]["score"] = 99
    lines[0] = json.dumps(entry)
    isolated_trail.path.write_text("\n".join(lines) + "\n")

    intact, violations = isolated_trail.verify_chain()
    assert not intact
    assert any("content altered" in v for v in violations)


def test_deleted_entry_is_detected(isolated_trail):
    for i in range(3):
        isolated_trail.log("core", "e", {"i": i})
    lines = isolated_trail.path.read_text().strip().splitlines()
    isolated_trail.path.write_text("\n".join([lines[0], lines[2]]) + "\n")

    intact, violations = isolated_trail.verify_chain()
    assert not intact
    assert any("previous_hash mismatch" in v for v in violations)


def test_chain_head_comes_from_disk_not_memory(tmp_path):
    """Two AuditTrail objects on one file must continue ONE chain.

    This is the multi-worker case: a module-global head restarts the chain in the
    middle of an existing one, and every worker then writes its own fork.
    """
    path = tmp_path / "shared.jsonl"
    a, b = AuditTrail(path), AuditTrail(path)
    first = a.log("guard", "from_a", {})
    second = b.log("guard", "from_b", {})
    assert second["previous_hash"] == first["hash"]
    assert AuditTrail(path).verify_chain() == (True, [])


def test_unparseable_line_is_a_violation_not_an_exception(isolated_trail):
    isolated_trail.log("core", "e", {})
    isolated_trail.path.write_text(isolated_trail.path.read_text() + "{not json\n")
    intact, violations = isolated_trail.verify_chain()
    assert not intact and any("unparseable" in v for v in violations)


def test_raise_on_violation_is_opt_in(isolated_trail):
    isolated_trail.log("core", "e", {})
    isolated_trail.path.write_text(isolated_trail.path.read_text().replace('"e"', '"tampered"'))
    isolated_trail.verify_chain()                       # must not raise
    with pytest.raises(LedgerViolation):
        isolated_trail.verify_chain(raise_on_violation=True)
