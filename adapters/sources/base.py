"""
Source Adapter — ABC interface for external knowledge sources.

Every source connector must implement this interface.
Connectors are independently replaceable.
"""
from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any, Optional


@dataclass
class SourceConfig:
    """Configuration for a source connector."""
    name: str = ""
    base_url: str = ""
    api_key: str = ""
    rate_limit: int = 60
    timeout: int = 30
    offline_mode: bool = False
    cache_dir: str = ""
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class SourceResult:
    """Result from a source query."""
    success: bool = False
    items: list[dict[str, Any]] = field(default_factory=list)
    total: int = 0
    source_name: str = ""
    query: str = ""
    error: str = ""
    metadata: dict[str, Any] = field(default_factory=dict)


class SourceAdapter(ABC):
    """Abstract base class for all source connectors."""

    @abstractmethod
    def name(self) -> str:
        """Return the name of this source."""
        ...

    @abstractmethod
    def configure(self, config: SourceConfig) -> None:
        """Configure the adapter."""
        ...

    @abstractmethod
    def health(self) -> dict[str, Any]:
        """Return health status."""
        ...

    @abstractmethod
    def search(self, query: str, max_results: int = 10) -> SourceResult:
        """Search this source for content."""
        ...

    @abstractmethod
    def fetch(self, item_id: str) -> SourceResult:
        """Fetch a specific item by ID."""
        ...

    def is_available(self) -> bool:
        """Check if source is available."""
        return True
