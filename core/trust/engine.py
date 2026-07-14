"""
Trust Engine — Configurable trust scoring for knowledge objects.

Tracks: Verified, Pending, Rejected, Conflicted, Recovered, Original,
Human Approved states. Everything configurable.
"""
from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Optional


class TrustLevel(str, Enum):
    VERIFIED = "verified"
    PENDING = "pending"
    REJECTED = "rejected"
    CONFLICTED = "conflicted"
    RECOVERED = "recovered"
    ORIGINAL = "original"
    HUMAN_APPROVED = "human_approved"
    HIGH_CONFIDENCE = "high_confidence"
    LOW_CONFIDENCE = "low_confidence"
    DEFERRED = "deferred"


@dataclass
class TrustFactor:
    """A factor contributing to the overall trust score."""
    factor_id: str = ""
    name: str = ""
    score: float = 0.0  # 0.0 to 1.0
    weight: float = 1.0
    category: str = ""
    metadata: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self):
        if not self.factor_id:
            self.factor_id = f"TF-{uuid.uuid4().hex[:12]}"


@dataclass
class TrustLevelThresholds:
    """Configuration for trust level assignment based on score."""
    verified: float = 0.9
    human_approved: float = 0.95
    high_confidence: float = 0.75
    recovered: float = 0.6
    conflicted: float = 0.3
    low_confidence: float = 0.15

    def get_level(self, score: float) -> TrustLevel:
        if score >= self.human_approved:
            return TrustLevel.HUMAN_APPROVED
        if score >= self.verified:
            return TrustLevel.VERIFIED
        if score >= self.high_confidence:
            return TrustLevel.HIGH_CONFIDENCE
        if score >= self.recovered:
            return TrustLevel.RECOVERED
        if score >= self.low_confidence:
            return TrustLevel.LOW_CONFIDENCE
        return TrustLevel.PENDING


DEFAULT_TRUST_FACTORS = {
    "source_reliability": 0.20,
    "ocr_quality": 0.15,
    "verification_result": 0.15,
    "cross_edition_agreement": 0.10,
    "metadata_completeness": 0.10,
    "confidence_score": 0.10,
    "recovery_quality": 0.10,
    "human_review": 0.10,
}


@dataclass
class TrustResult:
    """Complete trust evaluation for a knowledge unit."""
    knowledge_uuid: str = ""
    trust_score: float = 0.0
    trust_level: TrustLevel = TrustLevel.PENDING
    factors: list[TrustFactor] = field(default_factory=list)
    level_history: list[dict[str, Any]] = field(default_factory=list)
    evaluated_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    evaluation_version: str = "1.0.0"

    def to_dict(self) -> dict[str, Any]:
        return {
            "knowledge_uuid": self.knowledge_uuid,
            "trust_score": self.trust_score,
            "trust_level": self.trust_level.value,
            "factor_count": len(self.factors),
            "evaluated_at": self.evaluated_at,
        }


class TrustEngine:
    """
    Production trust engine.

    Calculates trust scores from multiple weighted factors.
    Assigns trust levels based on configurable thresholds.
    Tracks trust level history.
    """

    def __init__(self, thresholds: TrustLevelThresholds | None = None):
        self.thresholds = thresholds or TrustLevelThresholds()
        self.factor_weights = dict(DEFAULT_TRUST_FACTORS)
        self._results: dict[str, TrustResult] = {}

    def add_factor(
        self,
        knowledge_uuid: str,
        name: str,
        score: float,
        weight: float | None = None,
        category: str = "",
        metadata: dict | None = None,
    ) -> TrustFactor:
        factor = TrustFactor(
            name=name,
            score=max(0.0, min(1.0, score)),
            weight=weight if weight is not None else self.factor_weights.get(name, 1.0),
            category=category,
            metadata=metadata or {},
        )
        if knowledge_uuid not in self._results:
            self._results[knowledge_uuid] = TrustResult(knowledge_uuid=knowledge_uuid)
        self._results[knowledge_uuid].factors.append(factor)
        return factor

    def evaluate(self, knowledge_uuid: str) -> TrustResult:
        """Evaluate overall trust for a knowledge unit."""
        result = self._results.get(knowledge_uuid)
        if not result:
            result = TrustResult(knowledge_uuid=knowledge_uuid)
            self._results[knowledge_uuid] = result

        if not result.factors:
            result.trust_score = 0.0
            result.trust_level = TrustLevel.PENDING
            return result

        total_weight = sum(f.weight for f in result.factors)
        if total_weight == 0:
            result.trust_score = 0.0
            result.trust_level = TrustLevel.PENDING
            return result

        weighted_sum = sum(f.score * f.weight for f in result.factors)
        result.trust_score = round(weighted_sum / total_weight, 4)
        result.trust_level = self.thresholds.get_level(result.trust_score)

        # Record history
        result.level_history.append({
            "score": result.trust_score,
            "level": result.trust_level.value,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        })
        result.evaluated_at = datetime.now(timezone.utc).isoformat()
        return result

    def get_result(self, knowledge_uuid: str) -> Optional[TrustResult]:
        return self._results.get(knowledge_uuid)

    def get_level(self, knowledge_uuid: str) -> TrustLevel:
        result = self._results.get(knowledge_uuid)
        if not result:
            return TrustLevel.PENDING
        return result.trust_level

    def get_factors(self, knowledge_uuid: str) -> list[TrustFactor]:
        result = self._results.get(knowledge_uuid)
        if not result:
            return []
        return result.factors

    def list_by_level(self, level: TrustLevel) -> list[TrustResult]:
        return [r for r in self._results.values() if r.trust_level == level]

    def summary(self) -> dict:
        level_counts: dict[str, int] = {}
        scores = []
        for r in self._results.values():
            level_counts[r.trust_level.value] = level_counts.get(r.trust_level.value, 0) + 1
            scores.append(r.trust_score)
        return {
            "total_items": len(self._results),
            "avg_trust": sum(scores) / max(len(scores), 1),
            "by_level": level_counts,
        }
