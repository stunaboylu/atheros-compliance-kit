"""`assess()` — the whole of Module 4 in one call."""
from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass, field
from typing import Any

from ..core import i18n, license
from ..core.audit import AuditTrail, default_trail, new_session_id
from ..core.findings import Action, Coverage, Finding, Method, Score, Severity
from ..core.report import Report
from .criteria import CRITERIA, GROUPS, STATUS_WEIGHT, group_weights
from .optout import OptOutResult, enforce
from .registry import STALENESS_DAYS, ProviderEntry, lookup
from .residency import ResidencyResult, verify


@dataclass
class VendorAssessment:
    provider: str
    entry: ProviderEntry
    score: Score
    group_scores: dict[str, float]
    statuses: dict[str, str]
    residency: ResidencyResult
    optout: OptOutResult
    report: Report
    unknown_criteria: list[str] = field(default_factory=list)

    @property
    def unknown_ratio(self) -> float:
        return round(len(self.unknown_criteria) / len(CRITERIA), 3)

    def to_dict(self, locale: str = "en") -> dict[str, Any]:
        return {
            **self.report.to_dict(locale=locale),
            "provider": self.provider,
            "as_of": self.entry.as_of,
            "stale": self.entry.stale,
            "customer_verified": self.entry.customer_verified,
            "group_scores": self.group_scores,
            "statuses": self.statuses,
            "unknown_criteria": self.unknown_criteria,
            "unknown_ratio": self.unknown_ratio,
            "residency": self.residency.to_dict(),
            "training_optout": self.optout.to_dict(),
        }


def assess(
    provider: str,
    *,
    overrides: dict[str, Any] | None = None,
    required_regions: Sequence[str] = ("EU",),
    contract_flags: dict[str, Any] | None = None,
    dpf_certified: bool | None = None,
    bcr_in_place: bool = False,
    trail: AuditTrail | None = None,
    log: bool = True,
) -> VendorAssessment:
    license.require("vendor")
    session = new_session_id()
    entry = lookup(provider, overrides)
    statuses = entry.criteria()

    weighted, unknowns = 0.0, []
    group_earned: dict[str, float] = {}
    findings: list[Finding] = []

    for c in CRITERIA:
        status = statuses.get(c.key, "unknown")
        if status not in STATUS_WEIGHT:
            status = "unknown"
        statuses[c.key] = status
        earned = STATUS_WEIGHT[status] * c.weight
        weighted += earned
        group_earned[c.group] = group_earned.get(c.group, 0.0) + earned

        if status == "unknown":
            unknowns.append(c.key)
            findings.append(Finding(
                f"vendor_unknown.{c.key}",
                Severity.HIGH if c.critical else Severity.LOW,
                f"{c.question} — not established"
                + (" (this is a critical criterion)" if c.critical else ""),
                "vendor", Action.FLAG, c.article,
                evidence={"criterion": c.key, "group": c.group, "weight": c.weight},
                remediation=f"Ask the vendor directly. {c.why}",
                params={"question": c.question, "question_tr": c.ask("tr"),
                        "critical": " (this is a critical criterion)" if c.critical else ""},
            ))
        elif status == "not_met":
            findings.append(Finding(
                f"vendor_gap.{c.key}",
                Severity.CRITICAL if c.critical else Severity.MEDIUM,
                f"{c.question} — NOT met", "vendor",
                Action.BLOCK if c.critical else Action.FLAG, c.article,
                evidence={"criterion": c.key, "group": c.group, "weight": c.weight},
                remediation=c.why,
                params={"question": c.question, "question_tr": c.ask("tr")},
            ))
        elif status == "partial" and c.critical:
            findings.append(Finding(
                f"vendor_partial.{c.key}", Severity.HIGH,
                f"{c.question} — only partially met, on a critical criterion", "vendor",
                Action.FLAG, c.article, evidence={"criterion": c.key},
                remediation=c.why,
                params={"question": c.question, "question_tr": c.ask("tr")},
            ))

    total = sum(c.weight for c in CRITERIA)
    value = round(weighted / total * 100, 1)

    residency = verify(entry, required_regions, dpf_certified=dpf_certified,
                       bcr_in_place=bcr_in_place)
    optout = enforce(entry, contract_flags)
    findings.extend(residency.findings)
    findings.extend(optout.findings)

    report = Report(module="vendor", subject=entry.display_name, session_id=session)
    report.add(*findings)

    gws = group_weights()
    group_scores = {g: round(group_earned.get(g, 0.0) / gws[g] * 100, 1) for g in GROUPS}

    if entry.stale:
        age = entry.age_days
        findings.append(Finding(
            "vendor_facts_stale", Severity.MEDIUM,
            f"the facts used for this assessment are dated {entry.as_of}"
            + (f" ({age} days old, past the {STALENESS_DAYS}-day window)" if age else
               " and carry no date"),
            "vendor", Action.FLAG,
            evidence={"as_of": entry.as_of, "age_days": age},
            remediation="Re-verify with the vendor and pass the answers via `overrides=`. Vendor "
                        "terms change without notice.",
            params={
                "as_of": entry.as_of,
                "age": (f" ({age} days old, past the {STALENESS_DAYS}-day window)" if age
                        else " and carry no date"),
                # The parenthetical is prose, so it needs its own Turkish form —
                # an English clause inside a Turkish sentence is the leak a
                # bilingual report is judged on.
                "age_tr": (f" ({age} gün önce, {STALENESS_DAYS} günlük tazelik penceresinin "
                           f"dışında)" if age else " ve tarih taşımıyor"),
            },
        ))
        report.add(findings[-1])
        report.note_limit(*i18n.both("limit.vendor_seed", as_of=entry.as_of))

    if not entry.customer_verified:
        report.note_limit(*i18n.both("limit.vendor_unverified"))

    score = Score(
        "vendor_score", value, Method.DETERMINISTIC, threshold=60.0,
        basis={**group_scores, "unknown_criteria": len(unknowns),
               "unknown_penalty_applied": True, "customer_verified": entry.customer_verified},
    )
    report.add_score(score)

    if len(unknowns) > len(CRITERIA) * 0.3:
        report.note_limit(*i18n.both(
            "limit.vendor_unknowns", n=len(unknowns), total=len(CRITERIA),
            credit=f"{STATUS_WEIGHT['unknown']:.0%}"))

    report.coverage = {
        GROUPS[g]: (Coverage.COVERED if s >= 80 else
                    Coverage.PARTIAL if s >= 40 else Coverage.MISSING)
        for g, s in group_scores.items()
    }
    report.metadata = {
        "provider_key": entry.key, "as_of": entry.as_of, "stale": entry.stale,
        "required_regions": list(required_regions),
        "residency_verdict": residency.verdict, "residency_mechanism": residency.mechanism,
        "training_optout_verdict": optout.verdict,
        "source": entry.get("source"),
    }

    (trail or default_trail()).log("vendor", "vendor_assessment", {
        "provider": entry.key, "score": value, "group_scores": group_scores,
        "unknown_criteria": len(unknowns), "residency_verdict": residency.verdict,
        "training_optout_verdict": optout.verdict, "stale": entry.stale,
        "worst_severity": report.worst_severity.value if report.worst_severity else None,
    }, session_id=session) if log else None

    return VendorAssessment(
        provider=entry.display_name, entry=entry, score=score, group_scores=group_scores,
        statuses=statuses, residency=residency, optout=optout, report=report,
        unknown_criteria=unknowns,
    )
