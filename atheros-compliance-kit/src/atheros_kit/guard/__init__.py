"""Module 2 — third-party black-box API guardrails and wrapper.

    from atheros_kit.guard import GuardedClient, GuardPolicy, CustomEntity

    client = GuardedClient(call=my_llm_call, policy=GuardPolicy.strict())
    result = client.invoke("Summarise the case for ali@example.com")
    result.text          # safe to use
    result.degraded      # True if a fallback ran — never silent
    client.summary()     # token governance + what was masked, values excluded
"""
from .fallback import FallbackOutcome, Trigger, check_output, is_refusal
from .injection import ScanResult, Signature, scan, scan_documents
from .ledger import GuardLedger, InvocationRecord, TokenUsage, estimate_tokens
from .pii import Anonymizer, CustomEntity, MaskResult, detect_categories
from .policy import GuardPolicy
from .wrapper import GuardedClient, GuardResult

__all__ = [
    "GuardedClient", "GuardResult", "GuardPolicy", "GuardLedger",
    "Anonymizer", "CustomEntity", "MaskResult", "detect_categories",
    "scan", "scan_documents", "ScanResult", "Signature",
    "check_output", "is_refusal", "Trigger", "FallbackOutcome",
    "InvocationRecord", "TokenUsage", "estimate_tokens",
]
