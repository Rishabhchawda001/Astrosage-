"""Unit Alignment — Align units across languages and editions."""
from __future__ import annotations
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any

@dataclass
class AlignmentRecord:
    record_id: str = ""
    source_unit_id: str = ""
    target_unit_id: str = ""
    alignment_type: str = "translation"
    source_language: str = ""
    target_language: str = ""
    similarity: float = 0.0
    confidence: float = 0.0
    edition_id: str = ""
    translator: str = ""
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    metadata: dict[str, Any] = field(default_factory=dict)
    def __post_init__(self):
        if not self.record_id:
            self.record_id = f"UA-{uuid.uuid4().hex[:12]}"

class UnitAlignmentEngine:
    def __init__(self):
        self._records: dict[str, AlignmentRecord] = {}
        self._by_source: dict[str, list[str]] = {}
        self._by_target: dict[str, list[str]] = {}

    def align(self, source_unit_id: str, target_unit_id: str,
              alignment_type: str = "translation", **kwargs) -> AlignmentRecord:
        rec = AlignmentRecord(source_unit_id=source_unit_id,
                              target_unit_id=target_unit_id,
                              alignment_type=alignment_type, **kwargs)
        self._records[rec.record_id] = rec
        self._by_source.setdefault(source_unit_id, []).append(rec.record_id)
        self._by_target.setdefault(target_unit_id, []).append(rec.record_id)
        return rec

    def get_alignments(self, unit_id: str) -> list[AlignmentRecord]:
        s_ids = self._by_source.get(unit_id, [])
        t_ids = self._by_target.get(unit_id, [])
        all_ids = set(s_ids + t_ids)
        return [self._records[rid] for rid in all_ids if rid in self._records]

    def count(self) -> int:
        return len(self._records)

    def summary(self) -> dict:
        at: dict[str, int] = {}
        for r in self._records.values():
            at[r.alignment_type] = at.get(r.alignment_type, 0) + 1
        return {"total": self.count(), "by_type": at}
