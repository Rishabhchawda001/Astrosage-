"""
Knowledge Passport — Permanent identity and verification record for every knowledge unit.

Every logical knowledge object receives a passport that tracks its lifecycle
from OCR through recovery, verification, and approval.
"""
from __future__ import annotations

import hashlib
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Optional


class PassportStatus(str, Enum):
    CREATED = "created"
    EVIDENCE_COLLECTED = "evidence_collected"
    RECOVERY_ATTEMPTED = "recovery_attempted"
    VERIFIED = "verified"
    APPROVED = "approved"
    REJECTED = "rejected"
    CONFLICTED = "conflicted"
    UNDER_REVIEW = "under_review"
    DEFERRED = "deferred"


@dataclass
class ConflictRecord:
    """A conflict detected in this knowledge unit."""
    conflict_id: str = ""
    conflict_type: str = ""  # wording, verse_numbering, metadata, etc.
    variant_a: str = ""
    variant_b: str = ""
    source_a: str = ""
    source_b: str = ""
    detected_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    resolved: bool = False
    resolution: str = ""

    def __post_init__(self):
        if not self.conflict_id:
            self.conflict_id = f"CF-{uuid.uuid4().hex[:12]}"


@dataclass
class VersionRecord:
    """A version of the knowledge content."""
    version_id: str = ""
    content_hash: str = ""
    source: str = ""
    pipeline_version: str = ""
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

    def __post_init__(self):
        if not self.version_id:
            self.version_id = f"VER-{uuid.uuid4().hex[:12]}"


@dataclass
class KnowledgePassport:
    """
    Permanent passport for a knowledge unit.

    Tracks identity, provenance, recovery, verification, conflicts,
    versions, and approval status throughout its lifecycle.
    """
    knowledge_uuid: str = ""
    book_uuid: str = ""
    edition_uuid: str = ""
    document_uuid: str = ""
    language: str = ""
    script: str = ""
    original_source: str = ""
    recovered_sources: list[str] = field(default_factory=list)
    evidence_count: int = 0
    confidence: float = 0.0
    verification_status: str = "unverified"
    approval_status: str = "unreviewed"
    status: PassportStatus = PassportStatus.CREATED
    conflicts: list[ConflictRecord] = field(default_factory=list)
    versions: list[VersionRecord] = field(default_factory=list)
    checksums: dict[str, str] = field(default_factory=dict)
    metadata: dict[str, Any] = field(default_factory=dict)
    human_review_flag: bool = False
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    updated_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    last_verified: str = ""
    pipeline_version: str = "1.0.0"

    def __post_init__(self):
        if not self.knowledge_uuid:
            self.knowledge_uuid = f"KP-{uuid.uuid4().hex[:12]}"

    def add_version(self, content: str, source: str, pipeline_version: str = "") -> VersionRecord:
        content_hash = hashlib.sha256(content.encode("utf-8")).hexdigest()
        version = VersionRecord(
            content_hash=content_hash,
            source=source,
            pipeline_version=pipeline_version,
        )
        self.versions.append(version)
        self.checksums[version.version_id] = content_hash
        self.updated_at = datetime.now(timezone.utc).isoformat()
        return version

    def add_conflict(self, conflict_type: str, variant_a: str, variant_b: str,
                     source_a: str = "", source_b: str = "") -> ConflictRecord:
        conflict = ConflictRecord(
            conflict_type=conflict_type,
            variant_a=variant_a,
            variant_b=variant_b,
            source_a=source_a,
            source_b=source_b,
        )
        self.conflicts.append(conflict)
        self.status = PassportStatus.CONFLICTED
        self.updated_at = datetime.now(timezone.utc).isoformat()
        return conflict

    def update_confidence(self, confidence: float) -> None:
        self.confidence = max(0.0, min(1.0, confidence))
        self.updated_at = datetime.now(timezone.utc).isoformat()

    def approve(self) -> None:
        self.approval_status = "approved"
        self.status = PassportStatus.APPROVED
        self.updated_at = datetime.now(timezone.utc).isoformat()

    def reject(self, reason: str = "") -> None:
        self.approval_status = "rejected"
        self.status = PassportStatus.REJECTED
        self.updated_at = datetime.now(timezone.utc).isoformat()

    def flag_for_review(self) -> None:
        self.human_review_flag = True
        self.status = PassportStatus.UNDER_REVIEW
        self.updated_at = datetime.now(timezone.utc).isoformat()

    def add_evidence_source(self, source: str) -> None:
        if source not in self.recovered_sources:
            self.recovered_sources.append(source)
        self.evidence_count = len(self.recovered_sources)
        self.updated_at = datetime.now(timezone.utc).isoformat()

    def latest_version(self) -> Optional[VersionRecord]:
        return self.versions[-1] if self.versions else None

    def unresolve_conflicts(self) -> list[ConflictRecord]:
        return [c for c in self.conflicts if not c.resolved]

    def to_dict(self) -> dict[str, Any]:
        return {
            "knowledge_uuid": self.knowledge_uuid,
            "book_uuid": self.book_uuid,
            "edition_uuid": self.edition_uuid,
            "document_uuid": self.document_uuid,
            "language": self.language,
            "script": self.script,
            "original_source": self.original_source,
            "recovered_sources": self.recovered_sources,
            "evidence_count": self.evidence_count,
            "confidence": self.confidence,
            "verification_status": self.verification_status,
            "approval_status": self.approval_status,
            "status": self.status.value,
            "conflict_count": len(self.conflicts),
            "version_count": len(self.versions),
            "human_review_flag": self.human_review_flag,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "last_verified": self.last_verified,
            "pipeline_version": self.pipeline_version,
        }


class PassportManager:
    """Manages all knowledge passports."""

    def __init__(self):
        self._passports: dict[str, KnowledgePassport] = {}

    def create(self, **kwargs) -> KnowledgePassport:
        passport = KnowledgePassport(**kwargs)
        self._passports[passport.knowledge_uuid] = passport
        return passport

    def get(self, knowledge_uuid: str) -> Optional[KnowledgePassport]:
        return self._passports.get(knowledge_uuid)

    def list_all(self) -> list[KnowledgePassport]:
        return list(self._passports.values())

    def list_by_status(self, status: PassportStatus) -> list[KnowledgePassport]:
        return [p for p in self._passports.values() if p.status == status]

    def list_by_language(self, language: str) -> list[KnowledgePassport]:
        return [p for p in self._passports.values() if p.language == language]

    def list_pending_review(self) -> list[KnowledgePassport]:
        return [p for p in self._passports.values() if p.human_review_flag]

    def count(self) -> int:
        return len(self._passports)

    def summary(self) -> dict:
        status_counts: dict[str, int] = {}
        lang_counts: dict[str, int] = {}
        for p in self._passports.values():
            status_counts[p.status.value] = status_counts.get(p.status.value, 0) + 1
            lang_counts[p.language] = lang_counts.get(p.language, 0) + 1
        return {
            "total": self.count(),
            "by_status": status_counts,
            "by_language": lang_counts,
            "pending_review": len(self.list_pending_review()),
        }
