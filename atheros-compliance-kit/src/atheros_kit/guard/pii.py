"""PII and custom-entity anonymization for outbound prompts.

Design decisions worth stating, because each has a cheaper wrong version:

**Stable placeholders, not blanket redaction.** `ali@example.com` becomes
`⟦EMAIL_1⟧` and stays `⟦EMAIL_1⟧` for the whole session. Replacing every email
with `[EMAIL]` destroys the model's ability to tell two people apart, which
silently degrades every summarisation and extraction task the customer bought
the model for. Stable placeholders keep the reasoning and remove the identity.

**The vault is in-memory and never serialised.** Restoring the real values on
the way back is a convenience the operator opts into (`reversible=True`, the
default). `reversible=False` drops the mapping and the values are unrecoverable
by construction — which is what a maximum-isolation deployment needs.

**Detection is structural.** An email address and an IBAN have a shape; a
person's name does not. So a clean scan means "nothing recognisable was found",
never "no personal data present", and no caller may turn the first into the
second. `MaskResult.structural_only` exists to make that explicit at the type
level rather than in a comment nobody reads.
"""
from __future__ import annotations

import re
from collections.abc import Iterable
from dataclasses import dataclass, field
from re import Pattern

# ── Built-in detectors ────────────────────────────────────────────────────────
# Ordered: longer/more specific shapes first, so an AWS key is not shredded by
# the generic api_key rule and a JWT is not eaten by base64 lookalikes.
_BUILTIN: list[tuple[str, Pattern[str]]] = [
    ("JWT", re.compile(r"\beyJ[A-Za-z0-9_-]{8,}\.[A-Za-z0-9_-]{8,}\.[A-Za-z0-9_-]{8,}\b")),
    ("AWS_KEY", re.compile(r"\b(?:AKIA|ASIA)[0-9A-Z]{16}\b")),
    ("API_KEY", re.compile(r"\b(?:sk|pk|rk)-[A-Za-z0-9_-]{16,}\b")),
    # 11-30 body chars, spaces optional anywhere: an IBAN is 15-34 characters and its
    # length is not a multiple of four, so a strict four-group pattern misses every
    # country whose format ends in a partial group (NL, DE, TR among them).
    ("IBAN", re.compile(r"\b[A-Z]{2}\d{2}(?:[ ]?[A-Z0-9]){11,30}\b")),
    ("CREDIT_CARD", re.compile(r"\b(?:\d[ -]?){13,19}\b")),
    ("EMAIL", re.compile(r"\b[\w.+-]+@[\w-]+\.[\w.-]{2,}\b")),
    ("IPV6", re.compile(r"\b(?:[A-Fa-f0-9]{1,4}:){2,7}[A-Fa-f0-9]{1,4}\b")),
    ("IPV4", re.compile(r"\b(?:(?:25[0-5]|2[0-4]\d|1?\d?\d)\.){3}(?:25[0-5]|2[0-4]\d|1?\d?\d)\b")),
    # National IDs precede PHONE deliberately: the phone pattern will happily consume
    # a bare 9- or 11-digit run, and a TCKN masked as a phone number is a masked
    # value with the wrong category on the compliance record.
    ("TCKN", re.compile(r"(?<!\d)[1-9]\d{10}(?!\d)")),          # TR national ID
    ("BSN", re.compile(r"(?<!\d)\d{9}(?!\d)")),                 # NL citizen number
    ("PHONE", re.compile(r"(?<![\w.])\+?\d{1,3}[ .-]?\(?\d{2,4}\)?[ .-]?\d{3}[ .-]?\d{2,4}(?![\w.])")),
]

#: Categories that are almost always a genuine secret rather than candidate data.
#: A finding on one of these is CRITICAL; on the rest it is a masking record.
SECRET_CATEGORIES = frozenset({"JWT", "AWS_KEY", "API_KEY"})

_PLACEHOLDER_RE = re.compile(r"⟦([A-Z0-9_]+)_(\d+)⟧")


def _luhn_ok(digits: str) -> bool:
    """Cheap validity filter for CREDIT_CARD.

    Without it, any 13–19 digit run — an order id, a timestamp concatenation —
    is reported as a card number, and a masking report that cries wolf is one
    people switch off.
    """
    nums = [int(c) for c in digits if c.isdigit()]
    if not 13 <= len(nums) <= 19:
        return False
    total, parity = 0, len(nums) % 2
    for i, n in enumerate(nums):
        if i % 2 == parity:
            n *= 2
            if n > 9:
                n -= 9
        total += n
    return total % 10 == 0


def _iban_ok(candidate: str) -> bool:
    """ISO 13616 mod-97 check. Same reasoning as Luhn: precision over recall here."""
    s = candidate.replace(" ", "").upper()
    if not 15 <= len(s) <= 34:
        return False
    rearranged = s[4:] + s[:4]
    try:
        numeric = "".join(str(int(c, 36)) for c in rearranged)
    except ValueError:
        return False
    return int(numeric) % 97 == 1


def _tckn_ok(candidate: str) -> bool:
    """TR national-ID checksum. Both digits, not just the last one.

    Any 11-digit run passes the shape; only ~1 in 100 passes this. Without it
    every invoice number in a prompt is logged as a national identity number,
    which inflates the very metric a DPO uses to judge exposure.
    """
    d = [int(c) for c in candidate]
    if len(d) != 11 or d[0] == 0:
        return False
    odd = d[0] + d[2] + d[4] + d[6] + d[8]
    even = d[1] + d[3] + d[5] + d[7]
    return (odd * 7 - even) % 10 == d[9] and sum(d[:10]) % 10 == d[10]


def _bsn_ok(candidate: str) -> bool:
    """NL BSN 'elfproef': weights 9..2 then -1 on the check digit, sum % 11 == 0."""
    d = [int(c) for c in candidate]
    if len(d) != 9:
        return False
    total = sum(n * w for n, w in zip(d, (9, 8, 7, 6, 5, 4, 3, 2))) - d[8]
    return total % 11 == 0


_VALIDATORS = {"CREDIT_CARD": _luhn_ok, "IBAN": _iban_ok, "TCKN": _tckn_ok, "BSN": _bsn_ok}


@dataclass
class CustomEntity:
    """An enterprise-specific thing that must never leave the building.

    Internal project codenames, unreleased product names, revenue figures — none
    of which any general PII detector knows about, and all of which are exactly
    what a competitor would want from an intercepted prompt.
    """

    name: str                      # placeholder category, e.g. "CODENAME"
    pattern: str | None = None     # regex, OR
    literals: list[str] = field(default_factory=list)   # exact strings (case-insensitive)
    ignore_case: bool = True

    def compiled(self) -> Pattern[str]:
        if self.pattern:
            return re.compile(self.pattern, re.IGNORECASE if self.ignore_case else 0)
        if not self.literals:
            raise ValueError(f"CustomEntity {self.name!r} defines neither pattern nor literals")
        # Longest-first so "Project Northwind" wins over "Northwind".
        alts = "|".join(re.escape(s) for s in sorted(self.literals, key=len, reverse=True))
        return re.compile(rf"\b(?:{alts})\b", re.IGNORECASE if self.ignore_case else 0)


@dataclass
class MaskResult:
    text: str
    #: category → count. Values are deliberately absent: this object is what gets
    #: logged, and the ledger must never hold what it detected.
    entities: dict[str, int] = field(default_factory=dict)
    #: placeholder → original. Empty when reversible=False.
    vault: dict[str, str] = field(default_factory=dict, repr=False)
    structural_only: bool = True

    @property
    def masked_any(self) -> bool:
        return bool(self.entities)

    @property
    def secrets_found(self) -> list[str]:
        return sorted(c for c in self.entities if c in SECRET_CATEGORIES)

    def log_payload(self) -> dict:
        """Ledger-safe summary: classes and counts, never values."""
        return {
            "entities": dict(sorted(self.entities.items())),
            "total_masked": sum(self.entities.values()),
            "secrets": self.secrets_found,
            "structural_only": self.structural_only,
        }


class Anonymizer:
    """Session-scoped masker. One per conversation, so placeholders stay stable.

    Reuse across unrelated conversations would let a placeholder from one leak
    meaning into another, so the vault is scoped, not global.
    """

    def __init__(
        self,
        *,
        custom_entities: Iterable[CustomEntity] = (),
        categories: Iterable[str] | None = None,
        reversible: bool = True,
    ):
        self.reversible = reversible
        self._counter: dict[str, int] = {}
        self._seen: dict[tuple[str, str], str] = {}   # (category, value) → placeholder
        self._vault: dict[str, str] = {}
        wanted = set(categories) if categories else None
        self._detectors: list[tuple[str, Pattern[str]]] = [
            (name, rx) for name, rx in _BUILTIN if wanted is None or name in wanted
        ]
        # Custom entities run FIRST: an internal codename that happens to look
        # like an id must be masked as CODENAME, not swallowed by a generic rule.
        self._detectors = [(e.name, e.compiled()) for e in custom_entities] + self._detectors

    def _placeholder(self, category: str, value: str) -> str:
        key = (category, value)
        if key in self._seen:
            return self._seen[key]
        self._counter[category] = self._counter.get(category, 0) + 1
        ph = f"⟦{category}_{self._counter[category]}⟧"
        self._seen[key] = ph
        if self.reversible:
            self._vault[ph] = value
        return ph

    def mask(self, text: str) -> MaskResult:
        if not text:
            return MaskResult(text=text or "")
        counts: dict[str, int] = {}
        out = text
        for category, rx in self._detectors:
            validator = _VALIDATORS.get(category)

            def repl(m: re.Match, _c=category, _v=validator) -> str:
                raw = m.group(0)
                if _v is not None and not _v(raw):
                    return raw          # failed its checksum — not that entity
                counts[_c] = counts.get(_c, 0) + 1
                return self._placeholder(_c, raw)

            out = rx.sub(repl, out)
        return MaskResult(
            text=out,
            entities=counts,
            vault=dict(self._vault) if self.reversible else {},
            structural_only=True,
        )

    def unmask(self, text: str) -> str:
        """Restore originals in a model response.

        Only placeholders this session actually issued are restored. A model that
        invents `⟦EMAIL_7⟧` — or echoes one from a different session — gets left
        as-is rather than resolved against whatever happens to sit at that index.
        """
        if not self.reversible or not self._vault or not text:
            return text
        return _PLACEHOLDER_RE.sub(lambda m: self._vault.get(m.group(0), m.group(0)), text)

    def leaked_placeholders(self, text: str) -> list[str]:
        """Placeholders present in text that this session never issued.

        A non-empty result on a model response means the model is fabricating
        identifiers in our placeholder namespace — worth flagging, because
        downstream unmasking would otherwise be asked to resolve a hallucination.
        """
        return sorted({m.group(0) for m in _PLACEHOLDER_RE.finditer(text)} - set(self._vault))


def detect_categories(text: str) -> list[str]:
    """Which personal-data categories are visible, by name. No masking, no state.

    Exposed so other modules (the RAG corpus scanner, the evidence gate) reuse
    these detectors instead of growing a second, drifting copy.
    """
    found = []
    for name, rx in _BUILTIN:
        validator = _VALIDATORS.get(name)
        for m in rx.finditer(text or ""):
            if validator is None or validator(m.group(0)):
                found.append(name)
                break
    return sorted(set(found))
