"""Source Registry — Central registry for all knowledge sources."""
from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Optional


class SourceType(str, Enum):
    DIGITAL_LIBRARY = "digital_library"
    ACADEMIC = "academic"
    GOVERNMENT = "government"
    UNIVERSITY = "university"
    REPOSITORY = "repository"
    PUBLISHER = "publisher"
    LOCAL = "local"
    MIRROR = "mirror"


@dataclass
class SourceEntry:
    source_id: str = ""
    name: str = ""
    source_type: SourceType = SourceType.DIGITAL_LIBRARY
    base_url: str = ""
    trust_score: float = 0.0
    language_support: list[str] = field(default_factory=list)
    license_id: str = ""
    status: str = "active"
    metadata: dict[str, Any] = field(default_factory=dict)
    registered_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

    def __post_init__(self):
        if not self.source_id:
            self.source_id = f"SR-{uuid.uuid4().hex[:12]}"


class SourceRegistry:
    def __init__(self):
        self._entries: dict[str, SourceEntry] = {}

    def register(self, entry: SourceEntry) -> str:
        self._entries[entry.source_id] = entry
        return entry.source_id

    def get(self, source_id: str) -> Optional[SourceEntry]:
        return self._entries.get(source_id)

    def get_by_type(self, source_type: SourceType) -> list[SourceEntry]:
        return [e for e in self._entries.values() if e.source_type == source_type]

    def count(self) -> int:
        return len(self._entries)

    def summary(self) -> dict:
        type_counts: dict[str, int] = {}
        for e in self._entries.values():
            type_counts[e.source_type.value] = type_counts.get(e.source_type.value, 0) + 1
        return {"total": self.count(), "by_type": type_counts}
