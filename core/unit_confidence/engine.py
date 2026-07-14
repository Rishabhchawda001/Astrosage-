"""Unit Confidence — Per-unit confidence scoring."""
from __future__ import annotations
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any

@dataclass
class ConfidenceScore:
    score_id: str = ""
    unit_id: str = ""
    evidence_score: float = 0.0
    trust_score: float = 0.0
    agreement_score: float = 0.0
    recovery_confidence: float = 0.0
    translation_confidence: float = 0.0
    canonical_confidence: float = 0.0
    overall_confidence: float = 0.0
    computed_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    metadata: dict[str, Any] = field(default_factory=dict)
    def __post_init__(self):
        if not self.score_id:
            self.score_id = f"CS-{uuid.uuid4().hex[:12]}"

class UnitConfidenceEngine:
    def __init__(self):
        self._scores: dict[str, ConfidenceScore] = {}
        self._by_unit: dict[str, str] = {}

    def compute(self, unit_id: str, evidence_score: float = 0.0,
                trust_score: float = 0.0, agreement_score: float = 0.0,
                recovery_confidence: float = 0.0,
                translation_confidence: float = 0.0,
                canonical_confidence: float = 0.0, **kwargs) -> ConfidenceScore:
        overall = (evidence_score * 0.25 + trust_score * 0.20 + agreement_score * 0.20 +
                   recovery_confidence * 0.15 + translation_confidence * 0.10 +
                   canonical_confidence * 0.10)
        s = ConfidenceScore(unit_id=unit_id, evidence_score=evidence_score,
                            trust_score=trust_score, agreement_score=agreement_score,
                            recovery_confidence=recovery_confidence,
                            translation_confidence=translation_confidence,
                            canonical_confidence=canonical_confidence,
                            overall_confidence=overall, metadata=kwargs)
        self._scores[s.score_id] = s
        self._by_unit[unit_id] = s.score_id
        return s

    def get(self, unit_id: str) -> ConfidenceScore | None:
        sid = self._by_unit.get(unit_id)
        return self._scores.get(sid) if sid else None

    def count(self) -> int:
        return len(self._scores)

    def summary(self) -> dict:
        if not self._scores:
            return {"total": 0, "mean_confidence": 0.0}
        all_s = list(self._scores.values())
        return {"total": len(all_s),
                "mean_confidence": round(sum(s.overall_confidence for s in all_s) / len(all_s), 3)}
