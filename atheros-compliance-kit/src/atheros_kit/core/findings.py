"""One finding vocabulary, shared by all four modules.

Why this is in `core` and not repeated per module: the CI gate, the Markdown
report, the JSON export and the Console all render findings. If each module had
its own shape, each of those four consumers would need four renderers, and the
severity of a bias finding and a residency finding would drift apart. A finding
is the unit of evidence this product sells; it gets one definition.
"""
from __future__ import annotations

from collections.abc import Iterable
from dataclasses import asdict, dataclass, field
from enum import Enum
from typing import Any

from . import i18n


class Severity(str, Enum):
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    INFO = "info"

    @property
    def rank(self) -> int:
        return {"critical": 4, "high": 3, "medium": 2, "low": 1, "info": 0}[self.value]


class Action(str, Enum):
    """What the system did (or must do) about a finding.

    PASS/FLAG/BLOCK is the guardrail gate's contract, and the distinction is the
    point: BLOCK is "this must not reach the model or the user", FLAG is "a human
    decides". Collapsing them turns a safety control into either a nuisance or a
    rubber stamp.
    """

    PASS = "pass"
    FLAG = "flag"
    BLOCK = "block"


class Method(str, Enum):
    """How a score was actually produced.

    Rendered on every score. `DETERMINISTIC` where an LLM was configured means
    the run degraded, and the report says so rather than presenting a fallback
    number as if it were the primary one.
    """

    DETERMINISTIC = "deterministic"
    LLM = "llm"
    HYBRID = "hybrid"


class Coverage(str, Enum):
    COVERED = "covered"
    PARTIAL = "partial"
    MISSING = "missing"
    NOT_APPLICABLE = "not_applicable"


@dataclass
class Finding:
    """One assessed fact.

    `evidence` points at what the number was computed from — a chunk id, a
    criterion key, a session id. A finding without evidence is an opinion, and
    this product does not sell opinions.
    """

    check: str
    severity: Severity
    detail: str
    module: str
    action: Action = Action.FLAG
    article: str | None = None          # e.g. "Art. 10" / "Annex III" / "ISO 42001 §8.4"
    evidence: dict[str, Any] = field(default_factory=dict)
    remediation: str | None = None
    #: Values the localised template needs. `detail` above is the English
    #: rendering the module already wrote; these are the same values unformatted,
    #: so another language can be produced without re-deriving anything. A finding
    #: with no params still renders — in English — rather than failing.
    params: dict[str, Any] = field(default_factory=dict)

    def detail_in(self, locale: str = "en") -> str:
        return i18n.finding_text(self.check, "detail", locale, self.detail, self.params)

    def remediation_in(self, locale: str = "en") -> str | None:
        if self.remediation is None:
            return None
        return i18n.finding_text(self.check, "remediation", locale, self.remediation, self.params)

    def to_dict(self, locale: str = "en") -> dict[str, Any]:
        """Serialise, with EVERY language present.

        `detail` is rendered in the requested locale, and `detail_tr` carries the
        Turkish alongside it. Emitting both is what lets a static export toggle
        language without refetching — and, more importantly, it means an archived
        evidence pack is readable by a reviewer whose language was not chosen at
        the moment the report was generated.
        """
        d = asdict(self)
        d["severity"] = self.severity.value
        d["action"] = self.action.value
        d["detail"] = self.detail_in(locale)
        d["remediation"] = self.remediation_in(locale)
        d["detail_tr"] = self.detail_in("tr")
        d["remediation_tr"] = self.remediation_in("tr")
        return d

    def __str__(self) -> str:
        art = f" [{self.article}]" if self.article else ""
        return f"{self.severity.value.upper():8} {self.check}{art}: {self.detail}"


@dataclass
class Score:
    """A 0–100 score that knows how it was made and whether it is real.

    `value is None` means unmeasured. Unmeasured renders grey, never green — a
    tool that shows an absent measurement as a passing one is a broken
    instrument, and this is the single most common way governance dashboards
    lie.
    """

    name: str
    value: float | None
    method: Method = Method.DETERMINISTIC
    degraded: bool = False
    threshold: float | None = None
    basis: dict[str, Any] = field(default_factory=dict)

    @property
    def band(self) -> str:
        if self.value is None:
            return "unmeasured"
        if self.value >= 85:
            return "good"
        if self.value >= 70:
            return "watch"
        if self.value >= 50:
            return "poor"
        return "critical"

    @property
    def passed(self) -> bool | None:
        """None when unmeasured — deliberately not False.

        `if not score.passed` would treat an unmeasured score as a failure and
        `if score.passed` would treat it as a pass; both are wrong, so callers
        are forced to say which they mean.
        """
        if self.value is None or self.threshold is None:
            return None
        return self.value >= self.threshold

    def to_dict(self) -> dict[str, Any]:
        d = asdict(self)
        d["method"] = self.method.value
        d["band"] = self.band
        d["passed"] = self.passed
        return d


def worst(findings: Iterable[Finding]) -> Severity | None:
    """Highest severity present, or None for an empty set."""
    items = list(findings)
    return max((f.severity for f in items), key=lambda s: s.rank) if items else None


def harmonic_mean(values: Iterable[float]) -> float:
    """Used for every composite score in the Kit.

    Harmonic, not arithmetic, on purpose: one bad dimension must not be averaged
    away by four good ones. A corpus that is fine on geography and catastrophic
    on gender is not "mostly fair".
    """
    vals = [v for v in values if v is not None]
    if not vals:
        return 0.0
    # A zero must propagate, not be dropped. The harmonic mean of a set containing
    # zero IS zero, and that is precisely the behaviour this function was chosen
    # for: a dimension scoring 0 is the one that must dominate the composite.
    # Filtering non-positives out — the obvious way to avoid the division — makes
    # the worst possible input the only one with no effect on the result.
    if any(v <= 0 for v in vals):
        return 0.0
    return round(len(vals) / sum(1.0 / v for v in vals), 2)


def score_from_ratio(ratio: float, threshold: float = 0.8) -> float:
    """Ratio metric (0–1, ideal 1.0) → 0–100. Threshold 0.8 = the four-fifths rule."""
    if ratio >= 1.0:
        return 100.0
    if threshold <= 0:
        return 0.0
    return round(min(100.0, (ratio / threshold) * 100), 1)


def score_from_diff(diff: float, threshold: float = 0.1) -> float:
    """Difference metric (ideal 0.0) → 0–100. Zero at twice the threshold."""
    if diff <= 0:
        return 100.0
    if diff >= threshold * 2:
        return 0.0
    return round((1 - diff / (threshold * 2)) * 100, 1)
