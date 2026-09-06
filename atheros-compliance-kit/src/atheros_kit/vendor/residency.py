"""Data-residency verification and transfer-mechanism analysis.

What this does: establishes which of the three lawful transfer routes is even
available for a given provider and region set, and reports when none is.

What this deliberately does NOT do: decide whether a transfer is lawful. That
turns on a transfer impact assessment, the specific contract, and facts about the
recipient's jurisdiction that no library can read. The verdict vocabulary is
chosen to keep that line visible — `requires_scc` means "this route exists and
you must evidence it", never "you are fine".
"""
from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass, field

from ..core.findings import Action, Finding, Severity
from .registry import ADEQUACY_COUNTRIES, CONDITIONAL_ADEQUACY, EEA, ProviderEntry


@dataclass
class ResidencyResult:
    provider: str
    processing_regions: list[str]
    required_regions: list[str]
    verdict: str                       # compliant | requires_scc | non_compliant | unknown
    mechanism: str                     # adequacy | scc | bcr | none | unknown
    outside_required: list[str] = field(default_factory=list)
    findings: list[Finding] = field(default_factory=list)
    notes: list[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "provider": self.provider, "processing_regions": self.processing_regions,
            "required_regions": self.required_regions, "verdict": self.verdict,
            "mechanism": self.mechanism, "outside_required": self.outside_required,
            "notes": self.notes,
        }


def _normalise(region: str) -> str:
    r = (region or "").strip().upper()
    return {"EUROPE": "EU", "EEA": "EU", "UNITED STATES": "US", "USA": "US",
            "UNITED KINGDOM": "GB", "UK": "GB"}.get(r, r)


def verify(
    entry: ProviderEntry,
    required_regions: Sequence[str] = ("EU",),
    *,
    dpf_certified: bool | None = None,
    bcr_in_place: bool = False,
) -> ResidencyResult:
    """Check where a provider processes against where the customer requires it.

    `dpf_certified` must be stated explicitly for a US recipient. The EU–US Data
    Privacy Framework provides adequacy only for a recipient that self-certified
    under it, so "the US has adequacy" is true of the framework and false of any
    particular company until someone checks the list.
    """
    required = [_normalise(r) for r in required_regions] or ["EU"]
    processing = [_normalise(r) for r in (entry.get("regions") or [])]
    res = ResidencyResult(provider=entry.display_name, processing_regions=processing,
                          required_regions=required, verdict="unknown", mechanism="unknown")

    if not processing:
        res.notes.append(
            "The provider's processing regions are not recorded. This is unknown, not compliant — "
            "ask the vendor in writing and pass the answer via `overrides`."
        )
        res.findings.append(Finding(
            "residency_unknown", Severity.MEDIUM,
            f"processing regions for {entry.display_name} could not be established",
            "vendor", Action.FLAG, "GDPR Ch. V",
            remediation="Request the processing locations and sub-processor list from the vendor.",
            params={"provider": entry.display_name},
        ))
        return res

    required_set = {r for r in required}
    eea_required = bool(required_set & EEA)
    outside = [r for r in processing if r not in required_set and not (eea_required and r in EEA)]
    res.outside_required = outside

    if not outside:
        res.verdict, res.mechanism = "compliant", "adequacy"
        res.notes.append(
            f"All recorded processing is within the required region(s) {', '.join(required)}. "
            f"Confirm the vendor lets you PIN the region rather than merely offering it — "
            f"see the `data_residency_choice` criterion."
        )
        return res

    declared = (entry.get("transfer_mechanism") or "unknown").lower()
    adequate = [r for r in outside if r in ADEQUACY_COUNTRIES and r not in CONDITIONAL_ADEQUACY]
    conditional = [r for r in outside if r in CONDITIONAL_ADEQUACY]
    no_route = [r for r in outside if r not in ADEQUACY_COUNTRIES]

    if bcr_in_place:
        res.verdict, res.mechanism = "requires_scc", "bcr"
        res.notes.append("Binding Corporate Rules were declared; the transfer route exists and "
                         "must be evidenced by the approved BCR document.")
    # SCCs are the mechanism FOR countries without an adequacy decision, so a
    # declared SCC covers exactly the `no_route` case. Checking `no_route` first
    # made the finding contradict its own wording: it said "neither an adequacy
    # decision nor a declared transfer mechanism" about providers that declare
    # SCCs, and reported them non_compliant when the correct verdict is
    # requires_scc — the route exists and has to be evidenced.
    elif no_route and declared == "scc":
        res.verdict, res.mechanism = "requires_scc", "scc"
        res.findings.append(Finding(
            "transfer_requires_scc", Severity.HIGH,
            f"{entry.display_name} processes in {', '.join(no_route)}, which has no adequacy "
            f"decision; SCCs are declared and must be evidenced, with a transfer impact "
            f"assessment for each such country",
            "vendor", Action.FLAG, "GDPR Ch. V",
            evidence={"regions": no_route, "mechanism": "scc"},
            params={"provider": entry.display_name, "required": ", ".join(required),
                    "regions": ", ".join(no_route)},
            remediation="Attach the executed SCCs and a transfer impact assessment covering these "
                        "countries specifically. Where the assessment cannot support the transfer, "
                        "pin processing to an adequate region instead — this provider supports it.",
        ))
    elif no_route:
        res.verdict, res.mechanism = "non_compliant", "none"
        res.findings.append(Finding(
            "transfer_no_mechanism", Severity.CRITICAL,
            f"{entry.display_name} processes in {', '.join(no_route)}, which has neither an "
            f"adequacy decision nor a declared transfer mechanism",
            "vendor", Action.BLOCK, "GDPR Ch. V",
            evidence={"regions": no_route},
            remediation="Do not transfer personal data on this route. Pin processing to an "
                        "adequate region, or execute SCCs with a transfer impact assessment.",
            params={"provider": entry.display_name, "regions": ", ".join(no_route)},
        ))
    elif conditional and dpf_certified is not True:
        res.verdict, res.mechanism = "requires_scc", ("scc" if declared == "scc" else "unknown")
        res.findings.append(Finding(
            "dpf_certification_unverified", Severity.HIGH,
            f"{entry.display_name} processes in {', '.join(conditional)}. Adequacy there depends "
            f"on the recipient's own Data Privacy Framework certification, which has not been "
            f"confirmed for this vendor",
            "vendor", Action.FLAG, "GDPR Ch. V",
            evidence={"regions": conditional, "dpf_certified": dpf_certified},
            remediation="Check the vendor on the DPF participant list. If it is not certified, "
                        "the transfer needs SCCs and a transfer impact assessment.",
            params={"provider": entry.display_name, "regions": ", ".join(conditional)},
        ))
        res.notes.append("'The US has adequacy' is true of the framework and not of any particular "
                         "company until its certification is checked.")
    elif declared == "scc":
        res.verdict, res.mechanism = "requires_scc", "scc"
        res.findings.append(Finding(
            "transfer_requires_scc", Severity.MEDIUM,
            f"{entry.display_name} processes outside {', '.join(required)} "
            f"({', '.join(outside)}); SCCs are declared and must be evidenced",
            "vendor", Action.FLAG, "GDPR Ch. V",
            evidence={"regions": outside},
            remediation="Attach the executed SCCs and the transfer impact assessment to the "
                        "vendor file. A declared mechanism is not an evidenced one.",
            params={"provider": entry.display_name, "required": ", ".join(required),
                    "regions": ", ".join(outside)},
        ))
    elif adequate:
        res.verdict, res.mechanism = "compliant", "adequacy"
        res.notes.append(f"Processing in {', '.join(adequate)} is covered by an adequacy decision.")
    else:
        res.verdict, res.mechanism = "unknown", "unknown"
        res.findings.append(Finding(
            "transfer_mechanism_unknown", Severity.HIGH,
            f"{entry.display_name} processes outside the required region(s) and no transfer "
            f"mechanism is recorded",
            "vendor", Action.FLAG, "GDPR Ch. V", evidence={"regions": outside},
            remediation="Establish the mechanism in writing before the next transfer.",
            params={"provider": entry.display_name},
        ))

    if entry.stale:
        res.notes.append(
            f"These facts are dated {entry.as_of} and are past the {180}-day freshness window. "
            f"Re-verify before relying on this verdict."
        )
    return res
