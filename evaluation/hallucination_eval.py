"""Hallucination detection evaluator — measures resistance to fabricated claims."""
import json
from pathlib import Path
from dataclasses import dataclass, field

from evaluation.golden_loader import EvalQuestion


@dataclass
class HallucinationResult:
    question_id: str
    query: str
    confidence_score: float = 0.0
    evidence_sources: int = 0
    expected_entities_found: int = 0
    top_match_score: float = 0.0
    correctly_low_confidence: bool = False
    hallucination_detected: bool = False
    passed: bool = False


@dataclass
class HallucinationBenchmark:
    total_adversarial: int = 0
    correctly_rejected: int = 0
    false_positive_rate: float = 0.0
    avg_confidence_on_adversarial: float = 0.0
    avg_evidence_on_adversarial: float = 0.0
    max_confidence_on_adversarial: float = 0.0
    results: list[HallucinationResult] = field(default_factory=list)
    passed: bool = False


CONFIDENCE_MAP = {"low": 0.25, "medium": 0.55, "high": 0.85}
ADVERSARIAL_THRESHOLD = 0.55


class HallucinationEvaluator:
    """Evaluates the system's resistance to hallucination on adversarial queries."""

    def __init__(self, threshold: float = ADVERSARIAL_THRESHOLD):
        self.threshold = threshold

    def evaluate_question(
        self,
        question: EvalQuestion,
        answer_result: dict,
    ) -> HallucinationResult:
        """Score a single adversarial query result."""
        confidence_str = answer_result.get("confidence", "low")
        confidence_num = CONFIDENCE_MAP.get(confidence_str, 0.5)

        evidence_count = len(answer_result.get("evidence", {}).get("sources", []))
        top_match = answer_result.get("top_match_score", 0.0)
        entities_found = len(answer_result.get("entities", []))

        # Adversarial queries should produce LOW confidence
        correctly_low = confidence_num <= self.threshold
        hallucination = not correctly_low and evidence_count > 3
        passed = correctly_low or (confidence_num < 0.6 and evidence_count <= 2)

        return HallucinationResult(
            question_id=question.id,
            query=question.question,
            confidence_score=confidence_num,
            evidence_sources=evidence_count,
            expected_entities_found=entities_found,
            top_match_score=top_match,
            correctly_low_confidence=correctly_low,
            hallucination_detected=hallucination,
            passed=passed,
        )

    def aggregate(
        self, results: list[HallucinationResult]
    ) -> HallucinationBenchmark:
        if not results:
            return HallucinationBenchmark()

        correctly_rejected = sum(1 for r in results if r.correctly_low_confidence)
        avg_conf = sum(r.confidence_score for r in results) / len(results)
        avg_ev = sum(r.evidence_sources for r in results) / len(results)
        max_conf = max(r.confidence_score for r in results)
        false_positives = sum(1 for r in results if r.hallucination_detected)

        return HallucinationBenchmark(
            total_adversarial=len(results),
            correctly_rejected=correctly_rejected,
            false_positive_rate=false_positives / len(results),
            avg_confidence_on_adversarial=avg_conf,
            avg_evidence_on_adversarial=avg_ev,
            max_confidence_on_adversarial=max_conf,
            results=results,
            passed=correctly_rejected == len(results),
        )

    def to_dict(self, benchmark: HallucinationBenchmark) -> dict:
        return {
            "total_adversarial": benchmark.total_adversarial,
            "correctly_rejected": benchmark.correctly_rejected,
            "rejection_rate": round(
                benchmark.correctly_rejected
                / max(benchmark.total_adversarial, 1),
                4,
            ),
            "false_positive_rate": round(benchmark.false_positive_rate, 4),
            "avg_confidence_on_adversarial": round(
                benchmark.avg_confidence_on_adversarial, 4
            ),
            "avg_evidence_on_adversarial": round(
                benchmark.avg_evidence_on_adversarial, 4
            ),
            "max_confidence_on_adversarial": round(
                benchmark.max_confidence_on_adversarial, 4
            ),
            "passed": benchmark.passed,
        }
