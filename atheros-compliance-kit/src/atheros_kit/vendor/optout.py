"""Training opt-out enforcement.

The distinction this module exists to enforce: **available ≠ enabled ≠
contractual**. Three different facts, routinely collapsed into one line in a
vendor questionnaire:

1. *Available* — the vendor offers an opt-out. A marketing fact.
2. *Enabled* — it is switched on for this account. An operational fact, and the
   one nobody checks.
3. *Contractual* — the commitment survives a terms change and is enforceable. The
   only one worth anything in a dispute.

A vendor scoring "yes" on the first and nothing on the other two is the normal
case, and reporting that as compliant is how prompts end up in a training set.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from ..core.findings import Action, Finding, Severity
from .registry import ProviderEntry


@dataclass
class OptOutResult:
    provider: str
    available: bool | None
    enabled: bool | None
    contractual: bool | None
    zdr_available: bool | None
    zdr_enabled: bool | None
    verdict: str                     # enforced | available_not_evidenced | not_available | unknown
    findings: list[Finding] = field(default_factory=list)
    notes: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "provider": self.provider, "available": self.available, "enabled": self.enabled,
            "contractual": self.contractual, "zdr_available": self.zdr_available,
            "zdr_enabled": self.zdr_enabled, "verdict": self.verdict, "notes": self.notes,
        }


def enforce(entry: ProviderEntry, contract_flags: dict[str, Any] | None = None) -> OptOutResult:
    """Assess the opt-out position.

    `contract_flags` carries what the CUSTOMER can attest from their own signed
    agreement and console — `{"training_optout_enabled": True,
    "training_optout_contractual": True, "zdr_enabled": False}`. Nothing here
    infers those from the vendor's public documentation, because the vendor's
    public documentation is not evidence about a particular account.
    """
    flags = contract_flags or {}
    res = OptOutResult(
        provider=entry.display_name,
        available=entry.get("training_optout_available"),
        enabled=flags.get("training_optout_enabled"),
        contractual=flags.get("training_optout_contractual"),
        zdr_available=entry.get("zdr_available"),
        zdr_enabled=flags.get("zdr_enabled", entry.get("zdr_default") or None),
        verdict="unknown",
    )

    if res.available is False:
        res.verdict = "not_available"
        res.findings.append(Finding(
            "training_optout_unavailable", Severity.CRITICAL,
            f"{entry.display_name} offers no opt-out from using inputs for model training",
            "vendor", Action.BLOCK, "GDPR Art. 28(3)(a)",
            remediation="Do not send confidential or personal data to this provider. Every prompt "
                        "is a disclosure into a training corpus you cannot recall.",
            params={"provider": entry.display_name},
        ))
        return res

    if res.available is None:
        res.verdict = "unknown"
        res.findings.append(Finding(
            "training_optout_unknown", Severity.HIGH,
            f"whether {entry.display_name} uses inputs for training could not be established",
            "vendor", Action.FLAG, "GDPR Art. 28(3)(a)",
            remediation="Get this in writing before the next production call. An unanswered "
                        "question here is not a neutral fact.",
            params={"provider": entry.display_name},
        ))
        return res

    # Available. Now the two questions that actually matter.
    if res.enabled is True and res.contractual is True:
        res.verdict = "enforced"
        res.notes.append(
            "Opt-out is both switched on for this account and contractually committed. Re-verify "
            "after any change to the vendor's terms — a commitment in a version of the terms you "
            "no longer operate under is not a commitment."
        )
    else:
        res.verdict = "available_not_evidenced"
        missing: list[str] = []
        missing_tr: list[str] = []
        if res.enabled is not True:
            missing.append("not confirmed as enabled for this account")
            missing_tr.append("bu hesap için etkin olduğu doğrulanmadı")
        if res.contractual is not True:
            missing.append("no contractual commitment recorded")
            missing_tr.append("kayıtlı bir sözleşmesel taahhüt yok")
        res.findings.append(Finding(
            "training_optout_not_evidenced", Severity.HIGH,
            f"{entry.display_name} offers a training opt-out, but it is "
            f"{' and '.join(missing)}",
            "vendor", Action.FLAG, "GDPR Art. 28(3)(a)",
            evidence={"available": res.available, "enabled": res.enabled,
                      "contractual": res.contractual},
            remediation="Confirm the setting in the account console, then get the commitment into "
                        "the DPA. An opt-out that exists and is off protects nothing.",
            params={"provider": entry.display_name, "missing": " and ".join(missing),
                    "missing_tr": " ve ".join(missing_tr)},
        ))

    if res.zdr_available and res.zdr_enabled is not True:
        res.findings.append(Finding(
            "zdr_not_enabled", Severity.MEDIUM,
            f"{entry.display_name} supports zero data retention but it is not confirmed enabled "
            f"for this account",
            "vendor", Action.FLAG,
            evidence={"zdr_available": res.zdr_available, "zdr_enabled": res.zdr_enabled},
            remediation="Enable ZDR, or record the business reason for retaining prompts and the "
                        "retention period that applies to them.",
            params={"provider": entry.display_name},
        ))
    return res
