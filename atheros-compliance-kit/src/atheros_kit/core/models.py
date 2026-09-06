"""Model-tier abstraction — which model a check runs on is configuration, not code.

WHY TIERS AND NOT A MODEL PER CHECK
The cost argument is about how hard the work is, not about which check does it.
Classifying a chunk and drafting the final risk rationale are two different jobs
at two different price points; two checks doing comparable work should move
together when a better model appears. So checks name a TIER, the tier names a
provider + model, and re-pricing the whole toolkit is one edit.

PRECEDENCE, highest first:
  1. ATHEROS_MODEL__<CheckName>   one check      (e.g. "openai:gpt-5-2025-08-07")
  2. ATHEROS_TIER__<TIER>         one tier       (e.g. "gemini:models/gemini-3.5-flash")
  3. atheros-models.yaml          the file       (ATHEROS_MODELS_CONFIG to relocate)
  4. the built-in defaults below

Every resolution records whether the model name PINS a version. A floating alias
(`-latest`, `-preview`) means the log names a moving target: which model produced
a given classification cannot be established afterwards, and a re-run can
legitimately differ with no visible cause. The Kit does not refuse floating names
— the set of ids a deployment can reach is a deployment fact — it refuses to let
the drift be invisible.
"""
from __future__ import annotations

import json
import logging
import os
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any

log = logging.getLogger(__name__)

GEMINI, OPENAI, ANTHROPIC, NONE = "gemini", "openai", "anthropic", "none"

# Built-in defaults. `none` is a first-class provider: with no key configured the
# Kit runs its deterministic path and every score is marked degraded. That is the
# supported default, not a broken state.
_BUILTIN_TIERS: dict[str, dict[str, str]] = {
    # High-volume, short-answer work: lexicon matching assists, chunk labelling.
    "cheap": {"provider": NONE, "model": "deterministic"},
    # Retrieval-grounded matching over long context.
    "mid": {"provider": NONE, "model": "deterministic"},
    # Reasoning a person signs off: risk rationale, dossier prose, bias narrative.
    "strong": {"provider": NONE, "model": "deterministic"},
    # Scores the Kit's own output. Kept separate from `cheap` on purpose: moving
    # the judge changes the measurements, so it must not drift every time the
    # production tiers are re-priced.
    "judge": {"provider": NONE, "model": "deterministic"},
}

_BUILTIN_CHECKS: dict[str, dict[str, str]] = {
    "BiasNarrator": {"tier": "mid", "fallback": "cheap"},
    "DriftExplainer": {"tier": "cheap"},
    "RiskRationale": {"tier": "strong", "fallback": "mid"},
    "DossierWriter": {"tier": "strong", "fallback": "mid"},
    "InjectionJudge": {"tier": "cheap"},
    "GroundednessJudge": {"tier": "judge"},
    "VendorNarrator": {"tier": "cheap"},
    "RemediationPlanner": {"tier": "mid", "fallback": "cheap"},
}

_FLOATING_SUFFIXES = ("-latest", "-exp", "-preview", "-nightly")


def is_pinned(model: str) -> bool:
    """Whether this model name identifies one specific version, forever."""
    name = (model or "").strip().lower()
    if not name or name == "deterministic":
        return False
    if name.endswith(_FLOATING_SUFFIXES):
        return False
    # A dated build ("gpt-5-2025-08-07") or a numbered one ("...-flash-001") pins;
    # a bare family name does not. The ISO form is checked separately because a
    # date ends in two digits and would read as unpinned under the digit-run rule.
    return bool(re.search(r"\d{4}-\d{2}-\d{2}$", name) or re.search(r"\d{3,}$", name))


@dataclass(frozen=True)
class ModelRef:
    provider: str
    model: str

    @property
    def pinned(self) -> bool:
        return is_pinned(self.model)

    @property
    def available(self) -> bool:
        """Whether a key for this provider is present. `none` is always available."""
        if self.provider == NONE:
            return True
        return bool(os.environ.get({
            GEMINI: "GEMINI_API_KEY",
            OPENAI: "OPENAI_API_KEY",
            ANTHROPIC: "ANTHROPIC_API_KEY",
        }.get(self.provider, "")))

    def __str__(self) -> str:
        return f"{self.provider}:{self.model}"

    @classmethod
    def parse(cls, spec: str) -> "ModelRef":
        """`"openai:gpt-5-2025-08-07"` → ModelRef. A bare name means gemini, historically."""
        if ":" in spec:
            provider, _, model = spec.partition(":")
            return cls(provider.strip().lower(), model.strip())
        return cls(GEMINI, spec.strip())


@dataclass(frozen=True)
class ModelChoice:
    """What a check will actually run on, and what it falls back to."""

    check: str
    tier: str
    primary: ModelRef
    fallback: ModelRef | None = None

    @property
    def deterministic(self) -> bool:
        return self.primary.provider == NONE or not self.primary.available

    def to_dict(self) -> dict[str, Any]:
        return {
            "check": self.check,
            "tier": self.tier,
            "primary": str(self.primary),
            "pinned": self.primary.pinned,
            "fallback": str(self.fallback) if self.fallback else None,
            "deterministic": self.deterministic,
        }


def _load_file() -> dict[str, Any]:
    path = Path(os.environ.get("ATHEROS_MODELS_CONFIG", "atheros-models.yaml"))
    if not path.is_file():
        return {}
    text = path.read_text(encoding="utf-8")
    try:
        import yaml  # type: ignore

        return yaml.safe_load(text) or {}
    except ImportError:
        try:
            return json.loads(text)
        except json.JSONDecodeError:
            log.warning(
                "%s exists but PyYAML is not installed and it is not JSON — model "
                "assignment falls back to the built-in defaults. "
                "pip install 'atheros-compliance-kit[yaml]' to apply it.",
                path,
            )
            return {}


_FILE: dict[str, Any] | None = None


def _file_config() -> dict[str, Any]:
    global _FILE
    if _FILE is None:
        _FILE = _load_file()
    return _FILE


def reset_cache() -> None:
    """Re-read the config file. For tests and long-lived processes that rewrite it."""
    global _FILE
    _FILE = None


def tiers() -> dict[str, ModelRef]:
    merged = dict(_BUILTIN_TIERS)
    for name, spec in (_file_config().get("tiers") or {}).items():
        merged[name] = dict(spec or {})
    out: dict[str, ModelRef] = {}
    for name, spec in merged.items():
        env = os.environ.get(f"ATHEROS_TIER__{name.upper()}")
        out[name] = ModelRef.parse(env) if env else ModelRef(
            spec.get("provider", NONE), spec.get("model", "deterministic")
        )
    return out


def resolve(check: str) -> ModelChoice:
    """Resolve one check to a concrete model, applying the full precedence chain."""
    all_tiers = tiers()
    file_checks = _file_config().get("checks") or _file_config().get("agents") or {}
    spec = {**_BUILTIN_CHECKS.get(check, {}), **(file_checks.get(check) or {})}
    tier_name = spec.get("tier", "cheap")

    # 1. per-check env override wins over everything, including its tier.
    env = os.environ.get(f"ATHEROS_MODEL__{check}")
    if env:
        primary = ModelRef.parse(env)
    elif spec.get("provider") and spec.get("model"):
        # A check may name a model directly and skip the tier system entirely.
        primary = ModelRef(spec["provider"], spec["model"])
    else:
        primary = all_tiers.get(tier_name, all_tiers["cheap"])

    fb_name = spec.get("fallback")
    fallback = all_tiers.get(fb_name) if fb_name else None
    if fallback == primary:
        fallback = None  # a fallback identical to the primary is not a fallback
    return ModelChoice(check=check, tier=tier_name, primary=primary, fallback=fallback)


def floating_models() -> list[str]:
    """Configured models that pin nothing, de-duplicated, for one boot warning."""
    seen: dict[str, None] = {}
    for ref in tiers().values():
        if ref.provider != NONE and not ref.pinned:
            seen[str(ref)] = None
    for check in _BUILTIN_CHECKS:
        ref = resolve(check).primary
        if ref.provider != NONE and not ref.pinned:
            seen[str(ref)] = None
    return list(seen)


def configured_providers() -> list[str]:
    """Providers this process actually holds a key for."""
    return [p for p in (GEMINI, OPENAI, ANTHROPIC) if ModelRef(p, "x").available]


def warn_on_floating() -> None:
    """Call once at start-up. Names the drift instead of hiding it."""
    floating = floating_models()
    if floating:
        log.warning(
            "Model names that pin no version: %s. Every assessment produced on these "
            "records a moving target — 'which model produced this' cannot be answered later.",
            ", ".join(floating),
        )
