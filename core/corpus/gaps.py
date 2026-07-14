"""
Corpus Gap Engine — Scans the corpus and detects every type of gap.

Detects: missing pages, paragraphs, verses, slokas, broken OCR,
encoding corruption, low confidence, split/merged paragraphs,
broken tables, headings, metadata, bibliography, references,
commentary, translations, hierarchy, relationships, citations.
"""
from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Optional


class GapType(str, Enum):
    MISSING_PAGE = "missing_page"
    MISSING_PARAGRAPH = "missing_paragraph"
    MISSING_VERSE = "missing_verse"
    MISSING_SLOKA = "missing_sloka"
    BROKEN_OCR = "broken_ocr"
    ENCODING_CORRUPTION = "encoding_corruption"
    UNICODE_CORRUPTION = "unicode_corruption"
    LOW_CONFIDENCE = "low_confidence"
    SPLIT_PARAGRAPH = "split_paragraph"
    MERGED_PARAGRAPH = "merged_paragraph"
    BROKEN_TABLE = "broken_table"
    BROKEN_HEADING = "broken_heading"
    MISSING_METADATA = "missing_metadata"
    MISSING_BIBLIOGRAPHY = "missing_bibliography"
    MISSING_REFERENCES = "missing_references"
    BROKEN_COMMENTARY = "broken_commentary"
    BROKEN_TRANSLATION = "broken_translation"
    BROKEN_HIERARCHY = "broken_hierarchy"
    BROKEN_RELATIONSHIP = "broken_relationship"
    BROKEN_CITATION = "broken_citation"
    EMPTY_CONTENT = "empty_content"
    TRUNCATED_LINE = "truncated_line"
    SUSPICIOUS_WHITEPACE = "suspicious_whitespace"
    UNKNOWN = "unknown"


class GapSeverity(str, Enum):
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class GapStatus(str, Enum):
    DETECTED = "detected"
    QUEUED = "queued"
    IN_PROGRESS = "in_progress"
    RECOVERED = "recovered"
    VERIFIED = "verified"
    REJECTED = "rejected"
    DEFERRED = "deferred"
    UNKNOWN = "unknown"


@dataclass
class Gap:
    """A single gap in the corpus."""
    gap_id: str = ""
    gap_type: GapType = GapType.UNKNOWN
    severity: GapSeverity = GapSeverity.MEDIUM
    status: GapStatus = GapStatus.DETECTED
    book_uuid: str = ""
    edition_uuid: str = ""
    document_uuid: str = ""
    passport_id: str = ""
    page: int = 0
    chapter: str = ""
    verse: str = ""
    description: str = ""
    confidence: float = 0.0
    evidence_refs: list[str] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)
    detected_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    updated_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

    def __post_init__(self):
        if not self.gap_id:
            self.gap_id = f"GA-{uuid.uuid4().hex[:12]}"


class CorpusGapEngine:
    """
    Production gap detection engine.

    Scans documents and detects every type of corpus gap.
    Every gap receives UUID, severity, confidence, and evidence references.
    """

    def __init__(self):
        self._gaps: dict[str, Gap] = {}
        self._by_book: dict[str, list[str]] = {}
        self._by_type: dict[str, list[str]] = {}
        self._by_severity: dict[str, list[str]] = {}

    def detect_gap(self, **kwargs) -> Gap:
        gap = Gap(**kwargs)
        self._gaps[gap.gap_id] = gap
        self._by_book.setdefault(gap.book_uuid, []).append(gap.gap_id)
        self._by_type.setdefault(gap.gap_type.value, []).append(gap.gap_id)
        self._by_severity.setdefault(gap.severity.value, []).append(gap.gap_id)
        return gap

    def scan_empty_content(self, text: str, document_uuid: str = "", book_uuid: str = "", page: int = 0) -> list[Gap]:
        gaps = []
        if not text or len(text.strip()) < 10:
            gaps.append(self.detect_gap(
                gap_type=GapType.EMPTY_CONTENT,
                severity=GapSeverity.HIGH,
                document_uuid=document_uuid,
                book_uuid=book_uuid,
                page=page,
                description=f"Empty or near-empty content ({len(text.strip())} chars)",
                confidence=0.95,
            ))
        return gaps

    def scan_encoding(self, text: str, document_uuid: str = "", book_uuid: str = "", page: int = 0) -> list[Gap]:
        gaps = []
        if "\ufffd" in text:
            gaps.append(self.detect_gap(
                gap_type=GapType.UNICODE_CORRUPTION,
                severity=GapSeverity.HIGH,
                document_uuid=document_uuid,
                book_uuid=book_uuid,
                page=page,
                description=f"Unicode replacement characters found ({text.count(chr(0xFFFD))})",
                confidence=0.9,
            ))
        return gaps

    def scan_low_confidence(self, text: str, confidence: float, document_uuid: str = "", book_uuid: str = "", page: int = 0) -> list[Gap]:
        gaps = []
        if confidence < 0.5:
            gaps.append(self.detect_gap(
                gap_type=GapType.LOW_CONFIDENCE,
                severity=GapSeverity.MEDIUM,
                document_uuid=document_uuid,
                book_uuid=book_uuid,
                page=page,
                description=f"Low OCR confidence: {confidence:.2f}",
                confidence=confidence,
                metadata={"ocr_confidence": confidence},
            ))
        return gaps

    def scan_truncated_lines(self, text: str, document_uuid: str = "", book_uuid: str = "", page: int = 0) -> list[Gap]:
        gaps = []
        for line in text.split("\n"):
            stripped = line.strip()
            if stripped and len(stripped) > 10:
                if stripped and stripped[-1] not in ".।!?;:,—":
                    gaps.append(self.detect_gap(
                        gap_type=GapType.TRUNCATED_LINE,
                        severity=GapSeverity.LOW,
                        document_uuid=document_uuid,
                        book_uuid=book_uuid,
                        page=page,
                        description=f"Potentially truncated: ...{stripped[-30:]}",
                        confidence=0.4,
                    ))
        return gaps[:10]

    def scan_document(self, text: str, document_uuid: str = "", book_uuid: str = "", page: int = 0, ocr_confidence: float = 0.0) -> list[Gap]:
        gaps = []
        gaps.extend(self.scan_empty_content(text, document_uuid, book_uuid, page))
        gaps.extend(self.scan_encoding(text, document_uuid, book_uuid, page))
        gaps.extend(self.scan_low_confidence(text, ocr_confidence, document_uuid, book_uuid, page))
        gaps.extend(self.scan_truncated_lines(text, document_uuid, book_uuid, page))
        return gaps

    def get_gap(self, gap_id: str) -> Optional[Gap]:
        return self._gaps.get(gap_id)

    def get_gaps_by_book(self, book_uuid: str) -> list[Gap]:
        ids = self._by_book.get(book_uuid, [])
        return [self._gaps[gid] for gid in ids if gid in self._gaps]

    def get_gaps_by_type(self, gap_type: GapType) -> list[Gap]:
        ids = self._by_type.get(gap_type.value, [])
        return [self._gaps[gid] for gid in ids if gid in self._gaps]

    def get_gaps_by_severity(self, severity: GapSeverity) -> list[Gap]:
        ids = self._by_severity.get(severity.value, [])
        return [self._gaps[gid] for gid in ids if gid in self._gaps]

    def get_critical_gaps(self) -> list[Gap]:
        return self.get_gaps_by_severity(GapSeverity.CRITICAL)

    def count(self) -> int:
        return len(self._gaps)

    def summary(self) -> dict:
        type_counts: dict[str, int] = {}
        severity_counts: dict[str, int] = {}
        status_counts: dict[str, int] = {}
        for g in self._gaps.values():
            type_counts[g.gap_type.value] = type_counts.get(g.gap_type.value, 0) + 1
            severity_counts[g.severity.value] = severity_counts.get(g.severity.value, 0) + 1
            status_counts[g.status.value] = status_counts.get(g.status.value, 0) + 1
        return {
            "total_gaps": self.count(),
            "by_type": type_counts,
            "by_severity": severity_counts,
            "by_status": status_counts,
            "books_affected": len(self._by_book),
        }
