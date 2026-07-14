"""Source Scoring — Trust and quality scoring for sources."""
from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Optional


class TrustLevel(str, Enum):
    AUTHORITATIVE = "authoritative"
    RELIABLE = "reliable"
    MODERATE = "moderate"
    LOW = "low"
    UNTRUSTED = "untrusted"


@dataclass
class SourceScore:
    score_id: str = ""
    source_id: str = ""
    trust_score: float = 0.0
    trust_level: TrustLevel = TrustLevel.MODERATE
    publisher_reputation: float = 0.0
    academic_authority: float = 0.0
    government_authority: float = 0.0
    historical_authenticity: float = 0.0
    edition_quality: float = 0.0
    metadata_completeness: float = 0.0
    cross_source_agreement: float = 0.0
    human_verified: bool = False
    scored_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

    def __post_init__(self):
        if not self.score_id:
            self.score_id = f"SS-{uuid.uuid4().hex[:12]}"


class SourceScoringEngine:
    def __init__(self):
        self._scores: dict[str, SourceScore] = {}
        self._by_source: dict[str, str] = {}

    def score(self, source_id: str, **kwargs) -> SourceScore:
        factors = {k: v for k, v in kwargs.items() if isinstance(v, (int, float))}
        weights = {"publisher_reputation": 0.15, "academic_authority": 0.2, "government_authority": 0.1,
                   "historical_authenticity": 0.15, "edition_quality": 0.15, "metadata_completeness": 0.1,
                   "cross_source_agreement": 0.15}
        trust = sum(factors.get(k, 0) * w for k, w in weights.items())
        if trust >= 0.8: level = TrustLevel.AUTHORITATIVE
        elif trust >= 0.6: level = TrustLevel.RELIABLE
        elif trust >= 0.4: level = TrustLevel.MODERATE
        elif trust >= 0.2: level = TrustLevel.LOW
        else: level = TrustLevel.UNTRUSTED
        score = SourceScore(source_id=source_id, trust_score=round(trust, 4), trust_level=level, **{k: v for k, v in kwargs.items() if isinstance(v, (int, float))})
        self._scores[score.score_id] = score
        self._by_source[source_id] = score.score_id
        return score

    def get_score(self, source_id: str) -> Optional[SourceScore]:
        sid = self._by_source.get(source_id)
        return self._scores.get(sid) if sid else None

    def count(self) -> int:
        return len(self._scores)

    def summary(self) -> dict:
        scores = [s.trust_score for s in self._scores.values()]
        return {"total": self.count(), "avg_trust": sum(scores) / max(len(scores), 1)}
