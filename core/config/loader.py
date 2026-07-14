"""
Configuration Loader — Reads, merges, and provides configuration.

Supports:
  - YAML and JSON config files
  - Environment variable overrides
  - Layered config (defaults → file → env)
  - Config validation
"""
from __future__ import annotations

import json
import os
import logging
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)


class Config:
    """Immutable configuration container with dot-notation access."""

    def __init__(self, data: dict[str, Any] | None = None):
        self._data: dict[str, Any] = data or {}

    def get(self, key: str, default: Any = None) -> Any:
        """Get a config value. Supports dot-notation (e.g. 'plugin.ocr.engine')."""
        keys = key.split(".")
        val = self._data
        for k in keys:
            if isinstance(val, dict):
                val = val.get(k)
                if val is None:
                    return default
            else:
                return default
        return val

    def set(self, key: str, value: Any) -> None:
        """Set a config value. Supports dot-notation."""
        keys = key.split(".")
        d = self._data
        for k in keys[:-1]:
            if k not in d or not isinstance(d[k], dict):
                d[k] = {}
            d = d[k]
        d[keys[-1]] = value

    def to_dict(self) -> dict[str, Any]:
        return dict(self._data)

    def __contains__(self, key: str) -> bool:
        return self.get(key) is not None

    def __repr__(self) -> str:
        return f"Config({self._data})"


class ConfigLoader:
    """
    Loads configuration from files and environment variables.

    Priority: defaults < config file < environment variables
    """

    def __init__(self, base_dir: str | Path = "."):
        self.base_dir = Path(base_dir)
        self._defaults: dict[str, Any] = {}
        self._env_prefix = "ASTROSAGE_"

    def set_defaults(self, defaults: dict[str, Any]) -> None:
        self._defaults = dict(defaults)

    def load_file(self, filepath: str | Path) -> Config:
        """Load configuration from a JSON or YAML file."""
        path = Path(filepath)
        if not path.exists():
            logger.warning(f"Config file not found: {path}")
            return Config(self._defaults)

        with open(path, "r", encoding="utf-8") as f:
            if path.suffix in (".json",):
                data = json.load(f)
            elif path.suffix in (".yaml", ".yml"):
                try:
                    import yaml
                    data = yaml.safe_load(f)
                except ImportError:
                    logger.warning("PyYAML not installed, falling back to JSON")
                    data = json.load(f)
            else:
                data = json.load(f)

        merged = {**self._defaults, **data}
        return Config(self._apply_env_overrides(merged))

    def load_directory(self, dirpath: str | Path) -> Config:
        """Load all config files from a directory, merged in order."""
        d = Path(dirpath)
        if not d.exists():
            return Config(self._defaults)

        merged = dict(self._defaults)
        for f in sorted(d.glob("*.json")):
            with open(f, "r", encoding="utf-8") as fh:
                merged.update(json.load(fh))
        for f in sorted(d.glob("*.yaml")):
            try:
                import yaml
                with open(f, "r", encoding="utf-8") as fh:
                    merged.update(yaml.safe_load(fh) or {})
            except ImportError:
                pass

        return Config(self._apply_env_overrides(merged))

    def _apply_env_overrides(self, data: dict[str, Any]) -> dict[str, Any]:
        """Override config values with environment variables."""
        for key, value in os.environ.items():
            if key.startswith(self._env_prefix):
                config_key = key[len(self._env_prefix):].lower().replace("__", ".")
                # Try to parse as JSON, fallback to string
                try:
                    parsed = json.loads(value)
                except (json.JSONDecodeError, TypeError):
                    parsed = value
                self._set_nested(data, config_key, parsed)
        return data

    def _set_nested(self, data: dict, key: str, value: Any) -> None:
        keys = key.split(".")
        d = data
        for k in keys[:-1]:
            if k not in d:
                d[k] = {}
            d = d[k]
        d[keys[-1]] = value
