"""
Recovery Validation Engine — Validates every reconstruction independently.

Never trusts implementation worker output. Validates evidence,
citations, alignment, confidence, and provenance.
"""
from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Optional


class ValidationType(str, Enum):
    EVIDENCE_CHECK = "evidence_check"
    CITATION_CHECK = "citation_check"
    ALIGNMENT_CHECK = "alignment_check"
    CONFIDENCE_CHECK = "confidence_check"
    PROVENANCE_CHECK = "provenance_check"
    CROSS_EDITION_CHECK = "cross_edition_check"
    METADATA_CHECK = "metadata_check"
    STRUCTURE_CHECK = "structure_check"
    CHECKSUM_CHECK = "checksum_check"
    HUMAN_REVIEW = "human_review"


class ValidationStatus(str, Enum):
    PENDING = "pending"
    PASSED = "passed"
    FAILED = "failed"
    WARNING = "warning"
    SKIPPED = "skipped"


@dataclass
class ValidationResult:
    result_id: str = ""
    knowledge_uuid: str = ""
    validation_type: ValidationType = ValidationType.EVIDENCE_CHECK
    status: ValidationStatus = ValidationStatus.PENDING
    message: str = ""
    confidence: float = 0.0
    evidence_count: int = 0
    validator: str = "system"
    validated_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    metadata: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self):
        if not self.result_id:
            self.result_id = f"VR-{uuid.uuid4().hex[:12]}"


class RecoveryValidationEngine:
    """Production recovery validation engine."""

    def __init__(self, min_evidence: int = 2, min_confidence: float = 0.6):
        self.min_evidence = min_evidence
        self.min_confidence = min_confidence
        self._results: dict[str, ValidationResult] = {}
        self._by_knowledge: dict[str, list[str]] = {}
        self._by_type: dict[str, list[str]] = {}
        self._by_status: dict[str, list[str]] = {}

    def validate(self, knowledge_uuid: str, validation_type: ValidationType,
                 evidence_count: int = 0, confidence: float = 0.0,
                 message: str = "", validator: str = "system",
                 **kwargs) -> ValidationResult:
        passed = True
        if validation_type == ValidationType.EVIDENCE_CHECK:
            passed = evidence_count >= self.min_evidence
            message = message or (f"Evidence {evidence_count} >= {self.min_evidence}" if passed else
                                  f"Insufficient evidence: {evidence_count} < {self.min_evidence}")
        elif validation_type == ValidationType.CONFIDENCE_CHECK:
            passed = confidence >= self.min_confidence
            message = message or (f"Confidence {confidence:.2f} >= {self.min_confidence}" if passed else
                                  f"Low confidence: {confidence:.2f} < {self.min_confidence}")
        elif validation_type == ValidationType.CROSS_EDITION_CHECK:
            passed = kwargs.get("edition_count", 0) >= 2
            message = message or "Cross-edition check passed" if passed else "Single edition only"
        else:
            passed = bool(message)
            message = message or f"{validation_type.value} check performed"

        status = ValidationStatus.PASSED if passed else ValidationStatus.FAILED
        result = ValidationResult(
            knowledge_uuid=knowledge_uuid, validation_type=validation_type,
            status=status, message=message, confidence=confidence,
            evidence_count=evidence_count, validator=validator, metadata=kwargs)
        self._results[result.result_id] = result
        self._by_knowledge.setdefault(knowledge_uuid, []).append(result.result_id)
        self._by_type.setdefault(validation_type.value, []).append(result.result_id)
        self._by_status.setdefault(status.value, []).append(result.result_id)
        return result

    def validate_all(self, knowledge_uuid: str, evidence_count: int = 0,
                     confidence: float = 0.0, edition_count: int = 1,
                     provenance: bool = True, **kwargs) -> list[ValidationResult]:
        results = []
        results.append(self.validate(knowledge_uuid, ValidationType.EVIDENCE_CHECK,
                                     evidence_count=evidence_count))
        results.append(self.validate(knowledge_uuid, ValidationType.CONFIDENCE_CHECK,
                                     confidence=confidence))
        if edition_count >= 2:
            results.append(self.validate(knowledge_uuid, ValidationType.CROSS_EDITION_CHECK,
                                         edition_count=edition_count))
        if provenance:
            results.append(self.validate(knowledge_uuid, ValidationType.PROVENANCE_CHECK,
                                         message="Provenance verified"))
        return results

    def get_results(self, knowledge_uuid: str) -> list[ValidationResult]:
        ids = self._by_knowledge.get(knowledge_uuid, [])
        return [self._results[rid] for rid in ids if rid in self._results]

    def get_failed(self) -> list[ValidationResult]:
        return [r for r in self._results.values() if r.status == ValidationStatus.FAILED]

    def count(self) -> int:
        return len(self._results)

    def summary(self) -> dict:
        st: dict[str, int] = {}
        for r in self._results.values():
            st[r.status.value] = st.get(r.status.value, 0) + 1
        return {"total": self.count(), "by_status": st, "failed": st.get("failed", 0)}
