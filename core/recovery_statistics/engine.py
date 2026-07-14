"""
Recovery Statistics Engine — Tracks and aggregates recovery statistics.

Produces Book Completion Registry, Corpus Completion Registry,
Evidence Coverage Registry, Variant Registry, Recovery Registry,
Unknown Registry, Conflict Registry.
"""
from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any


@dataclass
class RecoveryStats:
    stats_id: str = ""
    book_uuid: str = ""
    book_title: str = ""
    language: str = ""
    total_paragraphs: int = 0
    total_gaps: int = 0
    gaps_recovered: int = 0
    gaps_unknown: int = 0
    gaps_conflict: int = 0
    editions_discovered: int = 0
    translations_found: int = 0
    commentaries_found: int = 0
    evidence_collected: int = 0
    variants_created: int = 0
    paragraphs_verified: int = 0
    paragraphs_recovered: int = 0
    paragraphs_unknown: int = 0
    paragraphs_conflicted: int = 0
    confidence_mean: float = 0.0
    trust_mean: float = 0.0
    completeness_pct: float = 0.0
    status: str = "pending"
    computed_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    metadata: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self):
        if not self.stats_id:
            self.stats_id = f"RS-{uuid.uuid4().hex[:12]}"


class RecoveryStatisticsEngine:
    """Production recovery statistics engine."""

    def __init__(self):
        self._stats: dict[str, RecoveryStats] = {}
        self._by_book: dict[str, str] = {}

    def record(self, book_uuid: str, book_title: str = "", language: str = "",
               **kwargs) -> RecoveryStats:
        stats = RecoveryStats(
            book_uuid=book_uuid, book_title=book_title,
            language=language, metadata=kwargs.get("metadata", {}))
        for k, v in kwargs.items():
            if k != "metadata" and hasattr(stats, k):
                setattr(stats, k, v)
        if stats.total_paragraphs > 0:
            stats.completeness_pct = (
                (stats.paragraphs_verified + stats.paragraphs_recovered) /
                stats.total_paragraphs * 100)
        self._stats[stats.stats_id] = stats
        self._by_book[book_uuid] = stats.stats_id
        return stats

    def get_stats(self, stats_id: str) -> RecoveryStats | None:
        return self._stats.get(stats_id)

    def get_by_book(self, book_uuid: str) -> RecoveryStats | None:
        sid = self._by_book.get(book_uuid)
        return self._stats.get(sid) if sid else None

    def corpus_summary(self) -> dict:
        all_stats = list(self._stats.values())
        if not all_stats:
            return {"total_books": 0}
        return {
            "total_books": len(all_stats),
            "total_paragraphs": sum(s.total_paragraphs for s in all_stats),
            "total_gaps": sum(s.total_gaps for s in all_stats),
            "gaps_recovered": sum(s.gaps_recovered for s in all_stats),
            "gaps_unknown": sum(s.gaps_unknown for s in all_stats),
            "gaps_conflict": sum(s.gaps_conflict for s in all_stats),
            "editions_discovered": sum(s.editions_discovered for s in all_stats),
            "translations_found": sum(s.translations_found for s in all_stats),
            "commentaries_found": sum(s.commentaries_found for s in all_stats),
            "evidence_collected": sum(s.evidence_collected for s in all_stats),
            "variants_created": sum(s.variants_created for s in all_stats),
            "mean_completeness": round(
                sum(s.completeness_pct for s in all_stats) / len(all_stats), 2),
            "books_complete": sum(1 for s in all_stats if s.completeness_pct >= 95),
            "books_partial": sum(1 for s in all_stats if 50 <= s.completeness_pct < 95),
            "books_low": sum(1 for s in all_stats if s.completeness_pct < 50),
        }

    def count(self) -> int:
        return len(self._stats)
