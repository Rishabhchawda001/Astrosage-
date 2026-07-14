"""
Verification Interface — Defines how recovery candidates are verified.

Input: OCR text, candidate recovery, evidence
Output: Verified/Rejected/Conflict/Manual Review, confidence, reason

Implementation comes in future phases. This is the contract.
"""
from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import Enum
from typing import Optional


class VerificationResult(str, Enum):
    VERIFIED = "verified"
    REJECTED = "rejected"
    CONFLICT = "conflict"
    MANUAL_REVIEW = "manual_review"


@dataclass
class VerificationInput:
    """Input to the verification process."""
    original_ocr: str
    candidate_text: str
    evidence_texts: list[str] = field(default_factory=list)
    evidence_sources: list[dict] = field(default_factory=list)
    document_uuid: str = ""
    book_uuid: str = ""
    page: int = 0
    language: str = ""
    metadata: dict = field(default_factory=dict)


@dataclass
class VerificationOutput:
    """Output of the verification process."""
    result: VerificationResult
    confidence: float = 0.0
    reason: str = ""
    character_accuracy: float = 0.0
    word_accuracy: float = 0.0
    agreement_score: float = 0.0
    evidence_count: int = 0
    details: dict = field(default_factory=dict)


class VerificationInterface(ABC):
    """
    Abstract interface for verification implementations.

    Every verification engine must implement this interface.
    This allows swapping verification strategies without
    changing the rest of the pipeline.
    """

    @abstractmethod
    def verify(self, input_data: VerificationInput) -> VerificationOutput:
        """Verify a recovery candidate against evidence."""
        ...

    @abstractmethod
    def name(self) -> str:
        """Return the name of this verification engine."""
        ...

    @abstractmethod
    def version(self) -> str:
        """Return the version of this verification engine."""
        ...


class DefaultVerification(VerificationInterface):
    """
    Default verification using character-level comparison.

    Compares original OCR, candidate, and evidence texts
    using character-level accuracy metrics.
    """

    def name(self) -> str:
        return "default_verification"

    def version(self) -> str:
        return "1.0.0"

    def verify(self, input_data: VerificationInput) -> VerificationOutput:
        if not input_data.candidate_text:
            return VerificationOutput(
                result=VerificationResult.REJECTED,
                confidence=0.0,
                reason="No candidate text provided",
            )

        if not input_data.evidence_texts:
            return VerificationOutput(
                result=VerificationResult.MANUAL_REVIEW,
                confidence=0.3,
                reason="No evidence available for comparison",
            )

        # Character-level comparison with evidence
        agreements = 0
        for evidence in input_data.evidence_texts:
            similarity = self._char_similarity(input_data.candidate_text, evidence)
            if similarity > 0.8:
                agreements += 1

        agreement_rate = agreements / len(input_data.evidence_texts) if input_data.evidence_texts else 0
        char_accuracy = self._char_similarity(input_data.original_ocr, input_data.candidate_text)

        # Determine result
        if agreement_rate >= 0.7 and char_accuracy > 0.5:
            result = VerificationResult.VERIFIED
            confidence = min(1.0, (agreement_rate + char_accuracy) / 2)
            reason = f"Strong agreement across {agreements}/{len(input_data.evidence_texts)} sources"
        elif agreement_rate < 0.3:
            result = VerificationResult.REJECTED
            confidence = 1.0 - agreement_rate
            reason = f"Low agreement: {agreement_rate:.1%} across evidence sources"
        else:
            result = VerificationResult.CONFLICT
            confidence = 0.5
            reason = f"Partial agreement: {agreement_rate:.1%} — conflicting evidence"

        return VerificationOutput(
            result=result,
            confidence=confidence,
            reason=reason,
            character_accuracy=char_accuracy,
            word_accuracy=self._word_similarity(input_data.original_ocr, input_data.candidate_text),
            agreement_score=agreement_rate,
            evidence_count=len(input_data.evidence_texts),
        )

    def _char_similarity(self, a: str, b: str) -> float:
        """Simple character-level Jaccard similarity."""
        if not a or not b:
            return 0.0
        set_a = set(a)
        set_b = set(b)
        intersection = set_a & set_b
        union = set_a | set_b
        return len(intersection) / len(union) if union else 0.0

    def _word_similarity(self, a: str, b: str) -> float:
        """Simple word-level Jaccard similarity."""
        words_a = set(a.split())
        words_b = set(b.split())
        if not words_a or not words_b:
            return 0.0
        intersection = words_a & words_b
        union = words_a | words_b
        return len(intersection) / len(union) if union else 0.0
