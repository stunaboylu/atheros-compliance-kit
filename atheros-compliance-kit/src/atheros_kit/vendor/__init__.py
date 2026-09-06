"""Module 4 — automated vendor and third-party risk assessment.

    from atheros_kit.vendor import assess

    a = assess("openai", required_regions=["EU"],
               contract_flags={"training_optout_enabled": True,
                               "training_optout_contractual": True})
    a.score.value            # weighted 0-100; `unknown` is penalised, not skipped
    a.residency.verdict      # compliant | requires_scc | non_compliant | unknown
    a.optout.verdict         # enforced | available_not_evidenced | not_available | unknown
"""
from .assess import VendorAssessment, assess
from .criteria import CRITERIA, CRITERIA_BY_KEY, GROUPS, STATUS_WEIGHT, Criterion
from .optout import OptOutResult, enforce
from .registry import PROVIDERS, ProviderEntry, known_providers, lookup
from .residency import ResidencyResult, verify

__all__ = [
    "assess", "VendorAssessment",
    "CRITERIA", "CRITERIA_BY_KEY", "Criterion", "GROUPS", "STATUS_WEIGHT",
    "verify", "ResidencyResult", "enforce", "OptOutResult",
    "lookup", "known_providers", "ProviderEntry", "PROVIDERS",
]
