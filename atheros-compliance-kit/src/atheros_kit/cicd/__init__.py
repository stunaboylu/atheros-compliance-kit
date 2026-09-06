"""CI/CD integration — turn an assessment into an enforced control."""
from .gate import CheckOutcome, EXIT_ERROR, EXIT_FAIL, EXIT_OK, GateResult, run

__all__ = ["run", "GateResult", "CheckOutcome", "EXIT_OK", "EXIT_FAIL", "EXIT_ERROR"]
