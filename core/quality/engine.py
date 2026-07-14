"""
Quality Metrics Engine.

Measures OCR completeness, reconstruction %, truth %, citation %,
evidence coverage, edition coverage, language coverage, and confidence
distribution across the corpus.
"""
from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any


@dataclass
class QualityScore:
    score_id: str = ""
    scope: str = ""  # book, chapter, page, paragraph, corpus
    scope_id: str = ""
    ocr_completeness: float = 0.0
    reconstruction_pct: float = 0.0
    truth_pct: float = 0.0
    citation_pct: float = 0.0
    evidence_coverage: float = 0.0
    edition_coverage: float = 0.0
    language_coverage: float = 0.0
    confidence_mean: float = 0.0
    confidence_min: float = 0.0
    confidence_max: float = 0.0
    trust_mean: float = 0.0
    conflict_count: int = 0
    total_paragraphs: int = 0
    verified_paragraphs: int = 0
    canonical_paragraphs: int = 0
    unknown_paragraphs: int = 0
    overall_score: float = 0.0
    computed_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    metadata: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self):
        if not self.score_id:
            self.score_id = f"QS-{uuid.uuid4().hex[:12]}"


class QualityEngine:
    """Production quality metrics engine."""

    _DEFAULT_WEIGHTS: dict[str, float] = {
        "ocr_completeness": 0.15,
        "reconstruction_pct": 0.15,
        "truth_pct": 0.20,
        "citation_pct": 0.10,
        "evidence_coverage": 0.15,
        "edition_coverage": 0.10,
        "language_coverage": 0.05,
        "confidence_mean": 0.10,
    }

    def __init__(self, weights: dict[str, float] | None = None):
        self._weights = {**self._DEFAULT_WEIGHTS}
        if weights:
            self._weights.update(weights)
        self._scores: dict[str, QualityScore] = {}
        self._by_scope: dict[str, list[str]] = {}

    def compute(self, scope: str, scope_id: str, *,
                total_paragraphs: int = 0, verified_paragraphs: int = 0,
                canonical_paragraphs: int = 0, unknown_paragraphs: int = 0,
                ocr_completeness: float = 0.0, reconstruction_pct: float = 0.0,
                citation_pct: float = 0.0, evidence_coverage: float = 0.0,
                edition_coverage: float = 0.0, language_coverage: float = 0.0,
                confidence_values: list[float] | None = None,
                trust_values: list[float] | None = None,
                conflict_count: int = 0, **kwargs) -> QualityScore:
        conf_vals = confidence_values or []
        trust_vals = trust_values or []

        truth_pct = (verified_paragraphs / total_paragraphs * 100) if total_paragraphs > 0 else 0.0
        conf_mean = sum(conf_vals) / len(conf_vals) if conf_vals else 0.0
        conf_min = min(conf_vals) if conf_vals else 0.0
        conf_max = max(conf_vals) if conf_vals else 0.0
        trust_mean = sum(trust_vals) / len(trust_vals) if trust_vals else 0.0

        overall = (
            self._weights["ocr_completeness"] * ocr_completeness +
            self._weights["reconstruction_pct"] * reconstruction_pct +
            self._weights["truth_pct"] * truth_pct +
            self._weights["citation_pct"] * citation_pct +
            self._weights["evidence_coverage"] * evidence_coverage +
            self._weights["edition_coverage"] * edition_coverage +
            self._weights["language_coverage"] * language_coverage +
            self._weights["confidence_mean"] * conf_mean
        ) / 100.0

        score = QualityScore(
            scope=scope, scope_id=scope_id,
            ocr_completeness=ocr_completeness, reconstruction_pct=reconstruction_pct,
            truth_pct=truth_pct, citation_pct=citation_pct,
            evidence_coverage=evidence_coverage, edition_coverage=edition_coverage,
            language_coverage=language_coverage, confidence_mean=conf_mean,
            confidence_min=conf_min, confidence_max=conf_max, trust_mean=trust_mean,
            conflict_count=conflict_count, total_paragraphs=total_paragraphs,
            verified_paragraphs=verified_paragraphs, canonical_paragraphs=canonical_paragraphs,
            unknown_paragraphs=unknown_paragraphs, overall_score=overall, metadata=kwargs)
        self._scores[score.score_id] = score
        self._by_scope.setdefault(scope, []).append(score.score_id)
        return score

    def get_score(self, score_id: str) -> QualityScore | None:
        return self._scores.get(score_id)

    def get_by_scope(self, scope: str) -> list[QualityScore]:
        ids = self._by_scope.get(scope, [])
        return [self._scores[sid] for sid in ids if sid in self._scores]

    def corpus_summary(self) -> dict:
        all_scores = list(self._scores.values())
        if not all_scores:
            return {"total_scores": 0, "mean_overall": 0.0}
        means = {
            "ocr_completeness": sum(s.ocr_completeness for s in all_scores) / len(all_scores),
            "truth_pct": sum(s.truth_pct for s in all_scores) / len(all_scores),
            "confidence_mean": sum(s.confidence_mean for s in all_scores) / len(all_scores),
            "overall_score": sum(s.overall_score for s in all_scores) / len(all_scores),
            "total_paragraphs": sum(s.total_paragraphs for s in all_scores),
            "verified_paragraphs": sum(s.verified_paragraphs for s in all_scores),
            "conflict_count": sum(s.conflict_count for s in all_scores),
        }
        return {"total_scores": len(all_scores), **means}

    def count(self) -> int:
        return len(self._scores)
