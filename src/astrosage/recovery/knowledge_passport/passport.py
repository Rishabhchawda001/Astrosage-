"""
Knowledge Passport — Complete provenance and verification record for recovered knowledge.

Every recovered knowledge object receives a passport containing:
  - Original OCR text
  - Recovered candidate text
  - Evidence sources
  - Agreement metrics
  - Verification history
  - Edition links
  - Checksums
"""
from __future__ import annotations

import json
from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from enum import Enum
from pathlib import Path
from typing import Optional


class RecoveryStatus(str, Enum):
    NOT_STARTED = "not_started"
    IN_PROGRESS = "in_progress"
    CANDIDATE_FOUND = "candidate_found"
    VERIFIED = "verified"
    REJECTED = "rejected"
    CONFLICT = "conflict"
    NEEDS_REVIEW = "needs_review"


class ReviewStatus(str, Enum):
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    DEFERRED = "deferred"
    NEEDS_MORE_EVIDENCE = "needs_more_evidence"


@dataclass
class EvidenceSource:
    source_id: str
    source_name: str
    text_snippet: str = ""
    confidence: float = 0.0
    page_number: int = 0
    url: str = ""
    retrieved_at: str = ""


@dataclass
class VerificationRecord:
    verifier: str  # "system", "human_reviewer_id", or pipeline name
    timestamp: str = ""
    result: str = ""  # "verified", "rejected", "conflict"
    confidence: float = 0.0
    notes: str = ""
    evidence_used: list[str] = field(default_factory=list)  # source_ids


@dataclass
class EditionLink:
    edition_id: str
    edition_name: str = ""
    publisher: str = ""
    year: str = ""
    language: str = ""
    confidence: float = 0.0
    text_agreement_pct: float = 0.0


@dataclass
class KnowledgePassport:
    """
    Complete passport for a recovered knowledge object.

    This is the definitive record of everything known about
    a piece of recovered knowledge.
    """
    passport_id: str = ""
    knowledge_uuid: str = ""  # Links to Knowledge Registry
    book_uuid: str = ""
    document_uuid: str = ""

    # Text content
    original_ocr: str = ""
    recovered_candidate: str = ""

    # Recovery metadata
    recovery_status: RecoveryStatus = RecoveryStatus.NOT_STARTED
    recovery_reason: str = ""
    recovery_pipeline_version: str = ""

    # Evidence
    evidence_sources: list[EvidenceSource] = field(default_factory=list)
    agreement_count: int = 0
    total_sources_checked: int = 0

    # Confidence
    confidence_score: float = 0.0
    confidence_breakdown: dict = field(default_factory=dict)

    # Review
    review_status: ReviewStatus = ReviewStatus.PENDING
    reviewer: str = ""
    review_notes: str = ""

    # Verification history
    verification_history: list[VerificationRecord] = field(default_factory=list)

    # Edition links
    edition_links: list[EditionLink] = field(default_factory=list)

    # Checksums
    original_checksum: str = ""
    recovered_checksum: str = ""

    # Timestamps
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    updated_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

    def add_evidence(self, source: EvidenceSource):
        """Add an evidence source."""
        self.evidence_sources.append(source)
        self.agreement_count = sum(
            1 for s in self.evidence_sources if s.confidence > 0.5
        )
        self.total_sources_checked = len(self.evidence_sources)
        self.updated_at = datetime.now(timezone.utc).isoformat()

    def add_verification(self, record: VerificationRecord):
        """Add a verification record."""
        self.verification_history.append(record)
        self.updated_at = datetime.now(timezone.utc).isoformat()

    def add_edition_link(self, link: EditionLink):
        """Link to another edition."""
        self.edition_links.append(link)
        self.updated_at = datetime.now(timezone.utc).isoformat()

    def compute_overall_confidence(self) -> float:
        """Compute overall confidence from all sources."""
        if not self.evidence_sources:
            return 0.0
        source_scores = [s.confidence for s in self.evidence_sources]
        agreement_bonus = min(0.2, self.agreement_count * 0.05)
        avg_confidence = sum(source_scores) / len(source_scores)
        self.confidence_score = min(1.0, avg_confidence + agreement_bonus)
        return self.confidence_score

    def to_dict(self) -> dict:
        return asdict(self)

    def save(self, directory: Path):
        """Save passport to directory."""
        directory.mkdir(parents=True, exist_ok=True)
        filepath = directory / f"{self.passport_id}.json"
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(self.to_dict(), f, indent=2, ensure_ascii=False)

    @classmethod
    def load(cls, filepath: Path) -> "KnowledgePassport":
        """Load passport from file."""
        with open(filepath, "r", encoding="utf-8") as f:
            data = json.load(f)
        data["evidence_sources"] = [
            EvidenceSource(**e) for e in data.get("evidence_sources", [])
        ]
        data["verification_history"] = [
            VerificationRecord(**v) for v in data.get("verification_history", [])
        ]
        data["edition_links"] = [
            EditionLink(**e) for e in data.get("edition_links", [])
        ]
        data["recovery_status"] = RecoveryStatus(data.get("recovery_status", "not_started"))
        data["review_status"] = ReviewStatus(data.get("review_status", "pending"))
        return cls(**data)


class KnowledgePassportRegistry:
    """Registry of all knowledge passports."""

    def __init__(self, passports_dir: str = "knowledge/recovery/knowledge_passports"):
        self.passports_dir = Path(passports_dir)
        self.passports_dir.mkdir(parents=True, exist_ok=True)
        self._passports: dict[str, KnowledgePassport] = {}

    def create_passport(self, knowledge_uuid: str, book_uuid: str = "", document_uuid: str = "") -> KnowledgePassport:
        """Create a new passport."""
        passport_id = f"KP-{knowledge_uuid[:12]}"
        passport = KnowledgePassport(
            passport_id=passport_id,
            knowledge_uuid=knowledge_uuid,
            book_uuid=book_uuid,
            document_uuid=document_uuid,
        )
        self._passports[passport_id] = passport
        return passport

    def get_passport(self, passport_id: str) -> Optional[KnowledgePassport]:
        if passport_id in self._passports:
            return self._passports[passport_id]
        # Try loading from disk
        filepath = self.passports_dir / f"{passport_id}.json"
        if filepath.exists():
            passport = KnowledgePassport.load(filepath)
            self._passports[passport_id] = passport
            return passport
        return None

    def get_passports_by_status(self, status: RecoveryStatus) -> list[KnowledgePassport]:
        return [p for p in self._passports.values() if p.recovery_status == status]

    def save_all(self):
        for passport in self._passports.values():
            passport.save(self.passports_dir)

    def summary(self) -> dict:
        status_counts = {}
        review_counts = {}
        for p in self._passports.values():
            status_counts[p.recovery_status.value] = status_counts.get(p.recovery_status.value, 0) + 1
            review_counts[p.review_status.value] = review_counts.get(p.review_status.value, 0) + 1
        return {
            "total_passports": len(self._passports),
            "by_recovery_status": status_counts,
            "by_review_status": review_counts,
        }
