"""Vector database adapter interfaces."""
from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Optional


@dataclass
class VectorEntry:
    id: str = ""
    vector: list[float] = field(default_factory=list)
    metadata: dict = field(default_factory=dict)
    text: str = ""


class VectorStoreAdapter(ABC):
    @abstractmethod
    def name(self) -> str: ...
    @abstractmethod
    def upsert(self, entries: list[VectorEntry]) -> None: ...
    @abstractmethod
    def query(self, vector: list[float], top_k: int = 10, filters: dict = None) -> list[VectorEntry]: ...
    @abstractmethod
    def delete(self, ids: list[str]) -> None: ...
    @abstractmethod
    def health(self) -> dict: ...


class QdrantAdapter(VectorStoreAdapter):
    def name(self) -> str: return "qdrant"
    def upsert(self, entries: list[VectorEntry]) -> None: pass
    def query(self, vector, top_k=10, filters=None): return []
    def delete(self, ids): pass
    def health(self): return {"status": "scaffold"}


class ChromaAdapter(VectorStoreAdapter):
    def name(self) -> str: return "chroma"
    def upsert(self, entries: list[VectorEntry]) -> None: pass
    def query(self, vector, top_k=10, filters=None): return []
    def delete(self, ids): pass
    def health(self): return {"status": "scaffold"}


class PgvectorAdapter(VectorStoreAdapter):
    def name(self) -> str: return "pgvector"
    def upsert(self, entries: list[VectorEntry]) -> None: pass
    def query(self, vector, top_k=10, filters=None): return []
    def delete(self, ids): pass
    def health(self): return {"status": "scaffold"}
