"""Unit Statistics — Statistics for knowledge unit processing."""
from __future__ import annotations
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any

@dataclass
class UnitStats:
    stats_id: str = ""
    book_uuid: str = ""
    book_title: str = ""
    total_units: int = 0
    verified_units: int = 0
    recovered_units: int = 0
    unknown_units: int = 0
    conflict_units: int = 0
    canonical_units: int = 0
    evidence_density: float = 0.0
    average_confidence: float = 0.0
    completeness_pct: float = 0.0
    computed_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    metadata: dict[str, Any] = field(default_factory=dict)
    def __post_init__(self):
        if not self.stats_id:
            self.stats_id = f"US-{uuid.uuid4().hex[:12]}"

class UnitStatisticsEngine:
    def __init__(self):
        self._stats: dict[str, UnitStats] = {}
        self._by_book: dict[str, str] = {}

    def record(self, book_uuid: str, book_title: str = "", **kwargs) -> UnitStats:
        s = UnitStats(book_uuid=book_uuid, book_title=book_title, **kwargs)
        for k, v in kwargs.items():
            if hasattr(s, k):
                setattr(s, k, v)
        if s.total_units > 0:
            s.completeness_pct = (s.verified_units + s.recovered_units) / s.total_units * 100
        self._stats[s.stats_id] = s
        self._by_book[book_uuid] = s.stats_id
        return s

    def get_by_book(self, book_uuid: str) -> UnitStats | None:
        sid = self._by_book.get(book_uuid)
        return self._stats.get(sid) if sid else None

    def corpus_summary(self) -> dict:
        all_s = list(self._stats.values())
        if not all_s:
            return {"total_books": 0}
        return {
            "total_books": len(all_s),
            "total_units": sum(s.total_units for s in all_s),
            "verified": sum(s.verified_units for s in all_s),
            "recovered": sum(s.recovered_units for s in all_s),
            "unknown": sum(s.unknown_units for s in all_s),
            "conflicts": sum(s.conflict_units for s in all_s),
            "mean_completeness": round(
                sum(s.completeness_pct for s in all_s) / len(all_s), 2),
        }

    def count(self) -> int:
        return len(self._stats)
