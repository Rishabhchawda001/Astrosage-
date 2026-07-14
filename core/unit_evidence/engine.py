"""Unit Evidence — Evidence mapping for every knowledge unit."""
from __future__ import annotations
import hashlib
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any

@dataclass
class UnitEvidenceRecord:
    record_id: str = ""
    unit_id: str = ""
    source_type: str = ""
    source_id: str = ""
    edition_id: str = ""
    publisher: str = ""
    language: str = ""
    translator: str = ""
    content: str = ""
    content_hash: str = ""
    confidence: float = 0.0
    trust: float = 0.0
    agreement_score: float = 0.0
    checksum: str = ""
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    metadata: dict[str, Any] = field(default_factory=dict)
    def __post_init__(self):
        if not self.record_id:
            self.record_id = f"UE-{uuid.uuid4().hex[:12]}"
        if not self.content_hash and self.content:
            self.content_hash = hashlib.sha256(self.content.encode("utf-8")).hexdigest()[:16]

class UnitEvidenceEngine:
    def __init__(self):
        self._records: dict[str, UnitEvidenceRecord] = {}
        self._by_unit: dict[str, list[str]] = {}

    def add(self, unit_id: str, source_type: str = "", content: str = "",
            confidence: float = 0.0, trust: float = 0.0, **kwargs) -> UnitEvidenceRecord:
        rec = UnitEvidenceRecord(unit_id=unit_id, source_type=source_type,
                                 content=content, confidence=confidence,
                                 trust=trust, **kwargs)
        self._records[rec.record_id] = rec
        self._by_unit.setdefault(unit_id, []).append(rec.record_id)
        return rec

    def get_by_unit(self, unit_id: str) -> list[UnitEvidenceRecord]:
        ids = self._by_unit.get(unit_id, [])
        return [self._records[rid] for rid in ids if rid in self._records]

    def evidence_count(self, unit_id: str) -> int:
        return len(self._by_unit.get(unit_id, []))

    def deduplicate(self) -> int:
        seen: set[str] = set()
        to_remove = []
        for rid, r in self._records.items():
            key = r.content_hash or r.content
            if key in seen:
                to_remove.append(rid)
            else:
                seen.add(key)
        for rid in to_remove:
            del self._records[rid]
        return len(to_remove)

    def count(self) -> int:
        return len(self._records)

    def summary(self) -> dict:
        st: dict[str, int] = {}
        for r in self._records.values():
            st[r.source_type] = st.get(r.source_type, 0) + 1
        return {"total": self.count(), "by_source_type": st, "unique_units": len(self._by_unit)}
