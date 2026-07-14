"""Memory adapter interfaces."""
from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any


@dataclass
class MemoryEntry:
    key: str = ""
    value: Any = None
    metadata: dict = field(default_factory=dict)
    timestamp: str = ""


class MemoryAdapter(ABC):
    @abstractmethod
    def name(self) -> str: ...
    @abstractmethod
    def store(self, entry: MemoryEntry) -> None: ...
    @abstractmethod
    def retrieve(self, key: str) -> MemoryEntry | None: ...
    @abstractmethod
    def search(self, query: str, top_k: int = 10) -> list[MemoryEntry]: ...
    @abstractmethod
    def delete(self, key: str) -> None: ...
    @abstractmethod
    def health(self) -> dict: ...


class KnowledgeMemoryAdapter(MemoryAdapter):
    def name(self): return "knowledge_memory"
    def store(self, entry): pass
    def retrieve(self, key): return None
    def search(self, query, top_k=10): return []
    def delete(self, key): pass
    def health(self): return {"status": "scaffold"}


class AgentMemoryAdapter(MemoryAdapter):
    def name(self): return "agent_memory"
    def store(self, entry): pass
    def retrieve(self, key): return None
    def search(self, query, top_k=10): return []
    def delete(self, key): pass
    def health(self): return {"status": "scaffold"}


class SessionMemoryAdapter(MemoryAdapter):
    def name(self): return "session_memory"
    def store(self, entry): pass
    def retrieve(self, key): return None
    def search(self, query, top_k=10): return []
    def delete(self, key): pass
    def health(self): return {"status": "scaffold"}


class ProjectMemoryAdapter(MemoryAdapter):
    def name(self): return "project_memory"
    def store(self, entry): pass
    def retrieve(self, key): return None
    def search(self, query, top_k=10): return []
    def delete(self, key): pass
    def health(self): return {"status": "scaffold"}


class BenchmarkMemoryAdapter(MemoryAdapter):
    def name(self): return "benchmark_memory"
    def store(self, entry): pass
    def retrieve(self, key): return None
    def search(self, query, top_k=10): return []
    def delete(self, key): pass
    def health(self): return {"status": "scaffold"}


class RecoveryMemoryAdapter(MemoryAdapter):
    def name(self): return "recovery_memory"
    def store(self, entry): pass
    def retrieve(self, key): return None
    def search(self, query, top_k=10): return []
    def delete(self, key): pass
    def health(self): return {"status": "scaffold"}
