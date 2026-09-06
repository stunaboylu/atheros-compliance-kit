"""The CI/CD compliance-and-safety regression gate.

`gate.run(config)` executes the configured checks, compares them to thresholds,
writes the reports, and returns an exit code. This is the mechanism that turns a
one-off assessment into a control: a governance number nobody enforces decays,
and the only enforcement point engineers respect is the one that fails the build.

Two rules the gate follows without exception:

- **An unmeasured check never passes.** A threshold on a score of `None` returns
  `unmeasured`, which fails by default. A gate that treats "we could not measure
  it" as green is a gate that goes green when the measurement breaks — the exact
  moment it should not.
- **Every skipped check is printed.** If a module was not configured, the summary
  says so. Silent partial coverage reads as full coverage.
"""
from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from ..core import i18n, license
from ..core.audit import AuditTrail, default_trail, new_session_id
from ..core.config import Config
from ..core.findings import Severity

EXIT_OK, EXIT_FAIL, EXIT_ERROR = 0, 1, 2


def _accepts_locale(fn) -> bool:
    """Whether a report object's to_dict takes a locale.

    The gate accepts shims (the CLI replays a previously written JSON report
    through one) as well as live objects, and a shim has no reason to carry a
    localiser. Asking rather than assuming keeps both callers working.
    """
    import inspect

    try:
        return "locale" in inspect.signature(fn).parameters
    except (TypeError, ValueError):
        return False


@dataclass
class CheckOutcome:
    name: str
    status: str                  # pass | fail | unmeasured | skipped | error
    actual: Any = None
    threshold: Any = None
    detail: str = ""

    @property
    def blocking(self) -> bool:
        return self.status in ("fail", "unmeasured", "error")

    def to_dict(self) -> dict[str, Any]:
        return {"name": self.name, "status": self.status, "actual": self.actual,
                "threshold": self.threshold, "detail": self.detail}


@dataclass
class GateResult:
    outcomes: list[CheckOutcome] = field(default_factory=list)
    reports: dict[str, Any] = field(default_factory=dict)
    session_id: str = "-"
    artefacts: list[str] = field(default_factory=list)
    locale: str = "en"

    @property
    def passed(self) -> bool:
        return not any(o.blocking for o in self.outcomes)

    @property
    def exit_code(self) -> int:
        if any(o.status == "error" for o in self.outcomes):
            return EXIT_ERROR
        return EXIT_OK if self.passed else EXIT_FAIL

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema": "atheros.gate/v1",
            "locale": self.locale,
            "session_id": self.session_id,
            "passed": self.passed,
            "exit_code": self.exit_code,
            "checks": [o.to_dict() for o in self.outcomes],
            "reports": self.reports,
            "artefacts": self.artefacts,
        }

    def to_markdown(self, locale: str | None = None) -> str:
        lo = i18n.resolve_locale(locale or self.locale)
        t = lambda key, **kw: i18n.ui(key, lo, **kw)  # noqa: E731
        icon = {"pass": "✅", "fail": "❌", "unmeasured": "⚠️", "skipped": "⏭️", "error": "💥"}
        result = t("gate.passed") if self.passed else t("gate.failed")
        lines = [
            f"## {t('gate.title', result=result)}",
            "",
            f"| | {t('col.check')} | {t('col.value')} | {t('col.threshold')} | {t('col.detail')} |",
            "|---|---|---|---|---|",
        ]
        for o in self.outcomes:
            lines.append(
                f"| {icon.get(o.status, '·')} | `{o.name}` | "
                f"{o.actual if o.actual is not None else '—'} | "
                f"{o.threshold if o.threshold is not None else '—'} | {o.detail} |"
            )
        skipped = [o for o in self.outcomes if o.status == "skipped"]
        if skipped:
            lines += ["", "> " + t("gate.skipped_note", n=len(skipped),
                                   names=", ".join(o.name for o in skipped))]
        if any(o.status == "unmeasured" for o in self.outcomes):
            lines += ["", "> " + t("gate.unmeasured_note")]
        lines += ["", f"_{t('gate.footer')}_"]
        return "\n".join(lines)


def _cmp(name: str, actual: float | None, threshold: float | None, *,
         direction: str = "min", locale: str = "en") -> CheckOutcome:
    if threshold is None:
        return CheckOutcome(name, "skipped", actual, None, i18n.ui("gate.no_threshold", locale))
    if actual is None:
        return CheckOutcome(name, "unmeasured", None, threshold,
                            i18n.ui("gate.unmeasured_detail", locale))
    ok = actual >= threshold if direction == "min" else actual <= threshold
    return CheckOutcome(name, "pass" if ok else "fail", actual, threshold,
                        "" if ok else f"{actual} {'<' if direction == 'min' else '>'} {threshold}")


def run(
    config: Config | dict[str, Any] | None = None,
    *,
    rag_audit: Any = None,
    classification: Any = None,
    vendor_assessments: list[Any] | None = None,
    guard_ledger: Any = None,
    trail: AuditTrail | None = None,
    write_to: str | Path | None = None,
    locale: str | None = None,
) -> GateResult:
    """Evaluate everything supplied against the configured thresholds.

    Inputs are passed in rather than discovered, so the gate is a pure function of
    what the caller measured. The CLI is what does the discovering — keeping the
    two apart is why this is testable without a corpus, a network, or a key.
    """
    license.require("cicd")
    cfg = config if isinstance(config, Config) else Config.load(**(config or {}))
    fail_on = cfg.get("fail_on", {}) or {}
    lo = i18n.resolve_locale(locale or cfg.get("locale"))
    res = GateResult(session_id=new_session_id(), locale=lo)
    trail = trail or default_trail()

    # ── RAG ──────────────────────────────────────────────────────────────────
    if rag_audit is not None:
        res.outcomes.append(_cmp("fairness_score", rag_audit.fairness_score,
                                 fail_on.get("fairness_score_below"), locale=lo))
        res.outcomes.append(_cmp("quality_score", rag_audit.quality_score,
                                 fail_on.get("quality_score_below"), locale=lo))
        bad_verdicts = fail_on.get("drift_verdict_in") or []
        if rag_audit.drift is None:
            res.outcomes.append(CheckOutcome("corpus_drift", "skipped", None, bad_verdicts,
                                             i18n.ui("gate.no_baseline", lo)))
        elif bad_verdicts:
            v = rag_audit.drift.verdict
            res.outcomes.append(CheckOutcome(
                "corpus_drift", "unmeasured" if v == "unmeasurable" else
                ("fail" if v in bad_verdicts else "pass"), v, bad_verdicts,
                "" if v not in bad_verdicts else f"corpus verdict is '{v}'"))
        res.reports["rag"] = rag_audit.to_dict(locale=lo) if _accepts_locale(rag_audit.to_dict) \
            else rag_audit.to_dict()
    else:
        res.outcomes.append(CheckOutcome("rag_audit", "skipped",
                                         detail=i18n.ui("gate.not_configured", lo)))

    # ── EU AI Act ────────────────────────────────────────────────────────────
    if classification is not None:
        bad_tiers = fail_on.get("risk_tier_in") or []
        tier = classification.tier
        res.outcomes.append(CheckOutcome(
            "eu_ai_act_tier", "fail" if tier in bad_tiers else "pass", tier, bad_tiers,
            "" if tier not in bad_tiers else f"tier '{tier}' is configured to fail the build"))
        if classification.grey_zone:
            res.outcomes.append(CheckOutcome(
                "classification_certainty", "unmeasured", classification.confidence, None,
                "the classification is a grey zone and needs human review"))
        res.reports["euact"] = classification.to_dict()
    else:
        res.outcomes.append(CheckOutcome("eu_ai_act", "skipped",
                                         detail=i18n.ui("gate.not_configured", lo)))

    # ── Vendors ──────────────────────────────────────────────────────────────
    if vendor_assessments:
        floor = fail_on.get("vendor_score_below")
        bad_res = fail_on.get("residency_verdict_in") or []
        for a in vendor_assessments:
            res.outcomes.append(_cmp(f"vendor_score.{a.entry.key}", a.score.value, floor,
                                     locale=lo))
            if bad_res:
                v = a.residency.verdict
                res.outcomes.append(CheckOutcome(
                    f"residency.{a.entry.key}",
                    "unmeasured" if v == "unknown" else ("fail" if v in bad_res else "pass"),
                    v, bad_res, "" if v not in bad_res else f"residency verdict '{v}'"))
        res.reports["vendor"] = [
            a.to_dict(locale=lo) if _accepts_locale(a.to_dict) else a.to_dict()
            for a in vendor_assessments
        ]
    else:
        res.outcomes.append(CheckOutcome("vendor", "skipped",
                                         detail=i18n.ui("gate.not_configured", lo)))

    # ── Guard ────────────────────────────────────────────────────────────────
    if guard_ledger is not None:
        summary = guard_ledger if isinstance(guard_ledger, dict) else guard_ledger.summary()
        cap = fail_on.get("guard_blocks_above")
        blocked = summary.get("blocked_calls", 0)
        res.outcomes.append(CheckOutcome(
            "guard_blocks", "pass" if cap is None or blocked <= cap else "fail",
            blocked, cap, "" if cap is None or blocked <= cap
            else f"{blocked} blocked invocation(s) exceed the configured cap of {cap}"))
        res.reports["guard"] = summary
    else:
        res.outcomes.append(CheckOutcome("guard", "skipped",
                                         detail=i18n.ui("gate.not_configured", lo)))

    # ── Ledger integrity ─────────────────────────────────────────────────────
    if fail_on.get("chain_violation"):
        intact, violations = trail.verify_chain(locale=lo)
        res.outcomes.append(CheckOutcome(
            "audit_chain", "pass" if intact else "fail", "intact" if intact else "violated",
            "intact", "" if intact else f"{len(violations)} violation(s): {violations[0]}"))

    # ── artefacts ────────────────────────────────────────────────────────────
    out_dir = Path(write_to or cfg.get("report_dir", ".atheros/reports"))
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / "atheros-report.json").write_text(
        json.dumps(res.to_dict(), indent=2, ensure_ascii=False), encoding="utf-8")
    (out_dir / "atheros-summary.md").write_text(res.to_markdown(lo), encoding="utf-8")
    res.artefacts = [str(out_dir / "atheros-report.json"), str(out_dir / "atheros-summary.md")]

    trail.log("cicd", "gate_run", {
        "passed": res.passed, "exit_code": res.exit_code,
        "checks": {o.name: o.status for o in res.outcomes},
    }, session_id=res.session_id)
    return res
