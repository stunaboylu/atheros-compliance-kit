"""Guard policy — what the wrapper does, declared rather than coded.

Three presets, because the three real deployments are: "I want visibility"
(observe), "I want the obvious harms stopped" (standard), and "nothing
identifiable leaves this process" (strict). Anything else is a field edit.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Callable, Literal

from .pii import CustomEntity

OnBudget = Literal["warn", "fallback", "raise"]
OnBlock = Literal["fallback", "raise", "pass_through"]


@dataclass
class GuardPolicy:
    # ── masking ──────────────────────────────────────────────────────────────
    mask_pii: bool = True
    reversible: bool = True
    categories: list[str] | None = None            # None = every built-in detector
    custom_entities: list[CustomEntity] = field(default_factory=list)
    #: Block outright if a secret shape (API key, JWT, AWS key) is in the prompt.
    #: Masking a live credential still means it was in a payload that a human can
    #: read in a log somewhere upstream; the right answer is to stop the call.
    block_on_secret: bool = True

    # ── injection firewall ───────────────────────────────────────────────────
    scan_injection: bool = True
    scan_encoded: bool = True
    scan_documents: bool = True
    on_block: OnBlock = "raise"

    # ── output side ──────────────────────────────────────────────────────────
    unmask_response: bool = True
    scan_output: bool = True
    #: Refusals are not failures, but they are not answers either. Detecting them
    #: is what lets `fallback` return something useful instead of surfacing the
    #: provider's apology as if it were the result.
    detect_refusal: bool = True
    #: Model output claiming certainty the evidence cannot support. Inherited
    #: from an earlier in-house assurance-overreach check: in a compliance product,
    #: "fully compliant" from an LLM is the single most dangerous sentence.
    detect_overclaim: bool = True

    # ── budgets ──────────────────────────────────────────────────────────────
    max_tokens_per_session: int | None = None
    max_tokens_per_day: int | None = None
    max_calls_per_session: int | None = None
    on_budget_exceeded: OnBudget = "raise"

    # ── fallback ─────────────────────────────────────────────────────────────
    retries: int = 2
    retry_backoff_seconds: float = 0.5
    static_fallback: str | None = None
    secondary_call: Callable | None = None

    # ── ledger ───────────────────────────────────────────────────────────────
    log_to_ledger: bool = True

    @classmethod
    def observe(cls) -> "GuardPolicy":
        """Measure, never interfere. For the first week in a live system.

        Nothing is blocked and nothing is masked — but every detection is on the
        ledger, so the team can see what a strict policy WOULD have stopped
        before it stops it in production.
        """
        return cls(
            mask_pii=False, block_on_secret=False, on_block="pass_through",
            unmask_response=False, retries=0,
        )

    @classmethod
    def standard(cls) -> "GuardPolicy":
        """Mask, block the critical signatures, fall back rather than fail."""
        return cls(on_block="fallback", static_fallback=DEFAULT_FALLBACK_TEXT)

    @classmethod
    def strict(cls) -> "GuardPolicy":
        """Maximum isolation: irreversible masking, raise on anything suspicious.

        `reversible=False` drops the vault, so masked values are unrecoverable by
        construction rather than by policy — the property a regulated deployment
        needs to be able to assert rather than promise.
        """
        return cls(
            reversible=False, unmask_response=False, on_block="raise",
            on_budget_exceeded="raise", retries=1,
        )


DEFAULT_FALLBACK_TEXT = (
    "This request could not be completed safely and was stopped by a policy control. "
    "No answer is being provided rather than an unverified one. "
    "Please contact your administrator with the session id if this was unexpected."
)
