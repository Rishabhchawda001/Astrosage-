"""
Chunk Quality — Scores chunk quality across multiple dimensions.

Dimensions: completeness, evidence, confidence, structure, metadata,
hierarchy, citation, language, graph connectivity.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Optional

from core.chunking.engine import Chunk


@dataclass
class QualityDimension:
    """A single quality dimension measurement."""
    name: str = ""
    score: float = 0.0  # 0.0 to 1.0
    weight: float = 1.0
    details: dict[str, Any] = field(default_factory=dict)


@dataclass
class QualityResult:
    """Complete quality assessment for a chunk."""
    chunk_id: str = ""
    dimensions: list[QualityDimension] = field(default_factory=list)
    overall_score: float = 0.0
    grade: str = ""  # A, B, C, D, F
    issues: list[str] = field(default_factory=list)

    def compute_overall(self) -> float:
        if not self.dimensions:
            return 0.0
        total_weight = sum(d.weight for d in self.dimensions)
        if total_weight == 0:
            return 0.0
        self.overall_score = round(
            sum(d.score * d.weight for d in self.dimensions) / total_weight, 4
        )
        if self.overall_score >= 0.9:
            self.grade = "A"
        elif self.overall_score >= 0.8:
            self.grade = "B"
        elif self.overall_score >= 0.6:
            self.grade = "C"
        elif self.overall_score >= 0.4:
            self.grade = "D"
        else:
            self.grade = "F"
        return self.overall_score


DEFAULT_WEIGHTS = {
    "completeness": 0.15,
    "evidence": 0.15,
    "confidence": 0.15,
    "structure": 0.10,
    "metadata": 0.10,
    "hierarchy": 0.10,
    "citation": 0.10,
    "language": 0.10,
    "graph_connectivity": 0.05,
}


class ChunkQualityEngine:
    """
    Production chunk quality scoring engine.
    
    Evaluates chunks across 9 quality dimensions.
    """

    def __init__(self, weights: dict[str, float] | None = None):
        self.weights = dict(DEFAULT_WEIGHTS)
        if weights:
            self.weights.update(weights)
        self._results: dict[str, QualityResult] = {}

    def score(self, chunk: Chunk) -> QualityResult:
        result = QualityResult(chunk_id=chunk.chunk_id)

        # Completeness
        completeness = min(1.0, chunk.word_count / 50) if chunk.word_count else 0.0
        result.dimensions.append(QualityDimension(
            name="completeness", score=completeness,
            weight=self.weights.get("completeness", 1.0),
            details={"word_count": chunk.word_count},
        ))

        # Evidence
        evidence = min(1.0, len(chunk.evidence_refs) * 0.25)
        result.dimensions.append(QualityDimension(
            name="evidence", score=evidence,
            weight=self.weights.get("evidence", 1.0),
            details={"evidence_count": len(chunk.evidence_refs)},
        ))

        # Confidence
        result.dimensions.append(QualityDimension(
            name="confidence", score=chunk.confidence,
            weight=self.weights.get("confidence", 1.0),
        ))

        # Structure
        structure = 1.0 if chunk.chunk_type else 0.5
        result.dimensions.append(QualityDimension(
            name="structure", score=structure,
            weight=self.weights.get("structure", 1.0),
            details={"chunk_type": chunk.chunk_type.value},
        ))

        # Metadata
        meta_fields = sum(1 for f in ["book_id", "edition_id", "language", "passport_id"] if getattr(chunk, f, None))
        metadata = meta_fields / 4
        result.dimensions.append(QualityDimension(
            name="metadata", score=metadata,
            weight=self.weights.get("metadata", 1.0),
        ))

        # Hierarchy
        hierarchy = 1.0 if chunk.hierarchy_path else 0.3
        result.dimensions.append(QualityDimension(
            name="hierarchy", score=hierarchy,
            weight=self.weights.get("hierarchy", 1.0),
        ))

        # Citation
        citation = min(1.0, len(chunk.citation_refs) * 0.5)
        result.dimensions.append(QualityDimension(
            name="citation", score=citation,
            weight=self.weights.get("citation", 1.0),
            details={"citation_count": len(chunk.citation_refs)},
        ))

        # Language
        language = 1.0 if chunk.language else 0.0
        result.dimensions.append(QualityDimension(
            name="language", score=language,
            weight=self.weights.get("language", 1.0),
        ))

        # Graph connectivity
        graph = min(1.0, len(chunk.graph_refs) * 0.33)
        result.dimensions.append(QualityDimension(
            name="graph_connectivity", score=graph,
            weight=self.weights.get("graph_connectivity", 1.0),
            details={"graph_refs": len(chunk.graph_refs)},
        ))

        # Issues
        if not chunk.text:
            result.issues.append("empty_text")
        if not chunk.passport_id:
            result.issues.append("missing_passport")
        if not chunk.language:
            result.issues.append("missing_language")
        if not chunk.evidence_refs:
            result.issues.append("no_evidence")

        result.compute_overall()
        self._results[chunk.chunk_id] = result
        return result

    def score_batch(self, chunks: list[Chunk]) -> dict[str, QualityResult]:
        return {c.chunk_id: self.score(c) for c in chunks}

    def get_result(self, chunk_id: str) -> Optional[QualityResult]:
        return self._results.get(chunk_id)

    def get_average_score(self) -> float:
        scores = [r.overall_score for r in self._results.values()]
        return sum(scores) / max(len(scores), 1)

    def get_grade_distribution(self) -> dict[str, int]:
        grades: dict[str, int] = {}
        for r in self._results.values():
            grades[r.grade] = grades.get(r.grade, 0) + 1
        return grades

    def summary(self) -> dict:
        scores = [r.overall_score for r in self._results.values()]
        return {
            "total_scored": len(self._results),
            "avg_score": sum(scores) / max(len(scores), 1),
            "grade_distribution": self.get_grade_distribution(),
        }
