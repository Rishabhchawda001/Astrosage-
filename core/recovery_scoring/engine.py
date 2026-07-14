"""
Recovery Scoring Engine — Measures knowledge completeness.

Every book receives measurable completeness scores across
multiple dimensions.
"""
from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any


class ScoreComponent(str, Enum):
    KNOWLEDGE_COMPLETENESS = "knowledge_completeness"
    EVIDENCE_COMPLETENESS = "evidence_completeness"
    EDITION_COMPLETENESS = "edition_completeness"
    TRANSLATION_COMPLETENESS = "translation_completeness"
    COMMENTARY_COMPLETENESS = "commentary_completeness"
    CITATION_COMPLETENESS = "citation_completeness"
    CONFIDENCE = "confidence"
    TRUST = "trust"


@dataclass
class RecoveryScore:
    score_id: str = ""
    book_uuid: str = ""
    book_title: str = ""
    knowledge_completeness: float = 0.0
    evidence_completeness: float = 0.0
    edition_completeness: float = 0.0
    translation_completeness: float = 0.0
    commentary_completeness: float = 0.0
    citation_completeness: float = 0.0
    confidence: float = 0.0
    trust: float = 0.0
    recovery_pct: float = 0.0
    overall_score: float = 0.0
    total_paragraphs: int = 0
    verified_paragraphs: int = 0
    recovered_paragraphs: int = 0
    unknown_paragraphs: int = 0
    editions_found: int = 0
    translations_found: int = 0
    commentaries_found: int = 0
    evidence_count: int = 0
    conflict_count: int = 0
    computed_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    metadata: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self):
        if not self.score_id:
            self.score_id = f"RS-{uuid.uuid4().hex[:12]}"


class RecoveryScoringEngine:
    """Production recovery scoring engine."""

    _WEIGHTS: dict[str, float] = {
        "knowledge_completeness": 0.25,
        "evidence_completeness": 0.20,
        "edition_completeness": 0.15,
        "translation_completeness": 0.10,
        "commentary_completeness": 0.10,
        "citation_completeness": 0.05,
        "confidence": 0.10,
        "trust": 0.05,
    }

    def __init__(self, weights: dict[str, float] | None = None):
        self._weights = {**self._WEIGHTS}
        if weights:
            self._weights.update(weights)
        self._scores: dict[str, RecoveryScore] = {}
        self._by_book: dict[str, str] = {}

    def compute(self, book_uuid: str, book_title: str = "",
                total_paragraphs: int = 0, verified_paragraphs: int = 0,
                recovered_paragraphs: int = 0, unknown_paragraphs: int = 0,
                editions_found: int = 0, translations_found: int = 0,
                commentaries_found: int = 0, evidence_count: int = 0,
                conflict_count: int = 0, confidence_values: list[float] | None = None,
                trust_values: list[float] | None = None, **kwargs) -> RecoveryScore:
        conf_vals = confidence_values or []
        trust_vals = trust_values or []
        knowledge_c = (verified_paragraphs / total_paragraphs * 100) if total_paragraphs > 0 else 0.0
        evidence_c = (evidence_count / max(total_paragraphs, 1) * 100) if evidence_count > 0 else 0.0
        edition_c = min(editions_found / 5, 1.0) * 100
        translation_c = min(translations_found / 3, 1.0) * 100
        commentary_c = min(commentaries_found / 2, 1.0) * 100
        citation_c = (evidence_count / max(total_paragraphs, 1) * 100) if evidence_count > 0 else 0.0
        conf_mean = (sum(conf_vals) / len(conf_vals) * 100) if conf_vals else 0.0
        trust_mean = (sum(trust_vals) / len(trust_vals) * 100) if trust_vals else 0.0
        recovery_pct = ((verified_paragraphs + recovered_paragraphs) / total_paragraphs * 100) if total_paragraphs > 0 else 0.0
        overall = (
            self._weights["knowledge_completeness"] * knowledge_c +
            self._weights["evidence_completeness"] * evidence_c +
            self._weights["edition_completeness"] * edition_c +
            self._weights["translation_completeness"] * translation_c +
            self._weights["commentary_completeness"] * commentary_c +
            self._weights["citation_completeness"] * citation_c +
            self._weights["confidence"] * conf_mean +
            self._weights["trust"] * trust_mean
        )
        score = RecoveryScore(
            book_uuid=book_uuid, book_title=book_title,
            knowledge_completeness=knowledge_c, evidence_completeness=evidence_c,
            edition_completeness=edition_c, translation_completeness=translation_c,
            commentary_completeness=commentary_c, citation_completeness=citation_c,
            confidence=conf_mean / 100, trust=trust_mean / 100,
            recovery_pct=recovery_pct, overall_score=overall,
            total_paragraphs=total_paragraphs, verified_paragraphs=verified_paragraphs,
            recovered_paragraphs=recovered_paragraphs, unknown_paragraphs=unknown_paragraphs,
            editions_found=editions_found, translations_found=translations_found,
            commentaries_found=commentaries_found, evidence_count=evidence_count,
            conflict_count=conflict_count, metadata=kwargs)
        self._scores[score.score_id] = score
        self._by_book[book_uuid] = score.score_id
        return score

    def get_score(self, score_id: str) -> RecoveryScore | None:
        return self._scores.get(score_id)

    def get_by_book(self, book_uuid: str) -> RecoveryScore | None:
        sid = self._by_book.get(book_uuid)
        return self._scores.get(sid) if sid else None

    def count(self) -> int:
        return len(self._scores)

    def corpus_summary(self) -> dict:
        if not self._scores:
            return {"total_books_scored": 0, "mean_overall": 0.0}
        all_scores = list(self._scores.values())
        return {
            "total_books_scored": len(all_scores),
            "mean_overall": round(sum(s.overall_score for s in all_scores) / len(all_scores), 2),
            "mean_recovery_pct": round(sum(s.recovery_pct for s in all_scores) / len(all_scores), 2),
            "mean_confidence": round(sum(s.confidence for s in all_scores) / len(all_scores), 2),
            "total_paragraphs": sum(s.total_paragraphs for s in all_scores),
            "total_verified": sum(s.verified_paragraphs for s in all_scores),
            "total_recovered": sum(s.recovered_paragraphs for s in all_scores),
            "total_unknown": sum(s.unknown_paragraphs for s in all_scores),
            "total_conflicts": sum(s.conflict_count for s in all_scores),
        }
