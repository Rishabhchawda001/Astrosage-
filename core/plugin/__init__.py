"""Plugin system — ABC-based, auto-discovering, lifecycle-managed plugins."""
from core.plugin.base import Plugin, PluginMetadata, PluginState
from core.plugin.loader import PluginLoader
from core.plugin.registry import PluginRegistry

__all__ = ["Plugin", "PluginMetadata", "PluginState", "PluginLoader", "PluginRegistry"]
