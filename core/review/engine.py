"""
Human Review Queue Engine.

Automatically queues items for human review based on confidence,
conflicts, single-source evidence, damaged scans, and other signals.
Never silently resolves. Every review item stores full context.
"""
from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Optional


class ReviewPriority(str, Enum):
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class ReviewReason(str, Enum):
    LOW_CONFIDENCE = "low_confidence"
    CONFLICT = "conflict"
    SINGLE_SOURCE = "single_source"
    DAMAGED_SCAN = "damaged_scan"
    UNKNOWN_LANGUAGE = "unknown_language"
    MANUAL_INSPECTION = "manual_inspection"
    METADATA_MISMATCH = "metadata_mismatch"
    EDITION_DISAGREEMENT = "edition_disagreement"
    TRANSLATION_CONFLICT = "translation_conflict"
    BROKEN_HIERARCHY = "broken_hierarchy"
    RECONSTRUCTION_LOW_CONF = "reconstruction_low_confidence"
    CITATION_MISSING = "citation_missing"
    CHECKSUM_MISMATCH = "checksum_mismatch"


class ReviewStatus(str, Enum):
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    APPROVED = "approved"
    REJECTED = "rejected"
    DEFERRED = "deferred"


@dataclass
class ReviewItem:
    item_id: str = ""
    knowledge_uuid: str = ""
    priority: ReviewPriority = ReviewPriority.MEDIUM
    reason: ReviewReason = ReviewReason.MANUAL_INSPECTION
    status: ReviewStatus = ReviewStatus.PENDING
    title: str = ""
    description: str = ""
    confidence: float = 0.0
    evidence_count: int = 0
    conflict_count: int = 0
    source_ids: list[str] = field(default_factory=list)
    edition_ids: list[str] = field(default_factory=list)
    context: dict[str, Any] = field(default_factory=dict)
    assigned_to: str = ""
    reviewer_notes: str = ""
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    reviewed_at: str = ""
    metadata: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self):
        if not self.item_id:
            self.item_id = f"RI-{uuid.uuid4().hex[:12]}"


class ReviewEngine:
    """Production human review queue engine."""

    def __init__(self):
        self._items: dict[str, ReviewItem] = {}
        self._by_knowledge: dict[str, list[str]] = {}
        self._by_status: dict[str, list[str]] = {}
        self._by_priority: dict[str, list[str]] = {}

    def queue(self, knowledge_uuid: str, reason: ReviewReason, priority: ReviewPriority = ReviewPriority.MEDIUM,
              title: str = "", description: str = "", confidence: float = 0.0,
              evidence_count: int = 0, conflict_count: int = 0,
              source_ids: list[str] | None = None, edition_ids: list[str] | None = None,
              context: dict[str, Any] | None = None, **kwargs) -> ReviewItem:
        item = ReviewItem(
            knowledge_uuid=knowledge_uuid, reason=reason, priority=priority,
            title=title, description=description, confidence=confidence,
            evidence_count=evidence_count, conflict_count=conflict_count,
            source_ids=source_ids or [], edition_ids=edition_ids or [],
            context=context or {}, metadata=kwargs)
        self._items[item.item_id] = item
        self._by_knowledge.setdefault(knowledge_uuid, []).append(item.item_id)
        self._by_status.setdefault(item.status.value, []).append(item.item_id)
        self._by_priority.setdefault(item.priority.value, []).append(item.item_id)
        return item

    def queue_low_confidence(self, knowledge_uuid: str, confidence: float, **kwargs) -> ReviewItem:
        priority = ReviewPriority.HIGH if confidence < 0.3 else ReviewPriority.MEDIUM
        return self.queue(knowledge_uuid, ReviewReason.LOW_CONFIDENCE, priority=priority,
                          confidence=confidence, title=f"Low confidence: {confidence:.2f}", **kwargs)

    def queue_conflict(self, knowledge_uuid: str, conflict_count: int, **kwargs) -> ReviewItem:
        priority = ReviewPriority.CRITICAL if conflict_count > 3 else ReviewPriority.HIGH
        return self.queue(knowledge_uuid, ReviewReason.CONFLICT, priority=priority,
                          conflict_count=conflict_count,
                          title=f"{conflict_count} conflicts detected", **kwargs)

    def queue_single_source(self, knowledge_uuid: str, source_id: str, **kwargs) -> ReviewItem:
        return self.queue(knowledge_uuid, ReviewReason.SINGLE_SOURCE, priority=ReviewPriority.MEDIUM,
                          title="Single source evidence", source_ids=[source_id], **kwargs)

    def approve(self, item_id: str, reviewer_notes: str = "") -> bool:
        item = self._items.get(item_id)
        if item:
            item.status = ReviewStatus.APPROVED
            item.reviewer_notes = reviewer_notes
            item.reviewed_at = datetime.now(timezone.utc).isoformat()
            return True
        return False

    def reject(self, item_id: str, reviewer_notes: str = "") -> bool:
        item = self._items.get(item_id)
        if item:
            item.status = ReviewStatus.REJECTED
            item.reviewer_notes = reviewer_notes
            item.reviewed_at = datetime.now(timezone.utc).isoformat()
            return True
        return False

    def get_pending(self) -> list[ReviewItem]:
        return [i for i in self._items.values() if i.status == ReviewStatus.PENDING]

    def get_by_knowledge(self, knowledge_uuid: str) -> list[ReviewItem]:
        ids = self._by_knowledge.get(knowledge_uuid, [])
        return [self._items[iid] for iid in ids if iid in self._items]

    def get_by_priority(self, priority: ReviewPriority) -> list[ReviewItem]:
        return [i for i in self._items.values() if i.priority == priority and i.status == ReviewStatus.PENDING]

    def count(self) -> int:
        return len(self._items)

    def summary(self) -> dict:
        ps: dict[str, int] = {}
        rs: dict[str, int] = {}
        ss: dict[str, int] = {}
        for item in self._items.values():
            ps[item.priority.value] = ps.get(item.priority.value, 0) + 1
            rs[item.reason.value] = rs.get(item.reason.value, 0) + 1
            ss[item.status.value] = ss.get(item.status.value, 0) + 1
        return {"total": self.count(), "by_priority": ps, "by_reason": rs, "by_status": ss}
