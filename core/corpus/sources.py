"""
Source Discovery Framework — Plugin-based architecture for external knowledge sources.

Adapters for: Archive.org, Open Library, National Digital Library,
University repos, GitHub repos, academic repos, Crossref, OpenAlex,
Internet Archive metadata, local mirrors, future connectors.
"""
from __future__ import annotations

import uuid
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Optional


class SourceCategory(str, Enum):
    DIGITAL_LIBRARY = "digital_library"
    ACADEMIC = "academic"
    GOVERNMENT = "government"
    UNIVERSITY = "university"
    REPOSITORY = "repository"
    METADATA = "metadata"
    LOCAL = "local"
    MIRROR = "mirror"
    FUTURE = "future"


class SourceStatus(str, Enum):
    ACTIVE = "active"
    INACTIVE = "inactive"
    RATE_LIMITED = "rate_limited"
    ERROR = "error"
    UNTESTED = "untested"


@dataclass
class SourceRecord:
    """Registry entry for a knowledge source."""
    source_id: str = ""
    name: str = ""
    category: SourceCategory = SourceCategory.DIGITAL_LIBRARY
    base_url: str = ""
    api_url: str = ""
    trust_score: float = 0.0
    language_support: list[str] = field(default_factory=list)
    document_types: list[str] = field(default_factory=list)
    license: str = ""
    version: str = ""
    status: SourceStatus = SourceStatus.UNTESTED
    last_validated: str = ""
    metadata: dict[str, Any] = field(default_factory=dict)
    registered_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

    def __post_init__(self):
        if not self.source_id:
            self.source_id = f"SR-{uuid.uuid4().hex[:12]}"


class SourceConnector(ABC):
    """Abstract base for source connectors."""

    @abstractmethod
    def name(self) -> str: ...

    @abstractmethod
    def search(self, query: str, max_results: int = 10) -> list[dict]: ...

    @abstractmethod
    def fetch(self, item_id: str) -> dict: ...

    @abstractmethod
    def health(self) -> dict: ...


class SourceRegistry:
    """
    Plugin-based source registry.

    Manages source records and connector plugins.
    """

    def __init__(self):
        self._sources: dict[str, SourceRecord] = {}
        self._connectors: dict[str, SourceConnector] = {}

    def register_source(self, source: SourceRecord) -> str:
        self._sources[source.source_id] = source
        return source.source_id

    def register_connector(self, source_id: str, connector: SourceConnector) -> None:
        self._connectors[source_id] = connector

    def get_source(self, source_id: str) -> Optional[SourceRecord]:
        return self._sources.get(source_id)

    def get_connector(self, source_id: str) -> Optional[SourceConnector]:
        return self._connectors.get(source_id)

    def get_by_category(self, category: SourceCategory) -> list[SourceRecord]:
        return [s for s in self._sources.values() if s.category == category]

    def get_active(self) -> list[SourceRecord]:
        return [s for s in self._sources.values() if s.status == SourceStatus.ACTIVE]

    def list_all(self) -> list[SourceRecord]:
        return list(self._sources.values())

    def count(self) -> int:
        return len(self._sources)

    def summary(self) -> dict:
        cat_counts: dict[str, int] = {}
        status_counts: dict[str, int] = {}
        for s in self._sources.values():
            cat_counts[s.category.value] = cat_counts.get(s.category.value, 0) + 1
            status_counts[s.status.value] = status_counts.get(s.status.value, 0) + 1
        return {"total_sources": self.count(), "by_category": cat_counts, "by_status": status_counts}
