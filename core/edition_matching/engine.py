"""Edition Matching — Match specific editions across sources."""
from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Optional


@dataclass
class EditionMatch:
    match_id: str = ""
    edition_a_id: str = ""
    edition_b_id: str = ""
    confidence: float = 0.0
    match_signals: dict[str, float] = field(default_factory=dict)
    detected_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

    def __post_init__(self):
        if not self.match_id:
            self.match_id = f"EM-{uuid.uuid4().hex[:12]}"


class EditionMatchingEngine:
    def __init__(self):
        self._matches: dict[str, EditionMatch] = {}

    def match(self, edition_a_id: str, edition_b_id: str, signals: dict[str, float] | None = None) -> EditionMatch:
        signals = signals or {}
        confidence = sum(signals.values()) / max(len(signals), 1) if signals else 0.0
        m = EditionMatch(edition_a_id=edition_a_id, edition_b_id=edition_b_id,
                         confidence=round(confidence, 4), match_signals=signals)
        self._matches[m.match_id] = m
        return m

    def count(self) -> int:
        return len(self._matches)

    def summary(self) -> dict:
        return {"total": self.count()}
