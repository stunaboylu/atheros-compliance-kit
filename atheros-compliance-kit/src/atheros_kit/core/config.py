"""Layered configuration.

Precedence, lowest to highest: built-in defaults → `atheros.yml`
(or `[tool.atheros]` in pyproject.toml) → `ATHEROS_*` environment variables →
explicit keyword arguments at the call site.

YAML is an optional extra. Without it the file is still read if it is JSON, and
a YAML file present-but-unreadable produces a named error rather than being
silently ignored — configuration that is silently dropped is worse than
configuration that is absent, because the operator believes it applied.
"""
from __future__ import annotations

import json
import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from .errors import ConfigError

_DEFAULTS: dict[str, Any] = {
    "audit_file": ".atheros/audit_trail.jsonl",
    "report_dir": ".atheros/reports",
    "locale": "en",
    "mode": "enterprise",           # fast | mvp | enterprise
    "redact_values_in_reports": True,
    "regulation_version": None,     # None = whatever the shipped vocabulary declares
    "fail_on": {                    # CI gate thresholds
        "fairness_score_below": 70,
        "quality_score_below": 70,
        "vendor_score_below": 60,
        "drift_verdict_in": ["shifted"],
        "risk_tier_in": ["unacceptable"],
        "guard_blocks_above": 0,
        "residency_verdict_in": ["non_compliant"],
        "chain_violation": True,
    },
}

_CONFIG_FILENAMES = ("atheros.yml", "atheros.yaml", "atheros.json")


def _load_yaml(text: str, path: Path) -> dict[str, Any]:
    try:
        import yaml  # type: ignore
    except ImportError:
        # A JSON document is valid YAML, so try that before giving up: it lets a
        # team use the config file without taking the yaml extra.
        try:
            return json.loads(text)
        except json.JSONDecodeError:
            raise ConfigError(
                f"{path} looks like YAML but PyYAML is not installed. Either install it "
                f"(pip install 'atheros-compliance-kit[yaml]') or write the file as JSON. "
                f"Refusing to ignore a config file that was clearly meant to apply."
            ) from None
    try:
        return yaml.safe_load(text) or {}
    except Exception as exc:  # yaml.YAMLError, but the extra may be absent at type time
        raise ConfigError(f"{path} is not valid YAML: {exc}") from exc


def _coerce(raw: str) -> Any:
    """Environment values are strings; config values are typed."""
    low = raw.strip().lower()
    if low in ("true", "yes", "on"):
        return True
    if low in ("false", "no", "off"):
        return False
    if low in ("none", "null", ""):
        return None
    try:
        return int(raw)
    except ValueError:
        pass
    try:
        return float(raw)
    except ValueError:
        pass
    if raw.strip().startswith(("{", "[")):
        try:
            return json.loads(raw)
        except json.JSONDecodeError:
            return raw
    return raw


def _deep_merge(base: dict[str, Any], over: dict[str, Any]) -> dict[str, Any]:
    out = dict(base)
    for k, v in over.items():
        if isinstance(v, dict) and isinstance(out.get(k), dict):
            out[k] = _deep_merge(out[k], v)
        else:
            out[k] = v
    return out


def find_config_file(start: Path | None = None) -> Path | None:
    """Nearest config file walking up from `start` (default: cwd) to the filesystem root."""
    cur = (start or Path.cwd()).resolve()
    for directory in (cur, *cur.parents):
        for name in _CONFIG_FILENAMES:
            candidate = directory / name
            if candidate.is_file():
                return candidate
        pyproject = directory / "pyproject.toml"
        if pyproject.is_file() and "[tool.atheros]" in pyproject.read_text(encoding="utf-8"):
            return pyproject
    return None


def _from_pyproject(path: Path) -> dict[str, Any]:
    try:
        import tomllib  # py3.11+
    except ImportError:  # pragma: no cover - py3.10
        try:
            import tomli as tomllib  # type: ignore
        except ImportError:
            raise ConfigError(
                f"{path} carries [tool.atheros] but no TOML reader is available on "
                f"Python 3.10. Install `tomli`, or move the settings to atheros.yml."
            ) from None
    return tomllib.loads(path.read_text(encoding="utf-8")).get("tool", {}).get("atheros", {})


@dataclass
class Config:
    values: dict[str, Any] = field(default_factory=lambda: dict(_DEFAULTS))
    source: str = "defaults"

    @classmethod
    def load(cls, path: str | Path | None = None, **overrides: Any) -> Config:
        values = dict(_DEFAULTS)
        sources = ["defaults"]

        cfg_path = Path(path) if path else find_config_file()
        if cfg_path and cfg_path.is_file():
            if cfg_path.name == "pyproject.toml":
                file_values = _from_pyproject(cfg_path)
            else:
                text = cfg_path.read_text(encoding="utf-8")
                file_values = json.loads(text) if cfg_path.suffix == ".json" else _load_yaml(text, cfg_path)
            values = _deep_merge(values, file_values or {})
            sources.append(str(cfg_path))

        env_values: dict[str, Any] = {}
        for key, raw in os.environ.items():
            if not key.startswith("ATHEROS_") or key.startswith(("ATHEROS_MODEL__", "ATHEROS_TIER__")):
                continue  # model overrides belong to core.models, not here
            env_values[key[len("ATHEROS_"):].lower()] = _coerce(raw)
        if env_values:
            values = _deep_merge(values, env_values)
            sources.append("env")

        if overrides:
            values = _deep_merge(values, overrides)
            sources.append("args")

        return cls(values=values, source=" → ".join(sources))

    def get(self, key: str, default: Any = None) -> Any:
        """Dotted lookup: `cfg.get("fail_on.drift_verdict_in", [])`."""
        node: Any = self.values
        for part in key.split("."):
            if not isinstance(node, dict) or part not in node:
                return default
            node = node[part]
        return node

    def __getitem__(self, key: str) -> Any:
        return self.get(key)


_ACTIVE: Config | None = None


def active_config() -> Config:
    global _ACTIVE
    if _ACTIVE is None:
        _ACTIVE = Config.load()
    return _ACTIVE


def set_active_config(cfg: Config) -> None:
    global _ACTIVE
    _ACTIVE = cfg
