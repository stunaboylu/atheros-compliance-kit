"""Fallback triggers and output-side checks.

The rule the whole file exists to enforce: a fallback is never silent. Every
degraded response carries `degraded=True` and the trigger that caused it, and
the ledger records both. A silent low-quality fallback in a compliance product
is worse than an outage — an outage is visible.
"""
from __future__ import annotations

import re
from dataclasses import dataclass
from enum import Enum

from ..core.findings import Action, Finding, Severity


class Trigger(str, Enum):
    PROVIDER_ERROR = "provider_error"
    TIMEOUT = "timeout"
    REFUSAL = "refusal"
    OUTPUT_BLOCKED = "output_blocked"
    INPUT_BLOCKED = "input_blocked"
    BUDGET_EXCEEDED = "budget_exceeded"
    EMPTY_RESPONSE = "empty_response"


#: Provider refusals. Detected so `fallback` can substitute something useful
#: rather than handing the caller the provider's apology as if it were an answer.
_REFUSAL_RE = re.compile(
    r"\b(?:i(?:'m| am)\s+(?:sorry|unable|not\s+able)|i\s+cannot\s+(?:assist|help|comply|provide)"
    r"|as\s+an\s+ai(?:\s+language)?\s+model,?\s+i\s+(?:cannot|can't|am\s+unable)"
    r"|i\s+(?:can(?:not|'t))\s+(?:fulfill|complete)\s+(?:that|this)\s+request)\b",
    re.IGNORECASE,
)

#: Assurance overreach — claiming certainty no evidence can support. Inherited
#: from an earlier in-house output gate. In this product the sentence "fully
#: compliant" coming back from a model and reaching a report is the failure mode
#: with actual legal consequences, so it BLOCKS rather than flags.
_OVERCLAIM_RE = re.compile(
    r"\b(?:fully|100%|completely|totally|guaranteed|certified)\s+compliant"
    r"|\bguarantee[sd]?\s+compliance"
    r"|\b(?:is|are)\s+certified\s+(?:under|for|to)"
    r"|\bno\s+(?:further\s+)?(?:action|remediation)\s+(?:is\s+)?(?:required|needed)\b"
    r"|\bthis\s+(?:system|model)\s+is\s+compliant\b",
    re.IGNORECASE,
)


def is_refusal(text: str) -> bool:
    return bool(text) and bool(_REFUSAL_RE.search(text))


def check_output(text: str, *, detect_refusal: bool = True,
                 detect_overclaim: bool = True) -> list[Finding]:
    """Output-side gate. Runs before the value returns to the application."""
    findings: list[Finding] = []
    if not text or not text.strip():
        findings.append(Finding(
            "empty_response", Severity.MEDIUM, "the provider returned no content",
            "guard", Action.FLAG, evidence={"length": len(text or "")},
            remediation="Retry, or fall back — do not present an empty answer as a result.",
        ))
        return findings
    if detect_refusal and is_refusal(text):
        findings.append(Finding(
            "provider_refusal", Severity.LOW,
            "the provider declined the request rather than answering it",
            "guard", Action.FLAG,
            remediation="Substitute the configured fallback; do not surface the refusal as an answer.",
        ))
    if detect_overclaim and _OVERCLAIM_RE.search(text):
        findings.append(Finding(
            "assurance_overclaim", Severity.CRITICAL,
            "model output asserts compliance or certainty that no evidence supports",
            "guard", Action.BLOCK, article="ISO 42001 §8.3",
            remediation=(
                "Never let this text reach a user or a report. Compliance conclusions come "
                "from evidence-graded assessment, not from model prose."
            ),
        ))
    return findings


@dataclass
class FallbackOutcome:
    text: str
    trigger: Trigger
    degraded: bool = True
    attempts: int = 0
    source: str = "static"        # "retry" | "secondary" | "static"

    def to_dict(self) -> dict:
        return {
            "trigger": self.trigger.value,
            "degraded": self.degraded,
            "attempts": self.attempts,
            "source": self.source,
        }
