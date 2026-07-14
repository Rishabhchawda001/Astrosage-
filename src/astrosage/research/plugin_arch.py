
"""
Plugin Architecture — every integration is a plugin.

Plugins are independently replaceable, testable, and discoverable.
"""
from __future__ import annotations
import importlib
import json
from abc import ABC, abstractmethod
from dataclasses import dataclass, field, asdict
from pathlib import Path
from typing import Any, Optional

@dataclass
class PluginManifest:
    name: str
    version: str
    category: str
    description: str = ""
    author: str = "AstroSage"
    dependencies: list[str] = field(default_factory=list)
    enabled: bool = True
    config: dict = field(default_factory=dict)

class Plugin(ABC):
    def __init__(self, manifest: PluginManifest):
        self.manifest = manifest

    @abstractmethod
    def initialize(self, config: dict = None) -> bool:
        pass

    @abstractmethod
    def execute(self, operation: str, **kwargs) -> Any:
        pass

    @abstractmethod
    def health_check(self) -> dict:
        pass

    def shutdown(self):
        pass

class PluginRegistry:
    def __init__(self):
        self._plugins: dict[str, Plugin] = {}
        self._manifests: dict[str, PluginManifest] = {}

    def register(self, plugin: Plugin) -> bool:
        self._plugins[plugin.manifest.name] = plugin
        self._manifests[plugin.manifest.name] = plugin.manifest
        return True

    def get(self, name: str) -> Optional[Plugin]:
        return self._plugins.get(name)

    def list_plugins(self) -> list[dict]:
        return [asdict(m) for m in self._manifests.values()]

    def list_by_category(self, category: str) -> list[str]:
        return [name for name, m in self._manifests.items() if m.category == category]

    def health_all(self) -> dict:
        results = {}
        for name, plugin in self._plugins.items():
            try:
                results[name] = plugin.health_check()
            except Exception as e:
                results[name] = {"status": "error", "error": str(e)}
        return results

    def save_registry(self, path: Path):
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(self.list_plugins(), indent=2))
