"""Change Detection — Detect new editions, updated scans, metadata changes."""
from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Optional


class ChangeType(str, Enum):
    NEW_EDITION = "new_edition"
    UPDATED_EDITION = "updated_edition"
    BETTER_SCAN = "better_scan"
    BETTER_OCR = "better_ocr"
    METADATA_CHANGE = "metadata_change"
    NEW_REPOSITORY = "new_repository"
    LICENSE_CHANGE = "license_change"


class ChangeStatus(str, Enum):
    DETECTED = "detected"
    QUEUED = "queued"
    REVIEWED = "reviewed"
    ACCEPTED = "accepted"
    REJECTED = "rejected"


@dataclass
class ChangeRecord:
    change_id: str = ""
    change_type: ChangeType = ChangeType.NEW_EDITION
    status: ChangeStatus = ChangeStatus.DETECTED
    source_id: str = ""
    edition_id: str = ""
    description: str = ""
    old_value: str = ""
    new_value: str = ""
    confidence: float = 0.0
    detected_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    metadata: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self):
        if not self.change_id:
            self.change_id = f"CD-{uuid.uuid4().hex[:12]}"


class ChangeDetectionEngine:
    def __init__(self):
        self._changes: dict[str, ChangeRecord] = {}
        self._by_source: dict[str, list[str]] = {}

    def detect(self, change_type: ChangeType, source_id: str = "", description: str = "", **kwargs) -> ChangeRecord:
        record = ChangeRecord(change_type=change_type, source_id=source_id, description=description, **kwargs)
        self._changes[record.change_id] = record
        self._by_source.setdefault(source_id, []).append(record.change_id)
        return record

    def get_pending(self) -> list[ChangeRecord]:
        return [c for c in self._changes.values() if c.status == ChangeStatus.DETECTED]

    def count(self) -> int:
        return len(self._changes)

    def summary(self) -> dict:
        type_counts: dict[str, int] = {}
        for c in self._changes.values():
            type_counts[c.change_type.value] = type_counts.get(c.change_type.value, 0) + 1
        return {"total": self.count(), "pending": len(self.get_pending()), "by_type": type_counts}
