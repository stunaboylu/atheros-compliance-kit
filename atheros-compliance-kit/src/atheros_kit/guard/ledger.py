"""Secure invocation logging and token governance.

Every call through `GuardedClient` lands here and, from here, on the hash chain.
What is recorded: who, when, which model, how many tokens, how long, which
entity CLASSES were masked, which signatures fired, whether it degraded. What is
never recorded: prompt text, response text, or any detected value.

That exclusion is the product's core promise and so it is enforced by
construction — the ledger's methods do not accept the text in the first place,
so no future caller can pass it "just this once for debugging".
"""
from __future__ import annotations

import time
from dataclasses import dataclass
from datetime import date
from typing import Any

from ..core.audit import AuditTrail, default_trail, new_session_id
from ..core.errors import BudgetExceeded


@dataclass
class TokenUsage:
    prompt_tokens: int = 0
    completion_tokens: int = 0

    @property
    def total(self) -> int:
        return self.prompt_tokens + self.completion_tokens

    def __add__(self, other: TokenUsage) -> TokenUsage:
        return TokenUsage(
            self.prompt_tokens + other.prompt_tokens,
            self.completion_tokens + other.completion_tokens,
        )


def estimate_tokens(text: str) -> int:
    """Character-based estimate used when the provider reports no usage.

    ~4 characters per token is wrong for every specific text and adequate for a
    budget. It is marked `estimated` on the record so nobody bills against it.
    """
    return max(1, len(text or "") // 4)


@dataclass
class InvocationRecord:
    session_id: str
    call_index: int
    model: str
    usage: TokenUsage
    usage_estimated: bool
    latency_ms: float
    input_action: str
    output_action: str
    masked_entities: dict[str, int]
    signatures: list[str]
    degraded: bool
    fallback_reason: str | None
    #: WHICH path actually produced the answer: primary | retry | secondary | static.
    #:
    #: The trigger says why a fallback happened; this says what answered. They are
    #: different questions and only one of them was being recorded. "degraded,
    #: provider_error" could mean a second model answered or a canned string did —
    #: for a compliance record those are not the same event, and the product's
    #: claim to answer "which model produced this" depends on the distinction.
    answered_by: str = "primary"
    attempts: int = 1
    error: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "call_index": self.call_index,
            "model": self.model,
            "tokens": {
                "prompt": self.usage.prompt_tokens,
                "completion": self.usage.completion_tokens,
                "total": self.usage.total,
                "estimated": self.usage_estimated,
            },
            "latency_ms": round(self.latency_ms, 2),
            "input_action": self.input_action,
            "output_action": self.output_action,
            "masked_entities": self.masked_entities,
            "signatures": self.signatures,
            "degraded": self.degraded,
            "fallback_reason": self.fallback_reason,
            "answered_by": self.answered_by,
            "attempts": self.attempts,
            "error": self.error,
        }


class GuardLedger:
    """Per-session accounting plus the append to the shared hash chain."""

    #: Daily totals are process-wide by design: a budget expressed per day that
    #: resets whenever a session object is constructed is not a budget.
    _daily: dict[str, int] = {}

    def __init__(self, session_id: str | None = None, trail: AuditTrail | None = None):
        self.session_id = session_id or new_session_id()
        self.trail = trail or default_trail()
        self.records: list[InvocationRecord] = []
        self.started_at = time.time()

    # ── accounting ───────────────────────────────────────────────────────────
    @property
    def usage(self) -> TokenUsage:
        total = TokenUsage()
        for r in self.records:
            total = total + r.usage
        return total

    @property
    def call_count(self) -> int:
        return len(self.records)

    @classmethod
    def daily_total(cls, day: str | None = None) -> int:
        return cls._daily.get(day or date.today().isoformat(), 0)

    @classmethod
    def reset_daily(cls) -> None:
        cls._daily.clear()

    def _charge_daily(self, tokens: int) -> None:
        key = date.today().isoformat()
        self._daily[key] = self._daily.get(key, 0) + tokens

    def check_budget(self, policy, projected_tokens: int = 0) -> str | None:
        """Return the breached budget's name, or None.

        Checked BEFORE the call, against a projection, because a budget enforced
        after the tokens are spent is a report, not a control.
        """
        if policy.max_calls_per_session is not None and self.call_count >= policy.max_calls_per_session:
            return "max_calls_per_session"
        if (policy.max_tokens_per_session is not None
                and self.usage.total + projected_tokens > policy.max_tokens_per_session):
            return "max_tokens_per_session"
        if (policy.max_tokens_per_day is not None
                and self.daily_total() + projected_tokens > policy.max_tokens_per_day):
            return "max_tokens_per_day"
        return None

    def enforce_budget(self, policy, projected_tokens: int = 0) -> str | None:
        breach = self.check_budget(policy, projected_tokens)
        if breach and policy.on_budget_exceeded == "raise":
            raise BudgetExceeded(
                f"{breach} exhausted for session {self.session_id} "
                f"(used {self.usage.total} tokens over {self.call_count} calls)"
            )
        return breach

    # ── recording ────────────────────────────────────────────────────────────
    def record(self, rec: InvocationRecord, *, log: bool = True) -> dict[str, Any] | None:
        self.records.append(rec)
        self._charge_daily(rec.usage.total)
        if not log:
            return None
        return self.trail.log(
            "guard", "llm_invocation", rec.to_dict(), session_id=self.session_id
        )

    def summary(self) -> dict[str, Any]:
        masked: dict[str, int] = {}
        signatures: set[str] = set()
        answered: dict[str, int] = {}
        for r in self.records:
            for k, v in r.masked_entities.items():
                masked[k] = masked.get(k, 0) + v
            signatures.update(r.signatures)
            answered[r.answered_by] = answered.get(r.answered_by, 0) + 1
        return {
            "session_id": self.session_id,
            "calls": self.call_count,
            "tokens": self.usage.total,
            "degraded_calls": sum(1 for r in self.records if r.degraded),
            "answered_by": dict(sorted(answered.items())),
            "retries": sum(r.attempts - 1 for r in self.records),
            "blocked_calls": sum(1 for r in self.records if r.input_action == "block"),
            "masked_entities": dict(sorted(masked.items())),
            "signatures_triggered": sorted(signatures),
            "duration_s": round(time.time() - self.started_at, 2),
        }
