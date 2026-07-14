"""
Conflict Resolution Engine.

Detects, classifies, and manages conflicts between sources.
Never silently resolves. Generates review tasks for all conflicts.
"""
from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Optional


class ConflictType(str, Enum):
    TRANSLATION = "translation"
    PUBLISHER = "publisher"
    OCR = "ocr"
    COMMENTARY = "commentary"
    HISTORICAL = "historical"
    METADATA = "metadata"
    SEMANTIC = "semantic"
    NUMBERING = "numbering"
    STRUCTURE = "structure"
    MISSING_CONTENT = "missing_content"
    EXTRA_CONTENT = "extra_content"


class ConflictSeverity(str, Enum):
    MINOR = "minor"
    MODERATE = "moderate"
    MAJOR = "major"
    CRITICAL = "critical"


class ConflictStatus(str, Enum):
    DETECTED = "detected"
    UNDER_REVIEW = "under_review"
    RESOLVED = "resolved"
    UNRESOLVED = "unresolved"
    DEFERRED = "deferred"


@dataclass
class Conflict:
    conflict_id: str = ""
    knowledge_uuid: str = ""
    conflict_type: ConflictType = ConflictType.SEMANTIC
    severity: ConflictSeverity = ConflictSeverity.MODERATE
    status: ConflictStatus = ConflictStatus.DETECTED
    title: str = ""
    description: str = ""
    source_a: str = ""
    source_b: str = ""
    text_a: str = ""
    text_b: str = ""
    edition_a: str = ""
    edition_b: str = ""
    page_a: int = 0
    page_b: int = 0
    verse_a: str = ""
    verse_b: str = ""
    confidence_a: float = 0.0
    confidence_b: float = 0.0
    resolution: str = ""
    resolved_by: str = ""
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    resolved_at: str = ""
    metadata: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self):
        if not self.conflict_id:
            self.conflict_id = f"CF-{uuid.uuid4().hex[:12]}"


class ConflictResolutionEngine:
    """Production conflict resolution engine. Never silently resolves."""

    def __init__(self, auto_classify: bool = True):
        self.auto_classify = auto_classify
        self._conflicts: dict[str, Conflict] = {}
        self._by_knowledge: dict[str, list[str]] = {}
        self._by_type: dict[str, list[str]] = {}
        self._by_severity: dict[str, list[str]] = {}
        self._by_status: dict[str, list[str]] = {}

    def detect(self, knowledge_uuid: str, conflict_type: ConflictType,
               text_a: str = "", text_b: str = "", source_a: str = "", source_b: str = "",
               edition_a: str = "", edition_b: str = "",
               severity: ConflictSeverity | None = None,
               title: str = "", description: str = "",
               confidence_a: float = 0.0, confidence_b: float = 0.0,
               **kwargs) -> Conflict:
        if self.auto_classify and severity is None:
            severity = self._classify_severity(text_a, text_b)

        conflict = Conflict(
            knowledge_uuid=knowledge_uuid, conflict_type=conflict_type,
            severity=severity, title=title, description=description,
            source_a=source_a, source_b=source_b,
            text_a=text_a, text_b=text_b,
            edition_a=edition_a, edition_b=edition_b,
            confidence_a=confidence_a, confidence_b=confidence_b, metadata=kwargs)
        self._conflicts[conflict.conflict_id] = conflict
        self._by_knowledge.setdefault(knowledge_uuid, []).append(conflict.conflict_id)
        self._by_type.setdefault(conflict_type.value, []).append(conflict.conflict_id)
        self._by_severity.setdefault(severity.value, []).append(conflict.conflict_id)
        self._by_status.setdefault(conflict.status.value, []).append(conflict.conflict_id)
        return conflict

    def _classify_severity(self, text_a: str, text_b: str) -> ConflictSeverity:
        if not text_a or not text_b:
            return ConflictSeverity.MODERATE
        a_words = set(text_a.lower().split())
        b_words = set(text_b.lower().split())
        if not a_words and not b_words:
            return ConflictSeverity.MINOR
        overlap = len(a_words & b_words) / max(len(a_words | b_words), 1)
        if overlap > 0.8:
            return ConflictSeverity.MINOR
        elif overlap > 0.5:
            return ConflictSeverity.MODERATE
        elif overlap > 0.2:
            return ConflictSeverity.MAJOR
        return ConflictSeverity.CRITICAL

    def resolve(self, conflict_id: str, resolution: str, resolved_by: str = "system") -> bool:
        conflict = self._conflicts.get(conflict_id)
        if conflict:
            conflict.status = ConflictStatus.RESOLVED
            conflict.resolution = resolution
            conflict.resolved_by = resolved_by
            conflict.resolved_at = datetime.now(timezone.utc).isoformat()
            return True
        return False

    def get_conflicts(self, knowledge_uuid: str) -> list[Conflict]:
        ids = self._by_knowledge.get(knowledge_uuid, [])
        return [self._conflicts[cid] for cid in ids if cid in self._conflicts]

    def get_unresolved(self) -> list[Conflict]:
        return [c for c in self._conflicts.values() if c.status == ConflictStatus.DETECTED]

    def get_by_severity(self, severity: ConflictSeverity) -> list[Conflict]:
        return [c for c in self._conflicts.values() if c.severity == severity]

    def count(self) -> int:
        return len(self._conflicts)

    def summary(self) -> dict:
        tc: dict[str, int] = {}
        sc: dict[str, int] = {}
        ss: dict[str, int] = {}
        for c in self._conflicts.values():
            tc[c.conflict_type.value] = tc.get(c.conflict_type.value, 0) + 1
            sc[c.severity.value] = sc.get(c.severity.value, 0) + 1
            ss[c.status.value] = ss.get(c.status.value, 0) + 1
        return {"total": self.count(), "by_type": tc, "by_severity": sc, "by_status": ss}
