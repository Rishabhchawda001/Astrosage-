"""Plugin Registry — Central registry for all loaded plugins."""
from __future__ import annotations

from core.plugin.base import Plugin, PluginMetadata


class PluginRegistry:
    """Central registry for plugin lookup and capability queries."""

    def __init__(self):
        self._plugins: dict[str, Plugin] = {}
        self._metadata: dict[str, PluginMetadata] = {}

    def register(self, plugin: Plugin) -> None:
        meta = plugin.metadata()
        self._plugins[meta.name] = plugin
        self._metadata[meta.name] = meta

    def unregister(self, name: str) -> None:
        self._plugins.pop(name, None)
        self._metadata.pop(name, None)

    def get(self, name: str) -> Plugin | None:
        return self._plugins.get(name)

    def get_metadata(self, name: str) -> PluginMetadata | None:
        return self._metadata.get(name)

    def list_plugins(self) -> list[PluginMetadata]:
        return list(self._metadata.values())

    def list_by_capability(self, capability: str) -> list[Plugin]:
        return [
            p for name, p in self._plugins.items()
            if capability in p.capabilities()
        ]

    def list_by_category(self, category: str) -> list[Plugin]:
        return [
            p for name, p in self._plugins.items()
            if self._metadata[name].category == category
        ]

    @property
    def count(self) -> int:
        return len(self._plugins)

    def summary(self) -> dict:
        categories = {}
        for meta in self._metadata.values():
            cat = meta.category or "uncategorized"
            categories[cat] = categories.get(cat, 0) + 1
        return {"total": self.count, "by_category": categories}
