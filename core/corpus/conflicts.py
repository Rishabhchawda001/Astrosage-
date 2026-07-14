"""
Conflict Engine — When sources disagree, DO NOT choose.

Store conflict, evidence, versions, reason. Await future resolution.
"""
from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Optional


class ConflictType(str, Enum):
    WORDING = "wording"
    VERSE_NUMBERING = "verse_numbering"
    MISSING_CONTENT = "missing_content"
    EXTRA_CONTENT = "extra_content"
    METADATA = "metadata"
    TRANSLATION = "translation"
    COMMENTARY = "commentary"
    HIERARCHY = "hierarchy"
    UNKNOWN = "unknown"


class ConflictStatus(str, Enum):
    DETECTED = "detected"
    UNDER_REVIEW = "under_review"
    RESOLVED = "resolved"
    DEFERRED = "deferred"


@dataclass
class Conflict:
    """A conflict between knowledge sources."""
    conflict_id: str = ""
    conflict_type: ConflictType = ConflictType.UNKNOWN
    status: ConflictStatus = ConflictStatus.DETECTED
    variant_a: str = ""
    variant_b: str = ""
    source_a: str = ""
    source_b: str = ""
    evidence: list[str] = field(default_factory=list)
    confidence: float = 0.0
    knowledge_uuid: str = ""
    description: str = ""
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    resolved_at: str = ""
    metadata: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self):
        if not self.conflict_id:
            self.conflict_id = f"CF-{uuid.uuid4().hex[:12]}"


class ConflictEngine:
    """Detects and stores conflicts. Never auto-resolves."""

    def __init__(self):
        self._conflicts: dict[str, Conflict] = {}
        self._by_knowledge: dict[str, list[str]] = {}

    def detect(self, conflict_type: ConflictType, variant_a: str, variant_b: str,
               source_a: str = "", source_b: str = "", knowledge_uuid: str = "",
               evidence: list[str] | None = None, confidence: float = 0.0) -> Conflict:
        conflict = Conflict(
            conflict_type=conflict_type, variant_a=variant_a[:500], variant_b=variant_b[:500],
            source_a=source_a, source_b=source_b, knowledge_uuid=knowledge_uuid,
            evidence=evidence or [], confidence=confidence,
        )
        self._conflicts[conflict.conflict_id] = conflict
        if knowledge_uuid:
            self._by_knowledge.setdefault(knowledge_uuid, []).append(conflict.conflict_id)
        return conflict

    def get_conflict(self, conflict_id: str) -> Optional[Conflict]:
        return self._conflicts.get(conflict_id)

    def get_unresolved(self) -> list[Conflict]:
        return [c for c in self._conflicts.values() if c.status != ConflictStatus.RESOLVED]

    def get_by_knowledge(self, knowledge_uuid: str) -> list[Conflict]:
        ids = self._by_knowledge.get(knowledge_uuid, [])
        return [self._conflicts[cid] for cid in ids if cid in self._conflicts]

    def count(self) -> int:
        return len(self._conflicts)

    def summary(self) -> dict:
        type_counts: dict[str, int] = {}
        status_counts: dict[str, int] = {}
        for c in self._conflicts.values():
            type_counts[c.conflict_type.value] = type_counts.get(c.conflict_type.value, 0) + 1
            status_counts[c.status.value] = status_counts.get(c.status.value, 0) + 1
        return {"total": self.count(), "unresolved": len(self.get_unresolved()), "by_type": type_counts, "by_status": status_counts}
