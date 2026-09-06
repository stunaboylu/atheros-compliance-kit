"""Cross-cutting foundations. Imports nothing from the four capability modules."""
from .audit import AuditTrail, default_trail, new_session_id, set_default_trail
from .config import Config, active_config, set_active_config
from .errors import (
    AtherosError,
    BudgetExceeded,
    ConfigError,
    GuardBlocked,
    LedgerViolation,
    MissingDependencyError,
)
from .findings import (
    Action,
    Coverage,
    Finding,
    Method,
    Score,
    Severity,
    harmonic_mean,
    score_from_diff,
    score_from_ratio,
    worst,
)
from .models import ModelChoice, ModelRef, floating_models, resolve, warn_on_floating
from .report import Report

__all__ = [
    "AuditTrail", "default_trail", "new_session_id", "set_default_trail",
    "Config", "active_config", "set_active_config",
    "AtherosError", "BudgetExceeded", "ConfigError", "GuardBlocked",
    "LedgerViolation", "MissingDependencyError",
    "Action", "Coverage", "Finding", "Method", "Score", "Severity",
    "harmonic_mean", "score_from_diff", "score_from_ratio", "worst",
    "ModelChoice", "ModelRef", "floating_models", "resolve", "warn_on_floating",
    "Report",
]
