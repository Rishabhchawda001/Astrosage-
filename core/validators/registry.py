"""
Validator Registry — Dynamic validator management.

Validators are generic, dynamically registered, and support
architecture, code quality, testing, knowledge, performance,
security, git, dependency, documentation, and constitution checks.
"""
from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Callable, Optional


class ValidationCategory(str, Enum):
    ARCHITECTURE = "architecture"
    CODE_QUALITY = "code_quality"
    TESTING = "testing"
    KNOWLEDGE = "knowledge"
    PERFORMANCE = "performance"
    SECURITY = "security"
    GIT = "git"
    DEPENDENCY = "dependency"
    DOCUMENTATION = "documentation"
    CONSTITUTION = "constitution"


class ValidationResult(str, Enum):
    PASSED = "passed"
    FAILED = "failed"
    SKIPPED = "skipped"
    WARNING = "warning"


@dataclass
class ValidationReport:
    report_id: str = ""
    validator_id: str = ""
    category: ValidationCategory = ValidationCategory.CODE_QUALITY
    result: ValidationResult = ValidationResult.SKIPPED
    message: str = ""
    details: dict[str, Any] = field(default_factory=dict)
    timestamp: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

    def __post_init__(self):
        if not self.report_id:
            self.report_id = f"VR-{uuid.uuid4().hex[:12]}"


@dataclass
class Validator:
    validator_id: str = ""
    name: str = ""
    category: ValidationCategory = ValidationCategory.CODE_QUALITY
    enabled: bool = True
    priority: int = 0
    validate_fn: Optional[Callable] = None
    metadata: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self):
        if not self.validator_id:
            self.validator_id = f"VD-{uuid.uuid4().hex[:12]}"


class ValidatorRegistry:
    """Dynamic validator registry with category-based lookup."""

    def __init__(self):
        self._validators: dict[str, Validator] = {}
        self._reports: dict[str, list[ValidationReport]] = {}

    def register(self, validator: Validator) -> str:
        self._validators[validator.validator_id] = validator
        return validator.validator_id

    def unregister(self, validator_id: str) -> bool:
        return self._validators.pop(validator_id, None) is not None

    def get(self, validator_id: str) -> Optional[Validator]:
        return self._validators.get(validator_id)

    def get_by_category(self, category: ValidationCategory) -> list[Validator]:
        return [v for v in self._validators.values() if v.category == category and v.enabled]

    def get_all_enabled(self) -> list[Validator]:
        return [v for v in self._validators.values() if v.enabled]

    def run_validator(self, validator_id: str, context: dict | None = None) -> ValidationReport:
        validator = self._validators.get(validator_id)
        if not validator:
            return ValidationReport(
                validator_id=validator_id,
                result=ValidationResult.FAILED,
                message="Validator not found",
            )
        if not validator.enabled:
            return ValidationReport(
                validator_id=validator_id,
                category=validator.category,
                result=ValidationResult.SKIPPED,
                message="Validator disabled",
            )
        if validator.validate_fn:
            try:
                result = validator.validate_fn(context or {})
                report = ValidationReport(
                    validator_id=validator_id,
                    category=validator.category,
                    result=ValidationResult.PASSED if result else ValidationResult.FAILED,
                )
            except Exception as e:
                report = ValidationReport(
                    validator_id=validator_id,
                    category=validator.category,
                    result=ValidationResult.FAILED,
                    message=str(e),
                )
        else:
            report = ValidationReport(
                validator_id=validator_id,
                category=validator.category,
                result=ValidationResult.PASSED,
                message="No validation function — passed by default",
            )
        self._reports.setdefault(validator_id, []).append(report)
        return report

    def run_all(self, context: dict | None = None) -> dict[str, ValidationReport]:
        results = {}
        for vid in self._validators:
            results[vid] = self.run_validator(vid, context)
        return results

    def all_passed(self, results: dict[str, ValidationReport]) -> bool:
        return all(r.result == ValidationResult.PASSED for r in results.values() if r.result != ValidationResult.SKIPPED)

    def count(self) -> int:
        return len(self._validators)

    def summary(self) -> dict:
        cat_counts: dict[str, int] = {}
        for v in self._validators.values():
            cat_counts[v.category.value] = cat_counts.get(v.category.value, 0) + 1
        return {
            "total_validators": self.count(),
            "by_category": cat_counts,
        }
