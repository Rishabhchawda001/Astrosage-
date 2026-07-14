"""
Alignment Engine — Cross-edition alignment of knowledge objects.

Supports alignment between parallel editions, translated editions,
commentary editions, and roman transliterations.
Never auto-merges. Creates alignment objects only.
"""
from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Optional


class EditionType(str, Enum):
    ORIGINAL = "original"
    TRANSLATION = "translation"
    CRITICAL_EDITION = "critical_edition"
    COMMENTARY = "commentary"
    ROMAN_TRANSLITERATION = "roman_transliteration"
    REGIONAL_EDITION = "regional_edition"
    PUBLISHER_EDITION = "publisher_edition"
    DIGITAL_REPRINT = "digital_reprint"
    UNKNOWN = "unknown"


class AlignmentStatus(str, Enum):
    PROPOSED = "proposed"
    PARTIAL = "partial"
    COMPLETE = "complete"
    CONFLICTED = "conflicted"
    REJECTED = "rejected"


@dataclass
class EditionInfo:
    """Information about a single edition."""
    edition_uuid: str = ""
    book_uuid: str = ""
    edition_type: EditionType = EditionType.UNKNOWN
    language: str = ""
    script: str = ""
    publisher: str = ""
    year: str = ""
    title: str = ""
    content_hash: str = ""
    metadata: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self):
        if not self.edition_uuid:
            self.edition_uuid = f"ED-{uuid.uuid4().hex[:12]}"


@dataclass
class AlignmentSegment:
    """A segment alignment between two editions."""
    segment_id: str = ""
    edition_a_uuid: str = ""
    edition_b_uuid: str = ""
    segment_a: str = ""  # text or reference
    segment_b: str = ""
    page_a: int = 0
    page_b: int = 0
    confidence: float = 0.0
    metadata: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self):
        if not self.segment_id:
            self.segment_id = f"AS-{uuid.uuid4().hex[:12]}"


@dataclass
class EditionAlignment:
    """Alignment between two or more editions."""
    alignment_id: str = ""
    edition_uuids: list[str] = field(default_factory=list)
    status: AlignmentStatus = AlignmentStatus.PROPOSED
    segments: list[AlignmentSegment] = field(default_factory=list)
    language_pairs: list[tuple[str, str]] = field(default_factory=list)
    alignment_type: str = "parallel"
    metadata: dict[str, Any] = field(default_factory=dict)
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    updated_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

    def __post_init__(self):
        if not self.alignment_id:
            self.alignment_id = f"AL-{uuid.uuid4().hex[:12]}"

    @property
    def segment_count(self) -> int:
        return len(self.segments)

    @property
    def avg_confidence(self) -> float:
        if not self.segments:
            return 0.0
        return sum(s.confidence for s in self.segments) / len(self.segments)


class AlignmentEngine:
    """
    Production alignment engine.

    Creates and manages cross-edition alignments.
    Never automatically merges content from different editions.
    """

    def __init__(self):
        self._editions: dict[str, EditionInfo] = {}
        self._alignments: dict[str, EditionAlignment] = {}
        self._edition_to_alignment: dict[str, set[str]] = {}

    def register_edition(self, edition: EditionInfo) -> str:
        self._editions[edition.edition_uuid] = edition
        return edition.edition_uuid

    def get_edition(self, edition_uuid: str) -> Optional[EditionInfo]:
        return self._editions.get(edition_uuid)

    def list_editions(self) -> list[EditionInfo]:
        return list(self._editions.values())

    def list_editions_by_language(self, language: str) -> list[EditionInfo]:
        return [e for e in self._editions.values() if e.language == language]

    def list_editions_by_type(self, edition_type: EditionType) -> list[EditionInfo]:
        return [e for e in self._editions.values() if e.edition_type == edition_type]

    def propose_alignment(
        self,
        edition_uuids: list[str],
        alignment_type: str = "parallel",
    ) -> EditionAlignment:
        """Propose a new alignment between editions. Does NOT merge content."""
        for eid in edition_uuids:
            if eid not in self._editions:
                raise ValueError(f"Unknown edition: {eid}")

        alignment = EditionAlignment(
            edition_uuids=list(edition_uuids),
            alignment_type=alignment_type,
            status=AlignmentStatus.PROPOSED,
        )
        self._alignments[alignment.alignment_id] = alignment
        for eid in edition_uuids:
            self._edition_to_alignment.setdefault(eid, set()).add(alignment.alignment_id)
        return alignment

    def add_segment(self, alignment_id: str, segment: AlignmentSegment) -> None:
        alignment = self._alignments.get(alignment_id)
        if not alignment:
            raise ValueError(f"Unknown alignment: {alignment_id}")
        alignment.segments.append(segment)
        alignment.updated_at = datetime.now(timezone.utc).isoformat()
        if alignment.status == AlignmentStatus.PROPOSED:
            alignment.status = AlignmentStatus.PARTIAL

    def get_alignment(self, alignment_id: str) -> Optional[EditionAlignment]:
        return self._alignments.get(alignment_id)

    def get_alignments_for_edition(self, edition_uuid: str) -> list[EditionAlignment]:
        ids = self._edition_to_alignment.get(edition_uuid, set())
        return [self._alignments[aid] for aid in ids if aid in self._alignments]

    def find_parallel_editions(self, book_uuid: str) -> list[EditionInfo]:
        return [e for e in self._editions.values() if e.book_uuid == book_uuid]

    def summary(self) -> dict:
        status_counts: dict[str, int] = {}
        for a in self._alignments.values():
            status_counts[a.status.value] = status_counts.get(a.status.value, 0) + 1
        return {
            "total_editions": len(self._editions),
            "total_alignments": len(self._alignments),
            "total_segments": sum(a.segment_count for a in self._alignments.values()),
            "by_status": status_counts,
        }
