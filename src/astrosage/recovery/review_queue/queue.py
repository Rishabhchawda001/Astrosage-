"""
Human Review Queue — Manages items requiring human review.

Supports states: Pending, Approved, Rejected, Deferred, Needs More Evidence.
"""
from __future__ import annotations

import json
import uuid
from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from enum import Enum
from pathlib import Path
from typing import Optional


class ReviewState(str, Enum):
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    DEFERRED = "deferred"
    NEEDS_MORE_EVIDENCE = "needs_more_evidence"


class ReviewType(str, Enum):
    OCR_CORRECTION = "ocr_correction"
    EDITION_CONFLICT = "edition_conflict"
    METADATA_VERIFICATION = "metadata_verification"
    RECOVERY_VERIFICATION = "recovery_verification"
    QUALITY_ISSUE = "quality_issue"
    CONFIDENCE_LOW = "confidence_low"


@dataclass
class ReviewItem:
    item_id: str
    review_type: ReviewType
    document_uuid: str
    book_uuid: str = ""
    page: int = 0
    original_text: str = ""
    candidate_text: str = ""
    evidence_summary: str = ""
    state: ReviewState = ReviewState.PENDING
    priority: int = 5  # 1=highest
    reviewer: str = ""
    timestamp: str = ""
    notes: str = ""
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    updated_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

    def to_dict(self) -> dict:
        d = asdict(self)
        d["review_type"] = self.review_type.value
        d["state"] = self.state.value
        return d


class ReviewQueue:
    """Human review queue for knowledge recovery."""

    def __init__(self, queue_dir: str = "knowledge/recovery/review_queue"):
        self.queue_dir = Path(queue_dir)
        self.queue_dir.mkdir(parents=True, exist_ok=True)
        self._items: dict[str, ReviewItem] = {}

    def add_item(
        self,
        review_type: ReviewType,
        document_uuid: str,
        book_uuid: str = "",
        page: int = 0,
        original_text: str = "",
        candidate_text: str = "",
        evidence_summary: str = "",
        priority: int = 5,
    ) -> str:
        item_id = f"RV-{uuid.uuid4().hex[:12]}"
        item = ReviewItem(
            item_id=item_id,
            review_type=review_type,
            document_uuid=document_uuid,
            book_uuid=book_uuid,
            page=page,
            original_text=original_text,
            candidate_text=candidate_text,
            evidence_summary=evidence_summary,
            priority=priority,
        )
        self._items[item_id] = item
        return item_id

    def approve(self, item_id: str, reviewer: str, notes: str = ""):
        if item_id in self._items:
            self._items[item_id].state = ReviewState.APPROVED
            self._items[item_id].reviewer = reviewer
            self._items[item_id].notes = notes
            self._items[item_id].timestamp = datetime.now(timezone.utc).isoformat()
            self._items[item_id].updated_at = datetime.now(timezone.utc).isoformat()

    def reject(self, item_id: str, reviewer: str, notes: str = ""):
        if item_id in self._items:
            self._items[item_id].state = ReviewState.REJECTED
            self._items[item_id].reviewer = reviewer
            self._items[item_id].notes = notes
            self._items[item_id].timestamp = datetime.now(timezone.utc).isoformat()
            self._items[item_id].updated_at = datetime.now(timezone.utc).isoformat()

    def defer(self, item_id: str, reviewer: str, notes: str = ""):
        if item_id in self._items:
            self._items[item_id].state = ReviewState.DEFERRED
            self._items[item_id].reviewer = reviewer
            self._items[item_id].notes = notes
            self._items[item_id].updated_at = datetime.now(timezone.utc).isoformat()

    def request_evidence(self, item_id: str, reviewer: str, notes: str = ""):
        if item_id in self._items:
            self._items[item_id].state = ReviewState.NEEDS_MORE_EVIDENCE
            self._items[item_id].reviewer = reviewer
            self._items[item_id].notes = notes
            self._items[item_id].updated_at = datetime.now(timezone.utc).isoformat()

    def get_item(self, item_id: str) -> Optional[ReviewItem]:
        return self._items.get(item_id)

    def get_pending(self) -> list[ReviewItem]:
        items = [i for i in self._items.values() if i.state == ReviewState.PENDING]
        return sorted(items, key=lambda i: i.priority)

    def get_by_state(self, state: ReviewState) -> list[ReviewItem]:
        return [i for i in self._items.values() if i.state == state]

    def get_by_type(self, review_type: ReviewType) -> list[ReviewItem]:
        return [i for i in self._items.values() if i.review_type == review_type]

    def save(self):
        data = {iid: i.to_dict() for iid, i in self._items.items()}
        filepath = self.queue_dir / "review_queue.json"
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

    def load(self):
        filepath = self.queue_dir / "review_queue.json"
        if not filepath.exists():
            return
        with open(filepath, "r", encoding="utf-8") as f:
            data = json.load(f)
        for iid, idata in data.items():
            idata["review_type"] = ReviewType(idata["review_type"])
            idata["state"] = ReviewState(idata["state"])
            self._items[iid] = ReviewItem(**idata)

    def summary(self) -> dict:
        state_counts = {}
        type_counts = {}
        for i in self._items.values():
            state_counts[i.state.value] = state_counts.get(i.state.value, 0) + 1
            type_counts[i.review_type.value] = type_counts.get(i.review_type.value, 0) + 1
        return {
            "total_items": len(self._items),
            "by_state": state_counts,
            "by_type": type_counts,
            "pending_count": len(self.get_pending()),
        }
