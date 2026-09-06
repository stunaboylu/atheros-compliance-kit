"""EU AI Act risk classification.

The decision order is the statute's own and is not negotiable: Art. 5 prohibition
first (a prohibited practice is not "high risk", it is not allowed), then
Annex I product safety and Annex III use cases for high risk, then Art. 50
transparency, then minimal. Running these in any other order produces answers
that are wrong in the direction that gets a customer fined.

Two honesty rules are enforced in code rather than left to the caller:

1. **"No indicator matched" is never rendered as "low risk".** A minimal verdict
   carries `evidence_basis="no_indicator_matched"` and a limit note. The lexicon
   is structural; it does not know what it has not been taught.
2. **Ambiguity produces a grey zone, not a confident tier.** Multiple Annex III
   categories, a sector/use-case conflict, or GPAI-plus-high-risk lowers
   confidence and names the conflict. A false confident tier is worse than an
   honest "this needs a human", because nobody re-examines it.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from ..core import i18n
from ..core.findings import Action, Finding, Severity
from . import vocabulary as V


class RiskTier(str):
    """Str-subclass so a tier compares equal to its wire value everywhere."""

    UNACCEPTABLE = "unacceptable"
    HIGH = "high"
    LIMITED = "limited"
    MINIMAL = "minimal"
    UNKNOWN = "unknown"


@dataclass
class SystemSpec:
    """What the engine needs to know. Everything optional except a name.

    Deliberately not a questionnaire: these are facts an engineer already has in
    the repository or the deployment description. If answering required a legal
    workshop, the tool would not be used.
    """

    name: str
    sector: str = ""
    use_cases: list[str] = field(default_factory=list)
    description: str = ""
    deployment_context: str = ""              # e.g. "internal tool", "public-facing eu"
    autonomy: str = "assistive"               # assistive | human_in_the_loop | autonomous
    human_oversight: str = "unknown"          # none | review | approval | unknown
    affected_persons: list[str] = field(default_factory=list)
    is_gpai: bool = False
    gpai_systemic_risk: bool = False
    generates_content: bool = False
    processes_biometrics: bool = False
    infers_emotions: bool = False
    safety_component: bool = False            # component of a product in Annex I
    eu_market: bool = True

    @property
    def subject(self) -> str:
        """The text the lexicons match against."""
        return " ".join(
            [self.name, self.sector, self.description, self.deployment_context]
            + list(self.use_cases) + list(self.affected_persons)
        )

    @classmethod
    def from_dict(cls, d: dict[str, Any]) -> "SystemSpec":
        known = {f for f in cls.__dataclass_fields__}
        return cls(**{k: v for k, v in d.items() if k in known})


@dataclass
class RiskClassification:
    tier: str
    confidence: float
    reasoning: list[str]
    articles: list[str]
    annex_categories: list[str]
    grey_zone: bool
    grey_zone_reason: str | None
    obligations: list[dict[str, str]]
    regulation_version: str
    evidence_basis: str
    gpai_obligations: list[dict[str, str]] = field(default_factory=list)
    limits: list[str] = field(default_factory=list)
    system: str = ""
    #: The same reasoning, built at the same moment from the same values. Not a
    #: translation of the finished English — a post-hoc translation of legal
    #: reasoning is where meaning goes, and this is the sentence a person signs.
    reasoning_tr: list[str] = field(default_factory=list)
    grey_zone_reason_tr: str | None = None
    limits_tr: list[str] = field(default_factory=list)

    def reasoning_in(self, locale: str = "en") -> list[str]:
        return self.reasoning_tr if locale == "tr" and self.reasoning_tr else self.reasoning

    def limits_in(self, locale: str = "en") -> list[str]:
        return self.limits_tr if locale == "tr" and self.limits_tr else self.limits

    def grey_zone_reason_in(self, locale: str = "en") -> str | None:
        if locale == "tr" and self.grey_zone_reason_tr:
            return self.grey_zone_reason_tr
        return self.grey_zone_reason

    def to_dict(self) -> dict[str, Any]:
        return {
            "system": self.system,
            "tier": self.tier,
            "confidence": self.confidence,
            "grey_zone": self.grey_zone,
            "grey_zone_reason": self.grey_zone_reason,
            "articles": self.articles,
            "annex_categories": self.annex_categories,
            "reasoning": self.reasoning,
            "reasoning_tr": self.reasoning_tr,
            "grey_zone_reason_tr": self.grey_zone_reason_tr,
            "limits_tr": self.limits_tr,
            "obligations": self.obligations,
            "gpai_obligations": self.gpai_obligations,
            "regulation_version": self.regulation_version,
            "evidence_basis": self.evidence_basis,
            "limits": self.limits,
        }

    def to_findings(self) -> list[Finding]:
        sev = {
            RiskTier.UNACCEPTABLE: Severity.CRITICAL,
            RiskTier.HIGH: Severity.HIGH,
            RiskTier.LIMITED: Severity.MEDIUM,
            RiskTier.MINIMAL: Severity.INFO,
            RiskTier.UNKNOWN: Severity.MEDIUM,
        }[self.tier]
        out = [Finding(
            check="eu_ai_act_tier",
            severity=sev,
            detail=f"classified {self.tier} (confidence {self.confidence:.2f}) — {self.reasoning[0] if self.reasoning else 'no reasoning recorded'}",
            module="euact",
            action=Action.BLOCK if self.tier == RiskTier.UNACCEPTABLE else Action.FLAG,
            article=self.articles[0] if self.articles else None,
            evidence={"annex_categories": self.annex_categories,
                      "regulation_version": self.regulation_version,
                      "evidence_basis": self.evidence_basis},
            remediation=self.obligations[0]["duty"] if self.obligations else None,
            params={"tier": self.tier, "confidence": f"{self.confidence:.2f}",
                    "reason": self.reasoning[0] if self.reasoning else "no reasoning recorded",
                    "reason_tr": (self.reasoning_tr[0] if self.reasoning_tr
                                  else "gerekçe kaydedilmedi")},
        )]
        if self.grey_zone:
            out.append(Finding(
                check="classification_grey_zone",
                severity=Severity.MEDIUM,
                detail=self.grey_zone_reason or "the inputs support more than one classification",
                module="euact",
                action=Action.FLAG,
                article="Art. 6",
                remediation="Route to a human reviewer. Do not act on the tier alone.",
                params={"reason": self.grey_zone_reason
                        or "the inputs support more than one classification",
                        "reason_tr": self.grey_zone_reason_tr
                        or "girdiler birden fazla sınıflandırmayı destekliyor"},
            ))
        return out


def _oversight_penalty(spec: SystemSpec) -> tuple[float, tuple[str, str] | None]:
    """Autonomy and oversight do not change the tier — they change the confidence.

    Art. 14 is an obligation attached to high-risk systems, not an input to
    whether a system is high-risk. Treating weak oversight as evidence OF high
    risk is a common and wrong shortcut: it makes well-governed high-risk systems
    look lower-risk, which is exactly backwards.
    """
    if spec.autonomy == "autonomous" and spec.human_oversight in ("none", "unknown"):
        return -0.05, i18n.both("oversight")
    return 0.0, None


def classify(spec: SystemSpec | dict[str, Any]) -> RiskClassification:
    if isinstance(spec, dict):
        spec = SystemSpec.from_dict(spec)
    subject = spec.subject
    reasoning: list[str] = []
    reasoning_tr: list[str] = []
    limits: list[str] = []
    limits_tr: list[str] = []
    articles: list[str] = []

    def reason(key: str, **params) -> None:
        en, tr = i18n.both(key, **params)
        reasoning.append(en)
        reasoning_tr.append(tr)

    def limit(key: str, **params) -> None:
        en, tr = i18n.both(key, **params)
        limits.append(en)
        limits_tr.append(tr)

    gpai = list(V.GPAI_OBLIGATIONS) if spec.is_gpai else []
    if spec.is_gpai and not spec.gpai_systemic_risk:
        gpai = [o for o in gpai if o["article"] != "Art. 55"]

    if not spec.eu_market:
        limit("limit.no_eu_market")

    # ── 1. Article 5 — prohibited ────────────────────────────────────────────
    banned = V.find_indicators(subject, V.UNACCEPTABLE_INDICATORS)
    # Two practices are prohibited only in a specific CONTEXT, and matching the
    # phrase alone over-triggers: emotion recognition is prohibited at work and in
    # education (Art. 5(1)(f)) and merely transparency-bound elsewhere.
    if "emotion_workplace_education" in banned and not any(
        s in (spec.sector or "").lower() for s in ("employment", "hr", "education", "recruitment")
    ):
        banned.pop("emotion_workplace_education")
    if banned:
        first = next(iter(banned))
        reason("prohibited", category=first, hits=", ".join(banned[first]))
        limit("limit.prohibited")
        return RiskClassification(
            tier=RiskTier.UNACCEPTABLE, confidence=0.95,
            reasoning=reasoning, reasoning_tr=reasoning_tr,
            articles=["Art. 5"], annex_categories=[], grey_zone=False, grey_zone_reason=None,
            obligations=V.OBLIGATIONS["unacceptable"], regulation_version=V.REGULATION_VERSION,
            evidence_basis="indicator_matched", gpai_obligations=gpai,
            limits=limits, limits_tr=limits_tr,
            system=spec.name,
        )

    # ── 2. High risk — Annex I (product safety) and Annex III (use case) ─────
    annex_iii = V.find_indicators(subject, V.ANNEX_III_CATEGORIES)
    annex_i = V.find_indicators(subject, V.ANNEX_I_PRODUCTS)
    sector_hit = (spec.sector or "").lower().replace("-", "_") in V.HIGH_RISK_SECTORS

    grey_zone, grey_reason, grey_reason_tr = False, None, None
    if annex_i or (spec.safety_component and annex_i):
        reason("annex_i", matches=", ".join(annex_i))
        articles += ["Art. 6(1)", "Annex I"]
    for category, hits in annex_iii.items():
        reason("annex_iii", category=category, hits=", ".join(hits))
        articles.append("Annex III")

    if annex_iii or annex_i:
        if sector_hit:
            reason("sector", sector=spec.sector)
            articles.append("Art. 6(2)")
        confidence = 0.85
        if len(annex_iii) >= 2:
            grey_zone = True
            grey_reason, grey_reason_tr = i18n.both(
                "grey.multi_annex", n=len(annex_iii), cats=", ".join(annex_iii))
            confidence = 0.65
        if annex_i and annex_iii:
            grey_zone = True
            grey_reason, grey_reason_tr = i18n.both("grey.annex_i_and_iii")
            confidence = 0.6
        delta, note_pair = _oversight_penalty(spec)
        if note_pair:
            confidence += delta
            reasoning.append(note_pair[0])
            reasoning_tr.append(note_pair[1])
        if spec.is_gpai:
            grey_zone = True
            gpai_en, gpai_tr = i18n.both("grey.gpai")
            grey_reason = (grey_reason or "") + gpai_en
            grey_reason_tr = (grey_reason_tr or "") + gpai_tr
        return RiskClassification(
            tier=RiskTier.HIGH, confidence=round(confidence, 2),
            reasoning=reasoning, reasoning_tr=reasoning_tr,
            articles=sorted(set(articles)) or ["Art. 6", "Annex III"],
            annex_categories=sorted(annex_iii) + sorted(annex_i),
            grey_zone=grey_zone, grey_zone_reason=grey_reason,
            grey_zone_reason_tr=grey_reason_tr,
            obligations=V.OBLIGATIONS["high"], regulation_version=V.REGULATION_VERSION,
            evidence_basis="indicator_matched", gpai_obligations=gpai,
            limits=limits, limits_tr=limits_tr,
            system=spec.name,
        )

    # A high-risk SECTOR with no matching use case is the definition of a grey
    # zone: the prior is raised and the evidence is absent. Reporting "minimal"
    # here is how a healthcare triage tool described in two vague sentences ends
    # up unclassified.
    if sector_hit:
        limited = V.find_indicators(subject, V.LIMITED_RISK_INDICATORS)
        reason("sector_only", sector=spec.sector)
        limit("limit.provide_use_cases")
        gz_en, gz_tr = i18n.both("grey.sector_only", sector=spec.sector)
        return RiskClassification(
            tier=RiskTier.LIMITED if limited else RiskTier.UNKNOWN,
            confidence=0.45,
            reasoning=reasoning, reasoning_tr=reasoning_tr,
            articles=["Art. 6(2)"] + (["Art. 50"] if limited else []),
            annex_categories=[], grey_zone=True,
            grey_zone_reason=gz_en, grey_zone_reason_tr=gz_tr,
            obligations=V.OBLIGATIONS["limited"] if limited else [],
            regulation_version=V.REGULATION_VERSION,
            evidence_basis="sector_only", gpai_obligations=gpai,
            limits=limits, limits_tr=limits_tr,
            system=spec.name,
        )

    # ── 3. Article 50 — transparency ─────────────────────────────────────────
    limited = V.find_indicators(subject, V.LIMITED_RISK_INDICATORS)
    if spec.generates_content:
        limited.setdefault("synthetic_content", ["declared: generates content"])
    if spec.infers_emotions:
        limited.setdefault("emotion_recognition", ["declared: infers emotions"])
    if spec.processes_biometrics:
        limited.setdefault("biometric_categorisation", ["declared: processes biometrics"])
    if limited:
        duties = [o for o in V.OBLIGATIONS["limited"]
                  if _duty_applies(o["article"], limited)]
        reason("transparency", matches=", ".join(limited))
        return RiskClassification(
            tier=RiskTier.LIMITED, confidence=0.8,
            reasoning=reasoning, reasoning_tr=reasoning_tr,
            articles=["Art. 50"], annex_categories=[], grey_zone=False, grey_zone_reason=None,
            obligations=duties or V.OBLIGATIONS["limited"],
            regulation_version=V.REGULATION_VERSION, evidence_basis="indicator_matched",
            gpai_obligations=gpai, limits=limits, limits_tr=limits_tr, system=spec.name,
        )

    # ── 4. Minimal — and say plainly what that verdict rests on ──────────────
    reason("minimal")
    limit("limit.minimal")
    return RiskClassification(
        tier=RiskTier.MINIMAL, confidence=0.6,
        reasoning=reasoning, reasoning_tr=reasoning_tr,
        articles=["Art. 6(3)"], annex_categories=[], grey_zone=False, grey_zone_reason=None,
        obligations=V.OBLIGATIONS["minimal"], regulation_version=V.REGULATION_VERSION,
        evidence_basis="no_indicator_matched", gpai_obligations=gpai,
        limits=limits, limits_tr=limits_tr,
        system=spec.name,
    )


def _duty_applies(article: str, matched: dict[str, list[str]]) -> bool:
    mapping = {
        "Art. 50(1)": {"human_interaction"},
        "Art. 50(2)": {"synthetic_content"},
        "Art. 50(3)": {"emotion_recognition", "biometric_categorisation"},
        "Art. 50(4)": {"deepfake"},
    }
    return bool(mapping.get(article, set()) & set(matched))
