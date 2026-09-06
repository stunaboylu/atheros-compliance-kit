"""Seeded provider facts — with dates, and a staleness rule.

**Read this before trusting anything below.** These entries are a starting point
assembled from public documentation, not a maintained compliance database. Vendor
terms change without notice and the difference between "offers zero data
retention" and "has it enabled on your account" is a contract, not a web page.

Two consequences are enforced in code rather than left to a disclaimer:

1. Every fact carries `as_of`. A fact without a date is a rumour.
2. Past `STALENESS_DAYS` an entry produces a finding, and the assessment that
   used it is marked stale. A governance tool whose vendor data quietly ages into
   fiction is worse than one with no vendor data, because the number still looks
   current.

The intended workflow is `overrides=` — a customer's own verified answers from
their signed DPA — with this registry as the prompt for what to go and verify.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date, datetime
from typing import Any

#: An entry older than this is reported as stale and its confidence is dropped.
STALENESS_DAYS = 180

#: criterion key → "met" | "partial" | "not_met" | "unknown"
ProviderFacts = dict[str, Any]

PROVIDERS: dict[str, ProviderFacts] = {
    "openai": {
        "display_name": "OpenAI",
        "as_of": "2026-02-01",
        "source": "public trust portal and API data-usage documentation",
        "regions": ["US", "EU"],
        "eu_data_residency_available": True,
        "transfer_mechanism": "scc",
        "training_optout_available": True,
        "training_optout_default_for_api": True,
        "zdr_available": True,
        "zdr_default": False,
        "criteria": {
            "iso_27001": "met", "iso_42001": "unknown", "soc2_type2": "met",
            "gdpr_dpa": "met", "sccs": "met", "subprocessor_list": "met",
            "zero_data_retention": "partial", "log_retention_defined": "met",
            "human_review_optout": "met", "encryption_in_transit": "met",
            "encryption_at_rest": "met", "tenant_isolation": "met",
            "pen_test_report": "partial", "vuln_disclosure": "met",
            "model_card": "partial", "eval_reports": "partial",
            "incident_history_disclosed": "partial", "deprecation_policy": "met",
            "sla": "met", "status_page": "met", "support_tier": "met",
            "exit_plan": "partial", "training_optout": "met", "data_residency_choice": "met",
        },
    },
    "anthropic": {
        "display_name": "Anthropic",
        "as_of": "2026-02-01",
        "source": "public trust centre and commercial terms",
        "regions": ["US", "EU"],
        "eu_data_residency_available": True,
        "transfer_mechanism": "scc",
        "training_optout_available": True,
        "training_optout_default_for_api": True,
        "zdr_available": True,
        "zdr_default": False,
        "criteria": {
            "iso_27001": "met", "iso_42001": "unknown", "soc2_type2": "met",
            "gdpr_dpa": "met", "sccs": "met", "subprocessor_list": "met",
            "zero_data_retention": "partial", "log_retention_defined": "met",
            "human_review_optout": "met", "encryption_in_transit": "met",
            "encryption_at_rest": "met", "tenant_isolation": "met",
            "pen_test_report": "partial", "vuln_disclosure": "met",
            "model_card": "met", "eval_reports": "met",
            "incident_history_disclosed": "partial", "deprecation_policy": "met",
            "sla": "met", "status_page": "met", "support_tier": "met",
            "exit_plan": "partial", "training_optout": "met", "data_residency_choice": "met",
        },
    },
    "google_vertex": {
        "display_name": "Google Cloud Vertex AI",
        "as_of": "2026-02-01",
        "source": "Google Cloud compliance resource centre",
        "regions": ["US", "EU", "ASIA"],
        "eu_data_residency_available": True,
        "transfer_mechanism": "scc",
        "training_optout_available": True,
        "training_optout_default_for_api": True,
        "zdr_available": True,
        "zdr_default": True,
        "criteria": {
            "iso_27001": "met", "iso_42001": "met", "soc2_type2": "met",
            "gdpr_dpa": "met", "sccs": "met", "subprocessor_list": "met",
            "zero_data_retention": "met", "log_retention_defined": "met",
            "human_review_optout": "met", "encryption_in_transit": "met",
            "encryption_at_rest": "met", "tenant_isolation": "met",
            "pen_test_report": "met", "vuln_disclosure": "met",
            "model_card": "met", "eval_reports": "partial",
            "incident_history_disclosed": "met", "deprecation_policy": "met",
            "sla": "met", "status_page": "met", "support_tier": "met",
            "exit_plan": "met", "training_optout": "met", "data_residency_choice": "met",
        },
    },
    "azure_openai": {
        "display_name": "Microsoft Azure OpenAI Service",
        "as_of": "2026-02-01",
        "source": "Microsoft Trust Center and Azure service terms",
        "regions": ["US", "EU", "UK", "ASIA"],
        "eu_data_residency_available": True,
        "transfer_mechanism": "scc",
        "training_optout_available": True,
        "training_optout_default_for_api": True,
        "zdr_available": True,
        "zdr_default": False,
        "criteria": {
            "iso_27001": "met", "iso_42001": "met", "soc2_type2": "met",
            "gdpr_dpa": "met", "sccs": "met", "subprocessor_list": "met",
            "zero_data_retention": "partial", "log_retention_defined": "met",
            "human_review_optout": "partial", "encryption_in_transit": "met",
            "encryption_at_rest": "met", "tenant_isolation": "met",
            "pen_test_report": "met", "vuln_disclosure": "met",
            "model_card": "partial", "eval_reports": "partial",
            "incident_history_disclosed": "met", "deprecation_policy": "met",
            "sla": "met", "status_page": "met", "support_tier": "met",
            "exit_plan": "met", "training_optout": "met", "data_residency_choice": "met",
        },
    },
    "aws_bedrock": {
        "display_name": "AWS Bedrock",
        "as_of": "2026-02-01",
        "source": "AWS compliance programmes and Bedrock data-protection documentation",
        "regions": ["US", "EU", "ASIA"],
        "eu_data_residency_available": True,
        "transfer_mechanism": "scc",
        "training_optout_available": True,
        "training_optout_default_for_api": True,
        "zdr_available": True,
        "zdr_default": True,
        "criteria": {
            "iso_27001": "met", "iso_42001": "unknown", "soc2_type2": "met",
            "gdpr_dpa": "met", "sccs": "met", "subprocessor_list": "met",
            "zero_data_retention": "met", "log_retention_defined": "met",
            "human_review_optout": "met", "encryption_in_transit": "met",
            "encryption_at_rest": "met", "tenant_isolation": "met",
            "pen_test_report": "met", "vuln_disclosure": "met",
            "model_card": "partial", "eval_reports": "partial",
            "incident_history_disclosed": "met", "deprecation_policy": "met",
            "sla": "met", "status_page": "met", "support_tier": "met",
            "exit_plan": "met", "training_optout": "met", "data_residency_choice": "met",
        },
    },
    "mistral": {
        "display_name": "Mistral AI",
        "as_of": "2026-02-01",
        "source": "public documentation and terms of service",
        "regions": ["EU"],
        "eu_data_residency_available": True,
        "transfer_mechanism": "adequacy",   # EU-established processor
        "training_optout_available": True,
        "training_optout_default_for_api": True,
        "zdr_available": True,
        "zdr_default": False,
        "criteria": {
            "iso_27001": "met", "iso_42001": "unknown", "soc2_type2": "partial",
            "gdpr_dpa": "met", "sccs": "met", "subprocessor_list": "partial",
            "zero_data_retention": "partial", "log_retention_defined": "partial",
            "human_review_optout": "unknown", "encryption_in_transit": "met",
            "encryption_at_rest": "met", "tenant_isolation": "partial",
            "pen_test_report": "unknown", "vuln_disclosure": "partial",
            "model_card": "met", "eval_reports": "partial",
            "incident_history_disclosed": "unknown", "deprecation_policy": "partial",
            "sla": "partial", "status_page": "met", "support_tier": "partial",
            "exit_plan": "unknown", "training_optout": "met", "data_residency_choice": "met",
        },
    },
    "cohere": {
        "display_name": "Cohere",
        "as_of": "2026-02-01",
        "source": "public security and privacy documentation",
        "regions": ["US", "EU", "CA"],
        "eu_data_residency_available": True,
        "transfer_mechanism": "scc",
        "training_optout_available": True,
        "training_optout_default_for_api": True,
        "zdr_available": True,
        "zdr_default": False,
        "criteria": {
            "iso_27001": "met", "iso_42001": "unknown", "soc2_type2": "met",
            "gdpr_dpa": "met", "sccs": "met", "subprocessor_list": "partial",
            "zero_data_retention": "partial", "log_retention_defined": "met",
            "human_review_optout": "partial", "encryption_in_transit": "met",
            "encryption_at_rest": "met", "tenant_isolation": "partial",
            "pen_test_report": "partial", "vuln_disclosure": "met",
            "model_card": "partial", "eval_reports": "partial",
            "incident_history_disclosed": "unknown", "deprecation_policy": "partial",
            "sla": "met", "status_page": "met", "support_tier": "met",
            "exit_plan": "partial", "training_optout": "met", "data_residency_choice": "partial",
        },
    },
}

#: Third countries with a European Commission adequacy decision. The mechanism a
#: transfer relies on is a legal determination; this list only says which of the
#: three routes is even available.
ADEQUACY_COUNTRIES = {
    "AD", "AR", "CA", "CH", "FO", "GG", "IL", "IM", "JE", "JP", "NZ", "KR", "GB", "UY", "US",
}
#: The US entry is the Data Privacy Framework, and it applies ONLY to a recipient
#: that self-certified under it. "US" alone therefore never establishes adequacy,
#: which is why `residency.verify` demands the certification flag explicitly.
CONDITIONAL_ADEQUACY = {"US"}

EEA = {
    "AT", "BE", "BG", "HR", "CY", "CZ", "DK", "EE", "FI", "FR", "DE", "GR", "HU", "IS", "IE",
    "IT", "LV", "LI", "LT", "LU", "MT", "NL", "NO", "PL", "PT", "RO", "SK", "SI", "ES", "SE",
    "EU", "EEA",
}


@dataclass
class ProviderEntry:
    key: str
    facts: ProviderFacts
    overrides: dict[str, Any] = field(default_factory=dict)

    @property
    def display_name(self) -> str:
        return self.overrides.get("display_name") or self.facts.get("display_name") or self.key

    @property
    def as_of(self) -> str:
        return self.overrides.get("as_of") or self.facts.get("as_of") or "unknown"

    @property
    def age_days(self) -> int | None:
        try:
            return (date.today() - datetime.fromisoformat(self.as_of).date()).days
        except (ValueError, TypeError):
            return None

    @property
    def stale(self) -> bool:
        age = self.age_days
        return age is None or age > STALENESS_DAYS

    @property
    def customer_verified(self) -> bool:
        """True when the caller supplied their own facts rather than relying on the seed."""
        return bool(self.overrides.get("criteria")) or bool(self.overrides.get("verified"))

    def criteria(self) -> dict[str, str]:
        merged = dict(self.facts.get("criteria") or {})
        merged.update(self.overrides.get("criteria") or {})
        return merged

    def get(self, key: str, default: Any = None) -> Any:
        if key in self.overrides:
            return self.overrides[key]
        return self.facts.get(key, default)


def lookup(provider: str, overrides: dict[str, Any] | None = None) -> ProviderEntry:
    """Find a provider, or return an all-unknown entry for one we do not seed.

    An unknown provider is not an error: the correct output is an assessment
    dominated by `unknown`, which scores badly and tells the customer exactly
    which questions to send the vendor. Refusing to assess would tell them nothing.
    """
    key = (provider or "").strip().lower().replace(" ", "_").replace("-", "_")
    facts = PROVIDERS.get(key)
    if facts is None:
        facts = {"display_name": provider, "as_of": None, "regions": [],
                 "source": "not in the seed registry — every criterion is unknown",
                 "criteria": {}}
    return ProviderEntry(key=key, facts=facts, overrides=overrides or {})


def known_providers() -> list[str]:
    return sorted(PROVIDERS)
