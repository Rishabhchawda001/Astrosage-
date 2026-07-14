"""Source Connector plugins — ABC-based interfaces for external source integration."""
from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Optional


@dataclass
class SourceQuery:
    title: str = ""
    author: str = ""
    isbn: str = ""
    doi: str = ""
    language: str = ""
    max_results: int = 10


@dataclass
class SourceResult:
    title: str = ""
    author: str = ""
    url: str = ""
    download_url: str = ""
    metadata: dict = field(default_factory=dict)
    confidence: float = 0.0


class SourceConnectorPlugin(ABC):
    """Abstract interface for source connector plugins."""

    @abstractmethod
    def name(self) -> str:
        ...

    @abstractmethod
    def search(self, query: SourceQuery) -> list[SourceResult]:
        ...

    @abstractmethod
    def get_metadata(self, identifier: str) -> Optional[SourceResult]:
        ...

    @abstractmethod
    def health_check(self) -> bool:
        ...
