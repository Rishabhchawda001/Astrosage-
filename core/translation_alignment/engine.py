"""Translation Alignment — Align texts across languages."""
from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Optional


@dataclass
class TranslationPair:
    pair_id: str = ""
    source_edition_id: str = ""
    target_edition_id: str = ""
    source_language: str = ""
    target_language: str = ""
    segments_aligned: int = 0
    segments_total: int = 0
    confidence: float = 0.0
    translator: str = ""
    metadata: dict[str, Any] = field(default_factory=dict)
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

    def __post_init__(self):
        if not self.pair_id:
            self.pair_id = f"TP-{uuid.uuid4().hex[:12]}"

    @property
    def alignment_ratio(self) -> float:
        return self.segments_aligned / max(self.segments_total, 1)


class TranslationAlignmentEngine:
    def __init__(self):
        self._pairs: dict[str, TranslationPair] = {}
        self._by_source: dict[str, list[str]] = {}

    def align(self, source_edition_id: str, target_edition_id: str, source_lang: str = "", target_lang: str = "", **kwargs) -> TranslationPair:
        pair = TranslationPair(source_edition_id=source_edition_id, target_edition_id=target_edition_id,
                              source_language=source_lang, target_language=target_lang, **kwargs)
        self._pairs[pair.pair_id] = pair
        self._by_source.setdefault(source_edition_id, []).append(pair.pair_id)
        return pair

    def get_pairs(self, edition_id: str) -> list[TranslationPair]:
        ids = self._by_source.get(edition_id, [])
        return [self._pairs[pid] for pid in ids if pid in self._pairs]

    def count(self) -> int:
        return len(self._pairs)

    def summary(self) -> dict:
        lang_pairs: dict[str, int] = {}
        for p in self._pairs.values():
            key = f"{p.source_language}->{p.target_language}"
            lang_pairs[key] = lang_pairs.get(key, 0) + 1
        return {"total": self.count(), "by_language_pair": lang_pairs}
