"""
Confidence Engine — Deterministic confidence scoring from weighted evidence.

Supports: OCR quality, source agreement, edition agreement, metadata agreement,
checksum consistency, recovery consistency, citation completeness.
All weights configurable.
"""
from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Optional


@dataclass
class ConfidenceSignal:
    """A single confidence measurement."""
    signal_id: str = ""
    name: str = ""
    score: float = 0.0  # 0.0 to 1.0
    weight: float = 1.0
    source: str = ""
    metadata: dict[str, Any] = field(default_factory=dict)
    timestamp: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

    def __post_init__(self):
        if not self.signal_id:
            self.signal_id = f"CS-{uuid.uuid4().hex[:12]}"


@dataclass
class ConfidenceResult:
    """Result of confidence calculation for a knowledge item."""
    knowledge_uuid: str = ""
    overall_confidence: float = 0.0
    signals: list[ConfidenceSignal] = field(default_factory=list)
    min_signal: str = ""
    max_signal: str = ""
    calculated_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    calculation_version: str = "1.0.0"

    def to_dict(self) -> dict[str, Any]:
        return {
            "knowledge_uuid": self.knowledge_uuid,
            "overall_confidence": self.overall_confidence,
            "signal_count": len(self.signals),
            "min_signal": self.min_signal,
            "max_signal": self.max_signal,
            "calculated_at": self.calculated_at,
        }


DEFAULT_WEIGHTS = {
    "ocr_quality": 0.20,
    "source_agreement": 0.15,
    "edition_agreement": 0.15,
    "metadata_agreement": 0.10,
    "checksum_consistency": 0.10,
    "recovery_consistency": 0.15,
    "citation_completeness": 0.15,
}


class ConfidenceEngine:
    """
    Deterministic confidence scoring engine.

    Calculates weighted confidence from multiple signal sources.
    All weights configurable. Produces deterministic, reproducible scores.
    """

    def __init__(self, weights: dict[str, float] | None = None):
        self.weights = dict(DEFAULT_WEIGHTS)
        if weights:
            self.weights.update(weights)
        self._results: dict[str, ConfidenceResult] = {}

    def add_signal(
        self,
        knowledge_uuid: str,
        name: str,
        score: float,
        weight: float | None = None,
        source: str = "",
        metadata: dict | None = None,
    ) -> ConfidenceSignal:
        """Add a signal to an existing or new result."""
        signal = ConfidenceSignal(
            name=name,
            score=max(0.0, min(1.0, score)),
            weight=weight if weight is not None else self.weights.get(name, 1.0),
            source=source,
            metadata=metadata or {},
        )
        if knowledge_uuid not in self._results:
            self._results[knowledge_uuid] = ConfidenceResult(knowledge_uuid=knowledge_uuid)
        self._results[knowledge_uuid].signals.append(signal)
        return signal

    def calculate(self, knowledge_uuid: str) -> ConfidenceResult:
        """Calculate weighted confidence for a knowledge item."""
        result = self._results.get(knowledge_uuid)
        if not result:
            result = ConfidenceResult(knowledge_uuid=knowledge_uuid)
            self._results[knowledge_uuid] = result

        if not result.signals:
            result.overall_confidence = 0.0
            return result

        total_weight = sum(s.weight for s in result.signals)
        if total_weight == 0:
            result.overall_confidence = 0.0
            return result

        weighted_sum = sum(s.score * s.weight for s in result.signals)
        result.overall_confidence = round(weighted_sum / total_weight, 4)

        scores = {s.name: s.score for s in result.signals}
        result.min_signal = min(scores, key=scores.get) if scores else ""
        result.max_signal = max(scores, key=scores.get) if scores else ""
        result.calculated_at = datetime.now(timezone.utc).isoformat()
        return result

    def get_result(self, knowledge_uuid: str) -> Optional[ConfidenceResult]:
        return self._results.get(knowledge_uuid)

    def get_score(self, knowledge_uuid: str) -> float:
        result = self._results.get(knowledge_uuid)
        if not result or not result.signals:
            return 0.0
        return result.overall_confidence

    def update_weights(self, weights: dict[str, float]) -> None:
        self.weights.update(weights)

    def summary(self) -> dict:
        scores = [r.overall_confidence for r in self._results.values() if r.signals]
        return {
            "total_items": len(self._results),
            "avg_confidence": sum(scores) / max(len(scores), 1),
            "min_confidence": min(scores) if scores else 0.0,
            "max_confidence": max(scores) if scores else 0.0,
            "weights": dict(self.weights),
        }
