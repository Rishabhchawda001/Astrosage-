"""Search adapter interfaces."""
from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Optional


@dataclass
class SearchQuery:
    query: str = ""
    top_k: int = 10
    filters: dict = field(default_factory=dict)
    language: str = ""


@dataclass
class SearchResult:
    document_id: str = ""
    chunk_id: str = ""
    text: str = ""
    score: float = 0.0
    rank: int = 0
    metadata: dict = field(default_factory=dict)


class SearchAdapter(ABC):
    @abstractmethod
    def name(self) -> str: ...
    @abstractmethod
    def search(self, query: SearchQuery) -> list[SearchResult]: ...
    @abstractmethod
    def health(self) -> dict: ...


class BM25Adapter(SearchAdapter):
    def name(self) -> str: return "bm25"
    def search(self, query: SearchQuery) -> list[SearchResult]: return []
    def health(self) -> dict: return {"status": "scaffold"}


class HybridSearchAdapter(SearchAdapter):
    def name(self) -> str: return "hybrid"
    def search(self, query: SearchQuery) -> list[SearchResult]: return []
    def health(self) -> dict: return {"status": "scaffold"}


class MetadataSearchAdapter(SearchAdapter):
    def name(self) -> str: return "metadata_search"
    def search(self, query: SearchQuery) -> list[SearchResult]: return []
    def health(self) -> dict: return {"status": "scaffold"}


class VectorSearchAdapter(SearchAdapter):
    def name(self) -> str: return "vector_search"
    def search(self, query: SearchQuery) -> list[SearchResult]: return []
    def health(self) -> dict: return {"status": "scaffold"}


class RerankingAdapter(SearchAdapter):
    def name(self) -> str: return "reranking"
    def search(self, query: SearchQuery) -> list[SearchResult]: return []
    def health(self) -> dict: return {"status": "scaffold"}


class KGSearchAdapter(SearchAdapter):
    def name(self) -> str: return "kg_search"
    def search(self, query: SearchQuery) -> list[SearchResult]: return []
    def health(self) -> dict: return {"status": "scaffold"}
