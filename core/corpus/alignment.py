"""Corpus Alignment — Cross-edition alignment for gap analysis."""
from __future__ import annotations
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Optional

class CorpusAlignmentType(str, Enum):
    PARALLEL = "parallel"
    TRANSLATION = "translation"
    COMMENTARY = "commentary"

class CorpusAlignmentStatus(str, Enum):
    PROPOSED = "proposed"
    PARTIAL = "partial"
    COMPLETE = "complete"

@dataclass
class CorpusAlignmentSegment:
    segment_id: str = ""
    text_a: str = ""
    text_b: str = ""
    confidence: float = 0.0
    def __post_init__(self):
        if not self.segment_id: self.segment_id = f"AS-{uuid.uuid4().hex[:12]}"

@dataclass
class CorpusEditionAlignment:
    alignment_id: str = ""
    edition_ids: list[str] = field(default_factory=list)
    alignment_type: CorpusAlignmentType = CorpusAlignmentType.PARALLEL
    status: CorpusAlignmentStatus = CorpusAlignmentStatus.PROPOSED
    segments: list[CorpusAlignmentSegment] = field(default_factory=list)
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    def __post_init__(self):
        if not self.alignment_id: self.alignment_id = f"EA-{uuid.uuid4().hex[:12]}"
    @property
    def segment_count(self) -> int:
        return len(self.segments)

class CorpusAlignmentEngine:
    def __init__(self):
        self._alignments: dict[str, CorpusEditionAlignment] = {}
        self._segments: dict[str, CorpusAlignmentSegment] = {}
    def propose(self, edition_ids: list[str], alignment_type: CorpusAlignmentType = CorpusAlignmentType.PARALLEL) -> CorpusEditionAlignment:
        a = CorpusEditionAlignment(edition_ids=list(edition_ids), alignment_type=alignment_type)
        self._alignments[a.alignment_id] = a
        return a
    def add_segment(self, alignment_id: str, segment: CorpusAlignmentSegment) -> None:
        a = self._alignments.get(alignment_id)
        if a:
            a.segments.append(segment)
            self._segments[segment.segment_id] = segment
    def count(self) -> int:
        return len(self._alignments)
    def summary(self) -> dict:
        return {"total_alignments": self.count(), "total_segments": len(self._segments)}
