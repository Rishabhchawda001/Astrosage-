"""Evidence Ranking — Rank evidence by quality, recency, and trust."""
from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Optional


@dataclass
class RankedEvidence:
    rank_id: str = ""
    evidence_id: str = ""
    knowledge_uuid: str = ""
    rank: int = 0
    score: float = 0.0
    source_trust: float = 0.0
    recency: float = 0.0
    edition_quality: float = 0.0
    metadata_completeness: float = 0.0
    ranked_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

    def __post_init__(self):
        if not self.rank_id:
            self.rank_id = f"RE-{uuid.uuid4().hex[:12]}"


class EvidenceRankingEngine:
    def __init__(self):
        self._rankings: dict[str, list[RankedEvidence]] = {}

    def rank(self, knowledge_uuid: str, evidence_items: list[dict[str, Any]]) -> list[RankedEvidence]:
        ranked = []
        for i, item in enumerate(evidence_items):
            score = (item.get("source_trust", 0.5) * 0.4 +
                     item.get("recency", 0.5) * 0.2 +
                     item.get("edition_quality", 0.5) * 0.2 +
                     item.get("metadata_completeness", 0.5) * 0.2)
            ranked.append(RankedEvidence(
                evidence_id=item.get("evidence_id", f"EV-{i}"),
                knowledge_uuid=knowledge_uuid, rank=i + 1,
                score=round(score, 4), **{k: v for k, v in item.items() if isinstance(v, (int, float))}))
        ranked.sort(key=lambda r: r.score, reverse=True)
        for i, r in enumerate(ranked):
            r.rank = i + 1
        self._rankings[knowledge_uuid] = ranked
        return ranked

    def get_ranked(self, knowledge_uuid: str) -> list[RankedEvidence]:
        return self._rankings.get(knowledge_uuid, [])

    def count(self) -> int:
        return sum(len(v) for v in self._rankings.values())

    def summary(self) -> dict:
        return {"total_ranked": self.count(), "knowledge_items": len(self._rankings)}
