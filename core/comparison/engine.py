"""
Comparison Engine — Conflict detection between knowledge sources.

Detects: different wording, verse numbering, metadata conflicts,
page mapping differences, translation conflicts, missing content.
Never auto-resolves.
"""
from __future__ import annotations

import hashlib
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Optional


class ConflictType(str, Enum):
    WORDING = "wording"
    VERSE_NUMBERING = "verse_numbering"
    METADATA = "metadata"
    PAGE_MAPPING = "page_mapping"
    TRANSLATION = "translation"
    MISSING_CONTENT = "missing_content"
    STRUCTURAL = "structural"
    CITATION = "citation"
    ENCODING = "encoding"
    UNKNOWN = "unknown"


class ConflictSeverity(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class ConflictStatus(str, Enum):
    DETECTED = "detected"
    UNDER_REVIEW = "under_review"
    RESOLVED = "resolved"
    DEFERRED = "deferred"
    UNRESOLVABLE = "unresolvable"


@dataclass
class Conflict:
    """A detected conflict between two or more sources."""
    conflict_id: str = ""
    conflict_type: ConflictType = ConflictType.UNKNOWN
    severity: ConflictSeverity = ConflictSeverity.MEDIUM
    status: ConflictStatus = ConflictStatus.DETECTED
    variant_a: str = ""
    variant_b: str = ""
    variant_c: str = ""
    source_a: str = ""
    source_b: str = ""
    source_c: str = ""
    preferred: str = ""
    reason: str = ""
    evidence: list[str] = field(default_factory=list)
    knowledge_uuid: str = ""
    page: int = 0
    metadata: dict[str, Any] = field(default_factory=dict)
    detected_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    resolved_at: str = ""
    resolver: str = ""

    def __post_init__(self):
        if not self.conflict_id:
            self.conflict_id = f"CD-{uuid.uuid4().hex[:12]}"

    def resolve(self, preferred: str, resolver: str = "human", reason: str = "") -> None:
        self.preferred = preferred
        self.resolver = resolver
        self.reason = reason
        self.status = ConflictStatus.RESOLVED
        self.resolved_at = datetime.now(timezone.utc).isoformat()

    def defer(self) -> None:
        self.status = ConflictStatus.DEFERRED


class ComparisonEngine:
    """
    Conflict detection engine.

    Compares knowledge items and detects conflicts.
    Never auto-resolves. All conflicts require human review.
    """

    def __init__(self):
        self._conflicts: dict[str, Conflict] = {}
        self._by_knowledge: dict[str, list[str]] = {}
        self._by_type: dict[str, list[str]] = {}

    def detect_text_conflict(
        self,
        knowledge_uuid: str,
        variant_a: str,
        variant_b: str,
        source_a: str = "",
        source_b: str = "",
    ) -> Conflict:
        """Detect text-level conflicts between two variants."""
        severity = ConflictSeverity.LOW
        if variant_a.strip() == variant_b.strip():
            severity = ConflictSeverity.LOW
        elif len(variant_a) != len(variant_b):
            severity = ConflictSeverity.MEDIUM
        elif hashlib.sha256(variant_a.encode()).hexdigest() != hashlib.sha256(variant_b.encode()).hexdigest():
            severity = ConflictSeverity.HIGH
        else:
            severity = ConflictSeverity.MEDIUM

        conflict = Conflict(
            conflict_type=ConflictType.WORDING,
            severity=severity,
            variant_a=variant_a[:500],
            variant_b=variant_b[:500],
            source_a=source_a,
            source_b=source_b,
            knowledge_uuid=knowledge_uuid,
        )
        return self._register_conflict(conflict)

    def detect_metadata_conflict(
        self,
        knowledge_uuid: str,
        metadata_a: dict,
        metadata_b: dict,
        source_a: str = "",
        source_b: str = "",
    ) -> list[Conflict]:
        """Detect metadata-level conflicts."""
        conflicts = []
        all_keys = set(metadata_a.keys()) | set(metadata_b.keys())
        for key in all_keys:
            val_a = metadata_a.get(key)
            val_b = metadata_b.get(key)
            if val_a != val_b and val_a is not None and val_b is not None:
                conflict = Conflict(
                    conflict_type=ConflictType.METADATA,
                    severity=ConflictSeverity.LOW if key in ("edition", "publisher") else ConflictSeverity.MEDIUM,
                    variant_a=str(val_a),
                    variant_b=str(val_b),
                    source_a=source_a,
                    source_b=source_b,
                    knowledge_uuid=knowledge_uuid,
                    metadata={"field": key},
                )
                conflicts.append(self._register_conflict(conflict))
        return conflicts

    def detect_missing_content(
        self,
        knowledge_uuid: str,
        present_in: list[str],
        missing_from: list[str],
    ) -> Conflict:
        """Detect content present in some sources but not others."""
        conflict = Conflict(
            conflict_type=ConflictType.MISSING_CONTENT,
            severity=ConflictSeverity.HIGH,
            source_a=", ".join(present_in),
            source_b=", ".join(missing_from),
            knowledge_uuid=knowledge_uuid,
            reason=f"Content present in [{', '.join(present_in)}] but missing from [{', '.join(missing_from)}]",
        )
        return self._register_conflict(conflict)

    def detect_verse_conflict(
        self,
        knowledge_uuid: str,
        numbering_a: str,
        numbering_b: str,
        source_a: str = "",
        source_b: str = "",
    ) -> Conflict:
        conflict = Conflict(
            conflict_type=ConflictType.VERSE_NUMBERING,
            severity=ConflictSeverity.MEDIUM,
            variant_a=numbering_a,
            variant_b=numbering_b,
            source_a=source_a,
            source_b=source_b,
            knowledge_uuid=knowledge_uuid,
        )
        return self._register_conflict(conflict)

    def _register_conflict(self, conflict: Conflict) -> Conflict:
        self._conflicts[conflict.conflict_id] = conflict
        self._by_knowledge.setdefault(conflict.knowledge_uuid, []).append(conflict.conflict_id)
        self._by_type.setdefault(conflict.conflict_type.value, []).append(conflict.conflict_id)
        return conflict

    def get_conflict(self, conflict_id: str) -> Optional[Conflict]:
        return self._conflicts.get(conflict_id)

    def get_conflicts_for_knowledge(self, knowledge_uuid: str) -> list[Conflict]:
        ids = self._by_knowledge.get(knowledge_uuid, [])
        return [self._conflicts[cid] for cid in ids if cid in self._conflicts]

    def get_unresolved(self) -> list[Conflict]:
        return [c for c in self._conflicts.values() if c.status != ConflictStatus.RESOLVED]

    def summary(self) -> dict:
        type_counts: dict[str, int] = {}
        severity_counts: dict[str, int] = {}
        status_counts: dict[str, int] = {}
        for c in self._conflicts.values():
            type_counts[c.conflict_type.value] = type_counts.get(c.conflict_type.value, 0) + 1
            severity_counts[c.severity.value] = severity_counts.get(c.severity.value, 0) + 1
            status_counts[c.status.value] = status_counts.get(c.status.value, 0) + 1
        return {
            "total_conflicts": len(self._conflicts),
            "unresolved": len(self.get_unresolved()),
            "by_type": type_counts,
            "by_severity": severity_counts,
            "by_status": status_counts,
        }
