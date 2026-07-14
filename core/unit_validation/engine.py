"""Unit Validation — Independent validation of every reconstructed unit."""
from __future__ import annotations
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any

class ValidationStatus(str, Enum):
    PENDING = "pending"
    PASSED = "passed"
    FAILED = "failed"
    WARNING = "warning"

@dataclass
class ValidationRecord:
    record_id: str = ""
    unit_id: str = ""
    validation_type: str = ""
    status: ValidationStatus = ValidationStatus.PENDING
    message: str = ""
    confidence: float = 0.0
    evidence_count: int = 0
    validator: str = "system"
    validated_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    metadata: dict[str, Any] = field(default_factory=dict)
    def __post_init__(self):
        if not self.record_id:
            self.record_id = f"VR-{uuid.uuid4().hex[:12]}"

class UnitValidationEngine:
    def __init__(self, min_evidence: int = 2, min_confidence: float = 0.6):
        self.min_evidence = min_evidence
        self.min_confidence = min_confidence
        self._records: dict[str, ValidationRecord] = {}
        self._by_unit: dict[str, list[str]] = {}
        self._by_status: dict[str, list[str]] = {}

    def validate(self, unit_id: str, validation_type: str,
                 evidence_count: int = 0, confidence: float = 0.0,
                 message: str = "", **kwargs) -> ValidationRecord:
        passed = True
        if validation_type == "evidence":
            passed = evidence_count >= self.min_evidence
        elif validation_type == "confidence":
            passed = confidence >= self.min_confidence
        status = ValidationStatus.PASSED if passed else ValidationStatus.FAILED
        r = ValidationRecord(unit_id=unit_id, validation_type=validation_type,
                             status=status, message=message, confidence=confidence,
                             evidence_count=evidence_count, metadata=kwargs)
        self._records[r.record_id] = r
        self._by_unit.setdefault(unit_id, []).append(r.record_id)
        self._by_status.setdefault(status.value, []).append(r.record_id)
        return r

    def get_failed(self) -> list[ValidationRecord]:
        ids = self._by_status.get("failed", [])
        return [self._records[rid] for rid in ids if rid in self._records]

    def count(self) -> int:
        return len(self._records)

    def summary(self) -> dict:
        sc: dict[str, int] = {}
        for r in self._records.values():
            sc[r.status.value] = sc.get(r.status.value, 0) + 1
        return {"total": self.count(), "by_status": sc}
