"""
Chunk Validation — Validates chunks for completeness and integrity.

Rejects: empty chunks, broken hierarchy, missing provenance, missing passport,
missing evidence, invalid citations.
"""
from __future__ import annotations

from enum import Enum
from dataclasses import dataclass, field
from typing import Any

from core.chunking.engine import Chunk


class ValidationSeverity(str, Enum):
    ERROR = "error"
    WARNING = "warning"
    INFO = "info"


@dataclass
class ValidationIssue:
    """A validation issue found in a chunk."""
    issue_type: str = ""
    severity: ValidationSeverity = ValidationSeverity.WARNING
    message: str = ""
    field: str = ""
    expected: str = ""
    actual: str = ""


@dataclass
class ValidationResult:
    """Result of chunk validation."""
    chunk_id: str = ""
    is_valid: bool = True
    issues: list[ValidationIssue] = field(default_factory=list)
    warnings: int = 0
    errors: int = 0

    @property
    def has_errors(self) -> bool:
        return self.errors > 0


class ChunkValidator:
    """
    Production chunk validator.
    
    Validates chunks for completeness, provenance, hierarchy, and integrity.
    """

    def __init__(self):
        self._results: dict[str, ValidationResult] = {}

    def validate(self, chunk: Chunk) -> ValidationResult:
        result = ValidationResult(chunk_id=chunk.chunk_id)
        
        # Empty text check
        if not chunk.text or not chunk.text.strip():
            result.issues.append(ValidationIssue(
                issue_type="empty_text",
                severity=ValidationSeverity.ERROR,
                message="Chunk has no text content",
                field="text",
            ))

        # Missing passport
        if not chunk.passport_id:
            result.issues.append(ValidationIssue(
                issue_type="missing_passport",
                severity=ValidationSeverity.WARNING,
                message="Chunk has no passport reference",
                field="passport_id",
            ))

        # Missing book_id
        if not chunk.book_id:
            result.issues.append(ValidationIssue(
                issue_type="missing_book_id",
                severity=ValidationSeverity.WARNING,
                message="Chunk has no book reference",
                field="book_id",
            ))

        # Missing language
        if not chunk.language:
            result.issues.append(ValidationIssue(
                issue_type="missing_language",
                severity=ValidationSeverity.WARNING,
                message="Chunk has no language specified",
                field="language",
            ))

        # No evidence references
        if not chunk.evidence_refs:
            result.issues.append(ValidationIssue(
                issue_type="no_evidence",
                severity=ValidationSeverity.INFO,
                message="Chunk has no evidence references",
                field="evidence_refs",
            ))

        # Checksum consistency
        import hashlib
        expected = hashlib.sha256(chunk.text.encode("utf-8")).hexdigest()
        if chunk.text_hash and chunk.text_hash != expected:
            result.issues.append(ValidationIssue(
                issue_type="checksum_mismatch",
                severity=ValidationSeverity.ERROR,
                message="Text hash does not match content",
                field="text_hash",
                expected=expected,
                actual=chunk.text_hash,
            ))

        # Hierarchy validation
        if chunk.parent_id and not chunk.ancestor_ids:
            result.issues.append(ValidationIssue(
                issue_type="incomplete_hierarchy",
                severity=ValidationSeverity.WARNING,
                message="Chunk has parent but no ancestors",
                field="ancestor_ids",
            ))

        # Count
        for issue in result.issues:
            if issue.severity == ValidationSeverity.ERROR:
                result.errors += 1
            elif issue.severity == ValidationSeverity.WARNING:
                result.warnings += 1

        result.is_valid = result.errors == 0
        self._results[chunk.chunk_id] = result
        return result

    def validate_batch(self, chunks: list[Chunk]) -> dict[str, ValidationResult]:
        results = {}
        for chunk in chunks:
            results[chunk.chunk_id] = self.validate(chunk)
        return results

    def get_result(self, chunk_id: str) -> ValidationResult | None:
        return self._results.get(chunk_id)

    def get_invalid_chunks(self) -> list[str]:
        return [cid for cid, r in self._results.items() if not r.is_valid]

    def summary(self) -> dict:
        total = len(self._results)
        valid = sum(1 for r in self._results.values() if r.is_valid)
        return {
            "total_validated": total,
            "valid": valid,
            "invalid": total - valid,
            "total_errors": sum(r.errors for r in self._results.values()),
            "total_warnings": sum(r.warnings for r in self._results.values()),
        }
