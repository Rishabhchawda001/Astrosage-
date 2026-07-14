"""
Extended Memory — Multi-scope memory for AstroSage.

Supports: project memory, execution memory, research memory,
book memory, source memory, edition memory, validation memory,
long-term memory.
"""
from __future__ import annotations

import json
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from pathlib import Path
from typing import Any, Optional


class MemoryScope(str, Enum):
    PROJECT = "project"
    EXECUTION = "execution"
    RESEARCH = "research"
    BOOK = "book"
    SOURCE = "source"
    EDITION = "edition"
    VALIDATION = "validation"
    LONG_TERM = "long_term"


@dataclass
class MemoryEntry:
    entry_id: str = ""
    scope: MemoryScope = MemoryScope.PROJECT
    key: str = ""
    value: Any = None
    tags: list[str] = field(default_factory=list)
    confidence: float = 1.0
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    updated_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    expires_at: str = ""
    metadata: dict[str, Any] = field(default_factory=dict)
    def __post_init__(self):
        if not self.entry_id: self.entry_id = f"ME-{uuid.uuid4().hex[:8]}"


class MemoryEngine:
    """Multi-scope memory engine with persistence."""

    def __init__(self, memory_dir: str = "knowledge/memory"):
        self.memory_dir = Path(memory_dir)
        self.memory_dir.mkdir(parents=True, exist_ok=True)
        self._entries: dict[str, MemoryEntry] = {}
        self._by_scope: dict[str, list[str]] = {}
        self._by_key: dict[str, list[str]] = {}

    def store(self, scope: MemoryScope, key: str, value: Any, tags: list[str] | None = None, confidence: float = 1.0) -> str:
        entry = MemoryEntry(scope=scope, key=key, value=value, tags=tags or [], confidence=confidence)
        self._entries[entry.entry_id] = entry
        self._by_scope.setdefault(scope.value, []).append(entry.entry_id)
        self._by_key.setdefault(key, []).append(entry.entry_id)
        return entry.entry_id

    def retrieve(self, scope: MemoryScope, key: str) -> list[MemoryEntry]:
        ids = self._by_key.get(key, [])
        return [self._entries[eid] for eid in ids if eid in self._entries and self._entries[eid].scope == scope]

    def search(self, query: str, scope: MemoryScope | None = None) -> list[MemoryEntry]:
        results = []
        for entry in self._entries.values():
            if scope and entry.scope != scope: continue
            if query.lower() in entry.key.lower() or query.lower() in str(entry.value).lower():
                results.append(entry)
        return results

    def count(self) -> int: return len(self._entries)

    def count_by_scope(self) -> dict[str, int]:
        return {scope: len(ids) for scope, ids in self._by_scope.items()}

    def summary(self) -> dict:
        return {"total": self.count(), "by_scope": self.count_by_scope()}
