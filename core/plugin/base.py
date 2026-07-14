"""
Plugin Base — ABC interface every AstroSage plugin must implement.

Lifecycle: discover → validate → initialize → ready → shutdown
"""
from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import Enum
from typing import Any


class PluginState(str, Enum):
    DISCOVERED = "discovered"
    VALIDATED = "validated"
    INITIALIZING = "initializing"
    READY = "ready"
    ERROR = "error"
    DISABLED = "disabled"
    SHUTDOWN = "shutdown"


@dataclass
class PluginMetadata:
    """Static metadata about a plugin. No runtime state."""
    name: str
    version: str
    description: str = ""
    author: str = ""
    dependencies: list[str] = field(default_factory=list)
    capabilities: list[str] = field(default_factory=list)
    category: str = ""  # ocr, parser, embedding, etc.
    tags: list[str] = field(default_factory=list)
    min_python: str = "3.11"
    config_schema: dict = field(default_factory=dict)


class Plugin(ABC):
    """
    Abstract base class for all AstroSage plugins.

    Every plugin implements this interface.
    Plugins are independently testable and replaceable.
    """

    @abstractmethod
    def metadata(self) -> PluginMetadata:
        """Return plugin metadata."""
        ...

    @abstractmethod
    def initialize(self, config: dict[str, Any] | None = None) -> None:
        """Initialize the plugin. Called once after discovery."""
        ...

    @abstractmethod
    def health(self) -> dict[str, Any]:
        """Return health status. Must return at least {"status": "ok"}."""
        ...

    @abstractmethod
    def shutdown(self) -> None:
        """Clean shutdown. Release resources."""
        ...

    def capabilities(self) -> list[str]:
        """Return list of capability strings. Default: empty."""
        return self.metadata().capabilities

    def validate_config(self, config: dict[str, Any]) -> list[str]:
        """Validate configuration. Return list of errors (empty = valid)."""
        return []

    @property
    def state(self) -> PluginState:
        return getattr(self, "_state", PluginState.DISCOVERED)

    @state.setter
    def state(self, value: PluginState):
        self._state = value
