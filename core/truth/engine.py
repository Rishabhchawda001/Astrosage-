"""
Truth Decision Engine — Accept, Reject, Needs Review, or Unknown.

Every decision includes explanation. Never silently resolve.
"""
from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Optional


class TruthDecision(str, Enum):
    ACCEPTED = "accepted"
    REJECTED = "rejected"
    NEEDS_REVIEW = "needs_review"
    UNKNOWN = "unknown"


@dataclass
class TruthVerdict:
    verdict_id: str = ""
    knowledge_uuid: str = ""
    decision: TruthDecision = TruthDecision.UNKNOWN
    confidence: float = 0.0
    explanation: str = ""
    evidence_count: int = 0
    source_count: int = 0
    edition_count: int = 0
    conflict_count: int = 0
    reviewer: str = "system"
    decided_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    metadata: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self):
        if not self.verdict_id:
            self.verdict_id = f"TV-{uuid.uuid4().hex[:12]}"


class TruthEngine:
    """Production truth decision engine."""

    def __init__(self, auto_accept_threshold: float = 0.85, auto_review_threshold: float = 0.5):
        self.auto_accept_threshold = auto_accept_threshold
        self.auto_review_threshold = auto_review_threshold
        self._verdicts: dict[str, TruthVerdict] = {}
        self._by_knowledge: dict[str, str] = {}

    def decide(self, knowledge_uuid: str, confidence: float, evidence_count: int = 0,
               source_count: int = 0, edition_count: int = 0, conflict_count: int = 0,
               explanation: str = "") -> TruthVerdict:
        if conflict_count > 0:
            decision = TruthDecision.NEEDS_REVIEW
            explanation = explanation or f"{conflict_count} conflicts detected"
        elif confidence >= self.auto_accept_threshold and evidence_count >= 2:
            decision = TruthDecision.ACCEPTED
            explanation = explanation or f"High confidence ({confidence:.2f}) with {evidence_count} evidence sources"
        elif confidence >= self.auto_review_threshold:
            decision = TruthDecision.NEEDS_REVIEW
            explanation = explanation or f"Moderate confidence ({confidence:.2f}) requires review"
        else:
            decision = TruthDecision.UNKNOWN
            explanation = explanation or f"Low confidence ({confidence:.2f}) with insufficient evidence"

        verdict = TruthVerdict(
            knowledge_uuid=knowledge_uuid, decision=decision, confidence=confidence,
            explanation=explanation, evidence_count=evidence_count, source_count=source_count,
            edition_count=edition_count, conflict_count=conflict_count)
        self._verdicts[verdict.verdict_id] = verdict
        self._by_knowledge[knowledge_uuid] = verdict.verdict_id
        return verdict

    def get_verdict(self, knowledge_uuid: str) -> Optional[TruthVerdict]:
        vid = self._by_knowledge.get(knowledge_uuid)
        return self._verdicts.get(vid) if vid else None

    def get_by_decision(self, decision: TruthDecision) -> list[TruthVerdict]:
        return [v for v in self._verdicts.values() if v.decision == decision]

    def count(self) -> int: return len(self._verdicts)

    def summary(self) -> dict:
        dc: dict[str, int] = {}
        for v in self._verdicts.values(): dc[v.decision.value] = dc.get(v.decision.value, 0) + 1
        return {"total": self.count(), "by_decision": dc}
