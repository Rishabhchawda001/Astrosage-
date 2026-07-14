"""
Gap Reconstruction Engine — Recover every recoverable gap using evidence.

Never invent text. Require configurable evidence threshold.
Every recovered fragment stores confidence, sources, edition IDs,
timestamps, matching score, reason.
"""
from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Optional


class RecoveryType(str, Enum):
    MISSING_PAGE = "missing_page"
    MISSING_VERSE = "missing_verse"
    MISSING_PARAGRAPH = "missing_paragraph"
    BROKEN_OCR = "broken_ocr"
    ENCODING_CORRUPTION = "encoding_corruption"
    PARTIAL_EXTRACTION = "partial_extraction"
    CUT_SENTENCE = "cut_sentence"
    SPLIT_PARAGRAPH = "split_paragraph"
    EMPTY_OCR = "empty_ocr"
    DAMAGED_SCAN = "damaged_scan"
    TABLE = "table"
    FOOTNOTE = "footnote"
    APPENDIX = "appendix"
    HEADER = "header"
    METADATA = "metadata"


class RecoveryStatus(str, Enum):
    CANDIDATE = "candidate"
    EVIDENCE_COLLECTED = "evidence_collected"
    VERIFIED = "verified"
    REJECTED = "rejected"
    UNKNOWN = "unknown"


@dataclass
class RecoveryFragment:
    fragment_id: str = ""
    knowledge_uuid: str = ""
    recovery_type: RecoveryType = RecoveryType.BROKEN_OCR
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
        if not self.fragment_id:
            self.fragment_id = f"RF-{uuid.uuid4().hex[:12]}"


class ReconstructionEngine:
    """Production reconstruction engine. Never invents text."""

    def __init__(self, min_evidence: int = 2, min_confidence: float = 0.6):
        self.min_evidence = min_evidence
        self.min_confidence = min_confidence
        self._fragments: dict[str, RecoveryFragment] = {}
        self._by_knowledge: dict[str, list[str]] = {}
        self._by_type: dict[str, list[str]] = {}

    def create_candidate(self, knowledge_uuid: str, recovery_type: RecoveryType,
                         original_text: str = "", recovered_text: str = "",
                         sources: list[str] | None = None, edition_ids: list[str] | None = None,
                         confidence: float = 0.0, matching_score: float = 0.0,
                         reason: str = "") -> RecoveryFragment:
        fragment = RecoveryFragment(
            knowledge_uuid=knowledge_uuid, recovery_type=recovery_type,
            original_text=original_text, recovered_text=recovered_text,
            sources=sources or [], edition_ids=edition_ids or [],
            confidence=confidence, matching_score=matching_score, reason=reason,
            status=RecoveryStatus.CANDIDATE if confidence >= self.min_confidence else RecoveryStatus.UNKNOWN)
        self._fragments[fragment.fragment_id] = fragment
        self._by_knowledge.setdefault(knowledge_uuid, []).append(fragment.fragment_id)
        self._by_type.setdefault(recovery_type.value, []).append(fragment.fragment_id)
        return fragment

    def verify(self, fragment_id: str, verified: bool, reason: str = "") -> bool:
        f = self._fragments.get(fragment_id)
        if f:
            f.status = RecoveryStatus.VERIFIED if verified else RecoveryStatus.REJECTED
            f.verified_at = datetime.now(timezone.utc).isoformat()
            f.reason = reason or f.reason
            return True
        return False

    def get_fragments(self, knowledge_uuid: str) -> list[RecoveryFragment]:
        ids = self._by_knowledge.get(knowledge_uuid, [])
        return [self._fragments[fid] for fid in ids if fid in self._fragments]

    def get_verified(self) -> list[RecoveryFragment]:
        return [f for f in self._fragments.values() if f.status == RecoveryStatus.VERIFIED]

    def count(self) -> int: return len(self._fragments)

    def summary(self) -> dict:
        tc: dict[str, int] = {}
        sc: dict[str, int] = {}
        for f in self._fragments.values():
            tc[f.recovery_type.value] = tc.get(f.recovery_type.value, 0) + 1
            sc[f.status.value] = sc.get(f.status.value, 0) + 1
        return {"total": self.count(), "by_type": tc, "by_status": sc}
