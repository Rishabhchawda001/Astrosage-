"""Unit Registry — Permanent registry for every knowledge unit."""
from __future__ import annotations
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any

class UnitStatus(str, Enum):
    ACTIVE = "active"
    ARCHIVED = "archived"
    SUPERSEDED = "superseded"

@dataclass
class RegistryEntry:
    entry_id: str = ""
    unit_id: str = ""
    book_uuid: str = ""
    unit_type: str = ""
    version: int = 1
    status: UnitStatus = UnitStatus.ACTIVE
    dependencies: list[str] = field(default_factory=list)
    references: list[str] = field(default_factory=list)
    source: str = ""
    confidence: float = 0.0
    trust: float = 0.0
    checksum: str = ""
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    metadata: dict[str, Any] = field(default_factory=dict)
    def __post_init__(self):
        if not self.entry_id:
            self.entry_id = f"UR-{uuid.uuid4().hex[:12]}"

class UnitRegistry:
    def __init__(self):
        self._entries: dict[str, RegistryEntry] = {}
        self._by_unit: dict[str, str] = {}
        self._by_book: dict[str, list[str]] = {}
        self._by_type: dict[str, list[str]] = {}

    def register(self, unit_id: str, book_uuid: str = "", unit_type: str = "",
                 source: str = "", confidence: float = 0.0, **kwargs) -> RegistryEntry:
        entry = RegistryEntry(unit_id=unit_id, book_uuid=book_uuid,
                              unit_type=unit_type, source=source, confidence=confidence, **kwargs)
        self._entries[entry.entry_id] = entry
        self._by_unit[unit_id] = entry.entry_id
        if book_uuid:
            self._by_book.setdefault(book_uuid, []).append(entry.entry_id)
        if unit_type:
            self._by_type.setdefault(unit_type, []).append(entry.entry_id)
        return entry

    def get_by_unit(self, unit_id: str) -> RegistryEntry | None:
        eid = self._by_unit.get(unit_id)
        return self._entries.get(eid) if eid else None

    def get_by_book(self, book_uuid: str) -> list[RegistryEntry]:
        ids = self._by_book.get(book_uuid, [])
        return [self._entries[eid] for eid in ids if eid in self._entries]

    def count(self) -> int:
        return len(self._entries)

    def summary(self) -> dict:
        tc: dict[str, int] = {}
        for e in self._entries.values():
            tc[e.unit_type] = tc.get(e.unit_type, 0) + 1
        return {"total": self.count(), "by_type": tc, "books": len(self._by_book)}
