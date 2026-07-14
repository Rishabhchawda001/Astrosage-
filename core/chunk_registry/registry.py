"""
Chunk Registry — Permanent registry for all chunks.

Every chunk gets UUID, version, dependencies, references, source,
confidence, trust, and status tracking.
"""
from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Optional


class ChunkStatus(str, Enum):
    CREATED = "created"
    VALIDATED = "validated"
    INDEXED = "indexed"
    EMBEDDED = "embedded"
    RETRIEVABLE = "retrievable"
    DEPRECATED = "deprecated"
    QUARANTINED = "quarantined"


@dataclass
class ChunkRecord:
    """Registry record for a chunk."""
    chunk_id: str = ""
    version: int = 1
    status: ChunkStatus = ChunkStatus.CREATED
    dependencies: list[str] = field(default_factory=list)
    references: list[str] = field(default_factory=list)
    source_document: str = ""
    source_page: int = 0
    confidence: float = 0.0
    trust_score: float = 0.0
    checksum: str = ""
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    updated_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    registered_by: str = "chunking_engine"
    metadata: dict[str, Any] = field(default_factory=dict)


class ChunkRegistry:
    """
    Permanent chunk registry.
    
    Tracks all chunks, their versions, dependencies, and status.
    Supports version upgrades and status transitions.
    """

    def __init__(self):
        self._records: dict[str, ChunkRecord] = {}
        self._versions: dict[str, list[int]] = {}

    def register(self, record: ChunkRecord) -> str:
        self._records[record.chunk_id] = record
        self._versions.setdefault(record.chunk_id, []).append(record.version)
        return record.chunk_id

    def get(self, chunk_id: str) -> Optional[ChunkRecord]:
        return self._records.get(chunk_id)

    def update_status(self, chunk_id: str, status: ChunkStatus) -> bool:
        record = self._records.get(chunk_id)
        if not record:
            return False
        record.status = status
        record.updated_at = datetime.now(timezone.utc).isoformat()
        return True

    def increment_version(self, chunk_id: str) -> int:
        record = self._records.get(chunk_id)
        if not record:
            return 0
        record.version += 1
        record.updated_at = datetime.now(timezone.utc).isoformat()
        self._versions.setdefault(chunk_id, []).append(record.version)
        return record.version

    def get_versions(self, chunk_id: str) -> list[int]:
        return self._versions.get(chunk_id, [])

    def list_by_status(self, status: ChunkStatus) -> list[ChunkRecord]:
        return [r for r in self._records.values() if r.status == status]

    def list_by_source(self, source: str) -> list[ChunkRecord]:
        return [r for r in self._records.values() if r.source_document == source]

    def get_dependencies(self, chunk_id: str) -> list[ChunkRecord]:
        record = self._records.get(chunk_id)
        if not record:
            return []
        return [self._records[dep] for dep in record.dependencies if dep in self._records]

    def count(self) -> int:
        return len(self._records)

    def summary(self) -> dict:
        status_counts: dict[str, int] = {}
        for r in self._records.values():
            status_counts[r.status.value] = status_counts.get(r.status.value, 0) + 1
        return {
            "total_records": self.count(),
            "by_status": status_counts,
        }
