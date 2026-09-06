"""Error types. One rule: an error names the fix, not just the fault."""
from __future__ import annotations


class AtherosError(Exception):
    """Base for everything this toolkit raises."""


class ConfigError(AtherosError):
    """Configuration is missing, malformed, or self-contradictory."""


class MissingDependencyError(AtherosError):
    """An optional extra is required for this call and is not installed.

    Raised instead of ImportError so the message can carry the install command.
    A stack trace ending in `ModuleNotFoundError: chromadb` tells an engineer
    what is absent; it does not tell them which extra of ours provides it.
    """

    def __init__(self, package: str, extra: str, purpose: str):
        super().__init__(
            f"{purpose} needs the optional package '{package}'. "
            f"Install it with:  pip install 'atheros-compliance-kit[{extra}]'"
        )
        self.package, self.extra = package, extra


class GuardBlocked(AtherosError):
    """A guardrail gate blocked the call and the policy says raise.

    Carries the gate result so a caller can log precisely what tripped without
    re-running the detectors.
    """

    def __init__(self, message: str, result=None):
        super().__init__(message)
        self.result = result


class BudgetExceeded(AtherosError):
    """A token or cost budget was exhausted and the policy says raise."""


class LedgerViolation(AtherosError):
    """The audit chain does not verify. Never raised implicitly — only by callers
    that asked for `verify_chain(raise_on_violation=True)`, because deciding what
    a broken chain means is the operator's call, not the library's."""
