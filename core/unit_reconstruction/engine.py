"""Unit Reconstruction — Recover individual atomic units."""
from __future__ import annotations
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any

class RecoveryStatus(str, Enum):
    CANDIDATE = "candidate"
    VERIFIED = "verified"
    REJECTED = "rejected"
    UNKNOWN = "unknown"

@dataclass
class UnitRecovery:
    recovery_id: str = ""
    unit_id: str = ""
    original_text: str = ""
    recovered_text: str = ""
    confidence: float = 0.0
    sources: list[str] = field(default_factory=list)
    edition_ids: list[str] = field(default_factory=list)
    matching_score: float = 0.0
    reason: str = ""
    status: RecoveryStatus = RecoveryStatus.CANDIDATE
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    verified_at: str = ""
    metadata: dict[str, Any] = field(default_factory=dict)
    def __post_init__(self):
        if not self.recovery_id:
            self.recovery_id = f"UR-{uuid.uuid4().hex[:12]}"

class UnitReconstructionEngine:
    def __init__(self, min_evidence: int = 2, min_confidence: float = 0.6):
        self.min_evidence = min_evidence
        self.min_confidence = min_confidence
        self._recoveries: dict[str, UnitRecovery] = {}
        self._by_unit: dict[str, list[str]] = {}

    def create_candidate(self, unit_id: str, original_text: str = "",
                         recovered_text: str = "", confidence: float = 0.0,
                         sources: list[str] | None = None, **kwargs) -> UnitRecovery:
        r = UnitRecovery(unit_id=unit_id, original_text=original_text,
                         recovered_text=recovered_text, confidence=confidence,
                         sources=sources or [],
                         status=RecoveryStatus.CANDIDATE if confidence >= self.min_confidence else RecoveryStatus.UNKNOWN,
                         **kwargs)
        self._recoveries[r.recovery_id] = r
        self._by_unit.setdefault(unit_id, []).append(r.recovery_id)
        return r

    def verify(self, recovery_id: str, verified: bool, reason: str = "") -> bool:
        r = self._recoveries.get(recovery_id)
        if r:
            r.status = RecoveryStatus.VERIFIED if verified else RecoveryStatus.REJECTED
            r.verified_at = datetime.now(timezone.utc).isoformat()
            if reason:
                r.reason = reason
            return True
        return False

    def get_by_unit(self, unit_id: str) -> list[UnitRecovery]:
        ids = self._by_unit.get(unit_id, [])
        return [self._recoveries[rid] for rid in ids if rid in self._recoveries]

    def count(self) -> int:
        return len(self._recoveries)

    def summary(self) -> dict:
        sc: dict[str, int] = {}
        for r in self._recoveries.values():
            sc[r.status.value] = sc.get(r.status.value, 0) + 1
        return {"total": self.count(), "by_status": sc}
