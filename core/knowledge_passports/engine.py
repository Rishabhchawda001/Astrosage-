"""
Knowledge Passport Engine — Permanent passport for every knowledge unit.

Every logical knowledge unit receives a permanent passport storing
UUIDs, sources, evidence, confidence, verification status, conflicts,
versions, checksums, and human review flags.
"""
from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Optional


class PassportStatus(str, Enum):
    PENDING = "pending"
    VERIFIED = "verified"
    APPROVED = "approved"
    REJECTED = "rejected"
    CONFLICTED = "conflicted"
    UNKNOWN = "unknown"


@dataclass
class KnowledgePassport:
    passport_id: str = ""
    knowledge_uuid: str = ""
    book_uuid: str = ""
    edition_uuid: str = ""
    language: str = ""
    original_source: str = ""
    recovered_sources: list[str] = field(default_factory=list)
    evidence_count: int = 0
    evidence_ids: list[str] = field(default_factory=list)
    confidence: float = 0.0
    verification_status: PassportStatus = PassportStatus.PENDING
    approval_status: PassportStatus = PassportStatus.PENDING
    conflicts: list[dict[str, Any]] = field(default_factory=list)
    versions: list[str] = field(default_factory=list)
    checksums: list[str] = field(default_factory=list)
    last_verified: str = ""
    human_review_flag: bool = False
    human_review_notes: str = ""
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    updated_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    metadata: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self):
        if not self.passport_id:
            self.passport_id = f"PP-{uuid.uuid4().hex[:12]}"


class KnowledgePassportEngine:
    """Production knowledge passport engine."""

    def __init__(self):
        self._passports: dict[str, KnowledgePassport] = {}
        self._by_knowledge: dict[str, str] = {}
        self._by_book: dict[str, list[str]] = {}

    def create(self, knowledge_uuid: str, book_uuid: str = "",
               edition_uuid: str = "", language: str = "",
               original_source: str = "", **kwargs) -> KnowledgePassport:
        passport = KnowledgePassport(
            knowledge_uuid=knowledge_uuid, book_uuid=book_uuid,
            edition_uuid=edition_uuid, language=language,
            original_source=original_source, metadata=kwargs)
        self._passports[passport.passport_id] = passport
        self._by_knowledge[knowledge_uuid] = passport.passport_id
        if book_uuid:
            self._by_book.setdefault(book_uuid, []).append(passport.passport_id)
        return passport

    def get(self, passport_id: str) -> KnowledgePassport | None:
        return self._passports.get(passport_id)

    def get_by_knowledge(self, knowledge_uuid: str) -> KnowledgePassport | None:
        pid = self._by_knowledge.get(knowledge_uuid)
        return self._passports.get(pid) if pid else None

    def get_by_book(self, book_uuid: str) -> list[KnowledgePassport]:
        ids = self._by_book.get(book_uuid, [])
        return [self._passports[pid] for pid in ids if pid in self._passports]

    def add_evidence(self, knowledge_uuid: str, evidence_id: str) -> bool:
        pid = self._by_knowledge.get(knowledge_uuid)
        passport = self._passports.get(pid) if pid else None
        if passport:
            if evidence_id not in passport.evidence_ids:
                passport.evidence_ids.append(evidence_id)
                passport.evidence_count = len(passport.evidence_ids)
            return True
        return False

    def add_conflict(self, knowledge_uuid: str, conflict: dict[str, Any]) -> bool:
        pid = self._by_knowledge.get(knowledge_uuid)
        passport = self._passports.get(pid) if pid else None
        if passport:
            passport.conflicts.append(conflict)
            passport.verification_status = PassportStatus.CONFLICTED
            return True
        return False

    def verify(self, knowledge_uuid: str, status: PassportStatus,
               confidence: float = 0.0) -> bool:
        pid = self._by_knowledge.get(knowledge_uuid)
        passport = self._passports.get(pid) if pid else None
        if passport:
            passport.verification_status = status
            if confidence > 0:
                passport.confidence = confidence
            passport.last_verified = datetime.now(timezone.utc).isoformat()
            passport.updated_at = datetime.now(timezone.utc).isoformat()
            return True
        return False

    def flag_for_review(self, knowledge_uuid: str, notes: str = "") -> bool:
        pid = self._by_knowledge.get(knowledge_uuid)
        passport = self._passports.get(pid) if pid else None
        if passport:
            passport.human_review_flag = True
            passport.human_review_notes = notes
            return True
        return False

    def approved(self) -> list[KnowledgePassport]:
        return [p for p in self._passports.values() if p.approval_status == PassportStatus.APPROVED]

    def count(self) -> int:
        return len(self._passports)

    def summary(self) -> dict:
        vs: dict[str, int] = {}
        for p in self._passports.values():
            vs[p.verification_status.value] = vs.get(p.verification_status.value, 0) + 1
        return {
            "total": self.count(),
            "by_verification_status": vs,
            "flagged_for_review": sum(1 for p in self._passports.values() if p.human_review_flag),
        }
