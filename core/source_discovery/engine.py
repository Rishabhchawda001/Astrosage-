"""
Global Source Discovery — Plugin-based connector framework.

Connectors for: Archive.org, Open Library, Google Books, National Digital Library,
Government archives, University repos, GitHub, Crossref, OpenAlex, Wikidata,
Internet Archive, Project Gutenberg, Publisher catalogs, Local corpus.
"""
from __future__ import annotations

import uuid
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Optional


class ConnectorType(str, Enum):
    ARCHIVE_ORG = "archive_org"
    OPEN_LIBRARY = "open_library"
    GOOGLE_BOOKS = "google_books"
    NDL = "national_digital_library"
    GOVERNMENT = "government"
    UNIVERSITY = "university"
    GITHUB = "github"
    CROSSREF = "crossref"
    OPENALEX = "openalex"
    WIKIDATA = "wikidata"
    GUTENBERG = "gutenberg"
    PUBLISHER = "publisher"
    LOCAL = "local"
    CUSTOM = "custom"


class ConnectorStatus(str, Enum):
    ACTIVE = "active"
    INACTIVE = "inactive"
    RATE_LIMITED = "rate_limited"
    ERROR = "error"
    UNTESTED = "untested"


@dataclass
class DiscoveryHit:
    """A single discovery result from a source."""
    hit_id: str = ""
    connector_type: ConnectorType = ConnectorType.CUSTOM
    title: str = ""
    author: str = ""
    language: str = ""
    year: str = ""
    edition: str = ""
    publisher: str = ""
    url: str = ""
    source_id: str = ""
    confidence: float = 0.0
    metadata: dict[str, Any] = field(default_factory=dict)
    discovered_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

    def __post_init__(self):
        if not self.hit_id:
            self.hit_id = f"DH-{uuid.uuid4().hex[:12]}"


class SourceConnector(ABC):
    """Abstract base for global source connectors."""

    @abstractmethod
    def name(self) -> str: ...

    @abstractmethod
    def connector_type(self) -> ConnectorType: ...

    @abstractmethod
    def search(self, query: str, max_results: int = 10) -> list[DiscoveryHit]: ...

    @abstractmethod
    def health(self) -> dict: ...

    def is_available(self) -> bool:
        return True


class GlobalSourceDiscovery:
    """
    Global source discovery engine with plugin connectors.

    Orchestrates searches across multiple authoritative sources.
    """
    def __init__(self):
        self._connectors: dict[str, SourceConnector] = {}
        self._hits: dict[str, DiscoveryHit] = {}
        self._by_connector: dict[str, list[str]] = {}
        self._searches: list[dict[str, Any]] = []

    def register_connector(self, connector: SourceConnector) -> str:
        cid = f"CN-{connector.name()}"
        self._connectors[cid] = connector
        return cid

    def search(self, query: str, connector_ids: list[str] | None = None, max_results: int = 10) -> list[DiscoveryHit]:
        targets = list(self._connectors.values())
        if connector_ids:
            targets = [c for cid, c in self._connectors.items() if cid in connector_ids]
        all_hits = []
        for connector in targets:
            try:
                hits = connector.search(query, max_results)
                all_hits.extend(hits)
                for hit in hits:
                    self._hits[hit.hit_id] = hit
                    self._by_connector.setdefault(connector.name(), []).append(hit.hit_id)
            except Exception:
                pass
        self._searches.append({"query": query, "results": len(all_hits)})
        return all_hits

    def get_hits(self, connector_name: str = "") -> list[DiscoveryHit]:
        if connector_name:
            ids = self._by_connector.get(connector_name, [])
            return [self._hits[hid] for hid in ids if hid in self._hits]
        return list(self._hits.values())

    def count(self) -> int:
        return len(self._hits)

    def summary(self) -> dict:
        return {"total_hits": self.count(), "connectors": len(self._connectors), "searches": len(self._searches)}
