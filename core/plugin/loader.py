"""
Plugin Loader — Auto-discovers, validates, and loads plugins from directories.

Supports:
  - Directory scanning for plugin modules
  - Dynamic import
  - Plugin validation
  - Dependency resolution
  - Lifecycle management
"""
from __future__ import annotations

import importlib
import logging
import pkgutil
from pathlib import Path
from typing import Any

from core.plugin.base import Plugin, PluginMetadata, PluginState

logger = logging.getLogger(__name__)


class PluginLoadError(Exception):
    """Raised when a plugin fails to load."""


class PluginLoader:
    """
    Discovers and loads plugins from directories.

    Scans a directory for Python modules containing Plugin subclasses.
    """

    def __init__(self, plugin_dirs: list[str | Path] | None = None):
        self.plugin_dirs = [Path(d) for d in (plugin_dirs or [])]
        self._discovered: dict[str, PluginMetadata] = {}
        self._loaded: dict[str, Plugin] = {}

    def discover(self) -> dict[str, PluginMetadata]:
        """Scan all plugin directories and discover plugin classes."""
        for plugin_dir in self.plugin_dirs:
            if not plugin_dir.exists():
                continue
            self._scan_directory(plugin_dir)
        return dict(self._discovered)

    def _scan_directory(self, directory: Path):
        """Recursively scan a directory for plugin modules."""
        for path in directory.rglob("*.py"):
            if path.name.startswith("_") or path.name == "base.py":
                continue
            try:
                self._try_load_module(path, directory)
            except Exception as e:
                logger.warning(f"Failed to scan {path}: {e}")

    def _try_load_module(self, module_path: Path, base_dir: Path):
        """Try to load a module and extract Plugin subclasses."""
        rel = module_path.relative_to(base_dir)
        module_name = str(rel.with_suffix("")).replace("/", ".").replace("\\", ".")
        if not module_name.startswith("core.plugin"):
            full_name = f"plugins.{module_name}"
        else:
            full_name = module_name

        try:
            mod = importlib.import_module(full_name)
        except ImportError:
            # Try alternate import path
            try:
                full_name = f"plugins.{rel.parent.name}.{module_path.stem}"
                mod = importlib.import_module(full_name)
            except ImportError as e:
                logger.debug(f"Cannot import {full_name}: {e}")
                return

        for attr_name in dir(mod):
            attr = getattr(mod, attr_name)
            if (isinstance(attr, type)
                    and issubclass(attr, Plugin)
                    and attr is not Plugin):
                try:
                    instance = attr()
                    meta = instance.metadata()
                    self._discovered[meta.name] = meta
                    self._loaded[meta.name] = instance
                    logger.info(f"Discovered plugin: {meta.name} v{meta.version}")
                except Exception as e:
                    logger.warning(f"Failed to instantiate {attr_name}: {e}")

    def load_plugin(self, name: str, config: dict[str, Any] | None = None) -> Plugin:
        """Initialize and return a named plugin."""
        if name not in self._loaded:
            raise PluginLoadError(f"Plugin '{name}' not found")
        plugin = self._loaded[name]
        try:
            plugin.state = PluginState.INITIALIZING
            plugin.initialize(config)
            plugin.state = PluginState.READY
            return plugin
        except Exception as e:
            plugin.state = PluginState.ERROR
            raise PluginLoadError(f"Plugin '{name}' failed to initialize: {e}")

    def load_all(self, configs: dict[str, dict[str, Any]] | None = None) -> dict[str, Plugin]:
        """Initialize all discovered plugins."""
        configs = configs or {}
        loaded = {}
        for name, meta in self._discovered.items():
            # Skip if dependencies not met
            missing = [d for d in meta.dependencies if d not in self._loaded]
            if missing:
                logger.warning(f"Plugin '{name}' missing dependencies: {missing}")
                continue
            try:
                loaded[name] = self.load_plugin(name, configs.get(name))
            except PluginLoadError as e:
                logger.error(str(e))
        return loaded

    def get_plugin(self, name: str) -> Plugin | None:
        return self._loaded.get(name)

    @property
    def discovered(self) -> dict[str, PluginMetadata]:
        return dict(self._discovered)

    @property
    def loaded(self) -> dict[str, Plugin]:
        return dict(self._loaded)

    def dependency_graph(self) -> dict[str, list[str]]:
        """Return dependency graph for all discovered plugins."""
        return {name: meta.dependencies for name, meta in self._discovered.items()}
