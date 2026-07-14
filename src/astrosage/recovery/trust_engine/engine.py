"""
Trust Engine — Configurable trust scoring for all knowledge artifacts.

Supports:
  - Source Trust: How reliable is the external source?
  - Edition Trust: How faithful is this edition to the original?
  - Metadata Trust: How accurate is the extracted metadata?
  - OCR Trust: How reliable is the OCR output?
  - Recovery Trust: How trustworthy is the recovered text?
  - Verification Trust: How thorough was the verification?

All values configurable. No hardcoded thresholds.
"""
from __future__ import annotations

import json
from dataclasses import dataclass, field, asdict
from enum import Enum
from pathlib import Path
from typing import Optional


class TrustCategory(str, Enum):
    SOURCE = "source"
    EDITION = "edition"
    METADATA = "metadata"
    OCR = "ocr"
    RECOVERY = "recovery"
    VERIFICATION = "verification"
    OVERALL = "overall"


@dataclass
class TrustScore:
    category: TrustCategory
    score: float  # 0.0 to 1.0
    confidence: float  # 0.0 to 1.0 — how confident are we in this score
    factors: dict = field(default_factory=dict)  # individual factor scores
    explanation: str = ""
    timestamp: str = ""

    def __post_init__(self):
        self.score = max(0.0, min(1.0, self.score))
        self.confidence = max(0.0, min(1.0, self.confidence))


@dataclass
class TrustConfiguration:
    """Configurable weights and thresholds for trust scoring."""
    source_weights: dict = field(default_factory=lambda: {
        "license_verified": 0.3,
        "api_reliability": 0.2,
        "community_reputation": 0.2,
        "data_freshness": 0.15,
        "metadata_completeness": 0.15,
    })
    edition_weights: dict = field(default_factory=lambda: {
        "publisher_reputation": 0.3,
        "scholarly_citations": 0.3,
        "edition_recency": 0.2,
        "cross_reference_agreement": 0.2,
    })
    ocr_weights: dict = field(default_factory=lambda: {
        "character_confidence": 0.4,
        "word_confidence": 0.3,
        "language_model_match": 0.2,
        "layout_preservation": 0.1,
    })
    recovery_weights: dict = field(default_factory=lambda: {
        "source_agreement": 0.4,
        "edition_count": 0.25,
        "character_level_match": 0.2,
        "human_review": 0.15,
    })
    verification_weights: dict = field(default_factory=lambda: {
        "cross_source_agreement": 0.35,
        "character_accuracy": 0.3,
        "human_verification": 0.2,
        "automated_checks": 0.15,
    })
    # Thresholds
    min_trust_for_auto_accept: float = 0.8
    min_trust_for_manual_review: float = 0.5
    min_confidence_threshold: float = 0.3


class TrustEngine:
    """
    Configurable trust scoring engine.

    All weights and thresholds are loaded from configuration.
    No hardcoded values in scoring logic.
    """

    def __init__(self, config_path: Optional[str] = None):
        self.config = TrustConfiguration()
        if config_path:
            self._load_config(config_path)

    def _load_config(self, path: str):
        filepath = Path(path)
        if filepath.exists():
            with open(filepath, "r") as f:
                data = json.load(f)
            if "source_weights" in data:
                self.config.source_weights = data["source_weights"]
            if "edition_weights" in data:
                self.config.edition_weights = data["edition_weights"]
            if "ocr_weights" in data:
                self.config.ocr_weights = data["ocr_weights"]
            if "recovery_weights" in data:
                self.config.recovery_weights = data["recovery_weights"]
            if "verification_weights" in data:
                self.config.verification_weights = data["verification_weights"]
            if "min_trust_for_auto_accept" in data:
                self.config.min_trust_for_auto_accept = data["min_trust_for_auto_accept"]
            if "min_trust_for_manual_review" in data:
                self.config.min_trust_for_manual_review = data["min_trust_for_manual_review"]
            if "min_confidence_threshold" in data:
                self.config.min_confidence_threshold = data["min_confidence_threshold"]

    def _weighted_score(self, factors: dict, weights: dict) -> float:
        """Compute weighted score from factor dict and weight dict."""
        total_weight = 0.0
        total_score = 0.0
        for key, weight in weights.items():
            if key in factors:
                total_score += factors[key] * weight
                total_weight += weight
        if total_weight == 0:
            return 0.0
        return total_score / total_weight

    def score_source(self, factors: dict) -> TrustScore:
        """Score source trust based on provided factors."""
        score = self._weighted_score(factors, self.config.source_weights)
        confidence = sum(factors.values()) / max(1, len(factors))
        return TrustScore(
            category=TrustCategory.SOURCE,
            score=score,
            confidence=confidence,
            factors=factors,
            explanation=f"Source trust: {score:.2f} from {len(factors)} factors",
        )

    def score_edition(self, factors: dict) -> TrustScore:
        score = self._weighted_score(factors, self.config.edition_weights)
        confidence = sum(factors.values()) / max(1, len(factors))
        return TrustScore(
            category=TrustCategory.EDITION,
            score=score,
            confidence=confidence,
            factors=factors,
            explanation=f"Edition trust: {score:.2f} from {len(factors)} factors",
        )

    def score_ocr(self, factors: dict) -> TrustScore:
        score = self._weighted_score(factors, self.config.ocr_weights)
        confidence = sum(factors.values()) / max(1, len(factors))
        return TrustScore(
            category=TrustCategory.OCR,
            score=score,
            confidence=confidence,
            factors=factors,
            explanation=f"OCR trust: {score:.2f} from {len(factors)} factors",
        )

    def score_recovery(self, factors: dict) -> TrustScore:
        score = self._weighted_score(factors, self.config.recovery_weights)
        confidence = sum(factors.values()) / max(1, len(factors))
        return TrustScore(
            category=TrustCategory.RECOVERY,
            score=score,
            confidence=confidence,
            factors=factors,
            explanation=f"Recovery trust: {score:.2f} from {len(factors)} factors",
        )

    def score_verification(self, factors: dict) -> TrustScore:
        score = self._weighted_score(factors, self.config.verification_weights)
        confidence = sum(factors.values()) / max(1, len(factors))
        return TrustScore(
            category=TrustCategory.VERIFICATION,
            score=score,
            confidence=confidence,
            factors=factors,
            explanation=f"Verification trust: {score:.2f} from {len(factors)} factors",
        )

    def compute_overall(self, scores: list[TrustScore]) -> TrustScore:
        """Compute overall trust from component scores."""
        if not scores:
            return TrustScore(
                category=TrustCategory.OVERALL,
                score=0.0,
                confidence=0.0,
                explanation="No component scores provided",
            )
        avg_score = sum(s.score for s in scores) / len(scores)
        avg_confidence = sum(s.confidence for s in scores) / len(scores)
        return TrustScore(
            category=TrustCategory.OVERALL,
            score=avg_score,
            confidence=avg_confidence,
            factors={s.category.value: s.score for s in scores},
            explanation=f"Overall trust: {avg_score:.2f} from {len(scores)} components",
        )

    def recommend_action(self, trust: TrustScore) -> str:
        """Recommend an action based on trust score."""
        if trust.score >= self.config.min_trust_for_auto_accept:
            return "auto_accept"
        elif trust.score >= self.config.min_trust_for_manual_review:
            return "manual_review"
        else:
            return "reject"

    def save_config(self, path: str):
        with open(path, "w") as f:
            json.dump(asdict(self.config), f, indent=2)
