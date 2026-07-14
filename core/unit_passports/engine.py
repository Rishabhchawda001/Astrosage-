"""Unit Passports — Knowledge passport for every atomic unit."""
from __future__ import annotations
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any

class PassportStatus(str, Enum):
    PENDING = "pending"
    VERIFIED = "verified"
    APPROVED = "approved"
    REJECTED = "rejected"
    CONFLICTED = "conflicted"
    UNKNOWN = "unknown"
    RECOVERED = "recovered"

@dataclass
class UnitPassport:
    passport_id: str = ""
    unit_id: str = ""
    book_uuid: str = ""
    evidence: list[str] = field(default_factory=list)
    variants: list[str] = field(default_factory=list)
    confidence: float = 0.0
    sources: list[str] = field(default_factory=list)
    editions: list[str] = field(default_factory=list)
    translations: list[str] = field(default_factory=list)
    commentaries: list[str] = field(default_factory=list)
    recovery_status: str = "pending"
    truth_status: str = "pending"
    canonical_status: str = "pending"
    verification_status: PassportStatus = PassportStatus.PENDING
    human_review: bool = False
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    updated_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    metadata: dict[str, Any] = field(default_factory=dict)
    def __post_init__(self):
        if not self.passport_id:
            self.passport_id = f"UP-{uuid.uuid4().hex[:12]}"

class UnitPassportEngine:
    def __init__(self):
        self._passports: dict[str, UnitPassport] = {}
        self._by_unit: dict[str, str] = {}
        self._by_book: dict[str, list[str]] = {}

    def create(self, unit_id: str, book_uuid: str = "", **kwargs) -> UnitPassport:
        p = UnitPassport(unit_id=unit_id, book_uuid=book_uuid, metadata=kwargs)
        self._passports[p.passport_id] = p
        self._by_unit[unit_id] = p.passport_id
        if book_uuid:
            self._by_book.setdefault(book_uuid, []).append(p.passport_id)
        return p

    def get_by_unit(self, unit_id: str) -> UnitPassport | None:
        pid = self._by_unit.get(unit_id)
        return self._passports.get(pid) if pid else None

    def update_evidence(self, unit_id: str, evidence_id: str) -> bool:
        pid = self._by_unit.get(unit_id)
        p = self._passports.get(pid) if pid else None
        if p and evidence_id not in p.evidence:
            p.evidence.append(evidence_id)
            return True
        return False

    def verify(self, unit_id: str, status: PassportStatus, confidence: float = 0.0) -> bool:
        pid = self._by_unit.get(unit_id)
        p = self._passports.get(pid) if pid else None
        if p:
            p.verification_status = status
            if confidence > 0:
                p.confidence = confidence
            p.updated_at = datetime.now(timezone.utc).isoformat()
            return True
        return False

    def count(self) -> int:
        return len(self._passports)

    def summary(self) -> dict:
        vs: dict[str, int] = {}
        for p in self._passports.values():
            vs[p.verification_status.value] = vs.get(p.verification_status.value, 0) + 1
        return {"total": self.count(), "by_status": vs}
