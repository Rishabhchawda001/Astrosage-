"""Book Matching — Identify identical works across sources."""
from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Optional


@dataclass
class BookMatch:
    match_id: str = ""
    edition_a_id: str = ""
    edition_b_id: str = ""
    title_similarity: float = 0.0
    author_similarity: float = 0.0
    metadata_similarity: float = 0.0
    overall_confidence: float = 0.0
    match_type: str = "exact"  # exact, variant, translation, commentary
    metadata: dict[str, Any] = field(default_factory=dict)
    detected_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

    def __post_init__(self):
        if not self.match_id:
            self.match_id = f"BM-{uuid.uuid4().hex[:12]}"


class BookMatchingEngine:
    def __init__(self, confidence_threshold: float = 0.7):
        self.confidence_threshold = confidence_threshold
        self._matches: dict[str, BookMatch] = {}
        self._by_edition: dict[str, list[str]] = {}

    def _text_similarity(self, a: str, b: str) -> float:
        words_a = set(a.lower().split()) if a else set()
        words_b = set(b.lower().split()) if b else set()
        union = words_a | words_b
        return len(words_a & words_b) / len(union) if union else 0.0

    def match(self, edition_a_id: str, edition_b_id: str, title_a: str = "", title_b: str = "",
              author_a: str = "", author_b: str = "", **kwargs) -> BookMatch:
        ts = self._text_similarity(title_a, title_b)
        aus = self._text_similarity(author_a, author_b)
        ms = kwargs.get("metadata_similarity", 0.0)
        overall = (ts * 0.5 + aus * 0.3 + ms * 0.2)
        match_type = "exact" if overall > 0.9 else "variant" if overall > 0.7 else "translation" if overall > 0.4 else "unrelated"
        m = BookMatch(edition_a_id=edition_a_id, edition_b_id=edition_b_id,
                      title_similarity=round(ts, 4), author_similarity=round(aus, 4),
                      metadata_similarity=round(ms, 4), overall_confidence=round(overall, 4),
                      match_type=match_type)
        self._matches[m.match_id] = m
        self._by_edition.setdefault(edition_a_id, []).append(m.match_id)
        self._by_edition.setdefault(edition_b_id, []).append(m.match_id)
        return m

    def get_matches(self, edition_id: str) -> list[BookMatch]:
        ids = self._by_edition.get(edition_id, [])
        return [self._matches[mid] for mid in ids if mid in self._matches]

    def get_confident_matches(self) -> list[BookMatch]:
        return [m for m in self._matches.values() if m.overall_confidence >= self.confidence_threshold]

    def count(self) -> int:
        return len(self._matches)

    def summary(self) -> dict:
        type_counts: dict[str, int] = {}
        for m in self._matches.values():
            type_counts[m.match_type] = type_counts.get(m.match_type, 0) + 1
        return {"total": self.count(), "confident": len(self.get_confident_matches()), "by_type": type_counts}
