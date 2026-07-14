"""
Source Connector Interfaces — Plugin contracts for external source integration.

Each connector implements a standard interface for querying external sources.
No actual implementation in this phase — interfaces only.
"""
from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import Enum
from typing import Optional, AsyncIterator


class ConnectorCapability(str, Enum):
    METADATA_SEARCH = "metadata_search"
    TEXT_DOWNLOAD = "text_download"
    EDITION_LIST = "edition_list"
    CITATION_LOOKUP = "citation_lookup"
    DOI_RESOLVE = "doi_resolve"


@dataclass
class ConnectorQuery:
    """Query to an external source."""
    query_text: str = ""
    title: str = ""
    author: str = ""
    isbn: str = ""
    doi: str = ""
    language: str = ""
    max_results: int = 10
    capabilities: list[ConnectorCapability] = field(default_factory=list)


@dataclass
class ConnectorResult:
    """Result from an external source query."""
    source_id: str = ""
    title: str = ""
    author: str = ""
    language: str = ""
    url: str = ""
    download_url: str = ""
    metadata: dict = field(default_factory=dict)
    confidence: float = 0.0


class SourceConnector(ABC):
    """
    Abstract interface for source connectors.

    Every external source (Internet Archive, Open Library, Crossref, etc.)
    implements this interface. This allows swapping sources without
    changing the rest of the pipeline.
    """

    @abstractmethod
    def name(self) -> str:
        """Return the name of this connector."""
        ...

    @abstractmethod
    def source_id(self) -> str:
        """Return the source_id in the Source Registry."""
        ...

    @abstractmethod
    def capabilities(self) -> list[ConnectorCapability]:
        """Return the capabilities of this connector."""
        ...

    @abstractmethod
    def search(self, query: ConnectorQuery) -> list[ConnectorResult]:
        """Search the external source."""
        ...

    @abstractmethod
    def get_metadata(self, identifier: str) -> Optional[ConnectorResult]:
        """Get metadata for a specific item."""
        ...

    @abstractmethod
    def health_check(self) -> bool:
        """Check if the source is accessible."""
        ...


class InternetArchiveConnector(SourceConnector):
    """Stub connector for Internet Archive."""

    def name(self) -> str:
        return "internet_archive"

    def source_id(self) -> str:
        return "src_internet_archive"

    def capabilities(self) -> list[ConnectorCapability]:
        return [
            ConnectorCapability.METADATA_SEARCH,
            ConnectorCapability.TEXT_DOWNLOAD,
            ConnectorCapability.EDITION_LIST,
        ]

    def search(self, query: ConnectorQuery) -> list[ConnectorResult]:
        # Implementation in future phase
        return []

    def get_metadata(self, identifier: str) -> Optional[ConnectorResult]:
        return None

    def health_check(self) -> bool:
        return False


class OpenLibraryConnector(SourceConnector):
    """Stub connector for Open Library."""

    def name(self) -> str:
        return "open_library"

    def source_id(self) -> str:
        return "src_open_library"

    def capabilities(self) -> list[ConnectorCapability]:
        return [
            ConnectorCapability.METADATA_SEARCH,
            ConnectorCapability.EDITION_LIST,
        ]

    def search(self, query: ConnectorQuery) -> list[ConnectorResult]:
        return []

    def get_metadata(self, identifier: str) -> Optional[ConnectorResult]:
        return None

    def health_check(self) -> bool:
        return False


class CrossrefConnector(SourceConnector):
    """Stub connector for Crossref."""

    def name(self) -> str:
        return "crossref"

    def source_id(self) -> str:
        return "src_crossref"

    def capabilities(self) -> list[ConnectorCapability]:
        return [
            ConnectorCapability.METADATA_SEARCH,
            ConnectorCapability.CITATION_LOOKUP,
            ConnectorCapability.DOI_RESOLVE,
        ]

    def search(self, query: ConnectorQuery) -> list[ConnectorResult]:
        return []

    def get_metadata(self, identifier: str) -> Optional[ConnectorResult]:
        return None

    def health_check(self) -> bool:
        return False


class OpenAlexConnector(SourceConnector):
    """Stub connector for OpenAlex."""

    def name(self) -> str:
        return "openalex"

    def source_id(self) -> str:
        return "src_openalex"

    def capabilities(self) -> list[ConnectorCapability]:
        return [
            ConnectorCapability.METADATA_SEARCH,
            ConnectorCapability.CITATION_LOOKUP,
        ]

    def search(self, query: ConnectorQuery) -> list[ConnectorResult]:
        return []

    def get_metadata(self, identifier: str) -> Optional[ConnectorResult]:
        return None

    def health_check(self) -> bool:
        return False


# ── Connector Registry ──────────────────────────────────────────────────

_CONNECTOR_REGISTRY: dict[str, SourceConnector] = {}


def register_connector(connector: SourceConnector):
    """Register a source connector."""
    _CONNECTOR_REGISTRY[connector.name()] = connector


def get_connector(name: str) -> Optional[SourceConnector]:
    """Get a registered connector by name."""
    return _CONNECTOR_REGISTRY.get(name)


def list_connectors() -> list[SourceConnector]:
    """List all registered connectors."""
    return list(_CONNECTOR_REGISTRY.values())


# Register default connectors
register_connector(InternetArchiveConnector())
register_connector(OpenLibraryConnector())
register_connector(CrossrefConnector())
register_connector(OpenAlexConnector())
