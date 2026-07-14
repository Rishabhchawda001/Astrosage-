"""
Reconstruction Engine — Generates candidate recoveries (never auto-reconstructs).

Each candidate stores: original, recovered candidate, supporting evidence,
supporting editions, supporting translations, confidence, human review requirement.
"""
from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Optional


class CandidateStatus(str, Enum):
    GENERATED = "generated"
    EVIDENCE_COLLECTED = "evidence_collected"
    SUBMITTED_FOR_REVIEW = "submitted_for_review"
    APPROVED = "approved"
    REJECTED = "rejected"
    SUPERSEDED = "superseded"


@dataclass
class RecoveryCandidate:
    """A candidate recovery for a gap."""
    candidate_id: str = ""
    gap_id: str = ""
    knowledge_uuid: str = ""
    original_text: str = ""
    recovered_text: str = ""
    supporting_evidence: list[str] = field(default_factory=list)
    supporting_editions: list[str] = field(default_factory=list)
    supporting_translations: list[str] = field(default_factory=list)
    confidence: float = 0.0
    requires_human_review: bool = True
    status: CandidateStatus = CandidateStatus.GENERATED
    reviewer: str = ""
    rejection_reason: str = ""
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    updated_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    metadata: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self):
        if not self.candidate_id:
            self.candidate_id = f"RC-{uuid.uuid4().hex[:12]}"


class ReconstructionEngine:
    """
    Candidate recovery engine.

    NEVER auto-reconstructs. Only generates candidates that require evidence
    and often human review before approval.
    """

    def __init__(self, auto_review_threshold: float = 0.95):
        self.auto_review_threshold = auto_review_threshold
        self._candidates: dict[str, RecoveryCandidate] = {}
        self._by_gap: dict[str, list[str]] = {}
        self._by_knowledge: dict[str, list[str]] = {}

    def create_candidate(self, gap_id: str, original_text: str, recovered_text: str,
                         knowledge_uuid: str = "", supporting_evidence: list[str] | None = None,
                         supporting_editions: list[str] | None = None, confidence: float = 0.0) -> RecoveryCandidate:
        requires_review = confidence < self.auto_review_threshold
        candidate = RecoveryCandidate(
            gap_id=gap_id, knowledge_uuid=knowledge_uuid,
            original_text=original_text, recovered_text=recovered_text,
            supporting_evidence=supporting_evidence or [],
            supporting_editions=supporting_editions or [],
            confidence=confidence, requires_human_review=requires_review,
        )
        self._candidates[candidate.candidate_id] = candidate
        self._by_gap.setdefault(gap_id, []).append(candidate.candidate_id)
        if knowledge_uuid:
            self._by_knowledge.setdefault(knowledge_uuid, []).append(candidate.candidate_id)
        return candidate

    def approve(self, candidate_id: str, reviewer: str = "human") -> bool:
        c = self._candidates.get(candidate_id)
        if c:
            c.status = CandidateStatus.APPROVED
            c.reviewer = reviewer
            c.updated_at = datetime.now(timezone.utc).isoformat()
            return True
        return False

    def reject(self, candidate_id: str, reason: str = "", reviewer: str = "human") -> bool:
        c = self._candidates.get(candidate_id)
        if c:
            c.status = CandidateStatus.REJECTED
            c.rejection_reason = reason
            c.reviewer = reviewer
            c.updated_at = datetime.now(timezone.utc).isoformat()
            return True
        return False

    def get_candidate(self, candidate_id: str) -> Optional[RecoveryCandidate]:
        return self._candidates.get(candidate_id)

    def get_by_gap(self, gap_id: str) -> list[RecoveryCandidate]:
        ids = self._by_gap.get(gap_id, [])
        return [self._candidates[cid] for cid in ids if cid in self._candidates]

    def get_pending_review(self) -> list[RecoveryCandidate]:
        return [c for c in self._candidates.values() if c.requires_human_review and c.status == CandidateStatus.GENERATED]

    def count(self) -> int:
        return len(self._candidates)

    def summary(self) -> dict:
        status_counts: dict[str, int] = {}
        for c in self._candidates.values():
            status_counts[c.status.value] = status_counts.get(c.status.value, 0) + 1
        return {"total_candidates": self.count(), "pending_review": len(self.get_pending_review()), "by_status": status_counts}
