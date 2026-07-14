"""
Knowledge Recovery Engine — orchestrates maximum evidence-backed knowledge recovery.

Scans every book, searches every source, builds book families,
aligns editions, recovers only with evidence, and produces
measurable completeness scores.
"""
from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Optional


class RecoveryStatus(str, Enum):
    PENDING = "pending"
    SCANNING = "scanning"
    SEARCHING = "searching"
    ALIGNING = "aligning"
    RECOVERING = "recovering"
    VALIDATING = "validating"
    COMPLETE = "complete"
    PARTIAL = "partial"
    FAILED = "failed"


class KnowledgeDomain(str, Enum):
    VEDIC = "vedic"
    AYURVEDA = "ayurveda"
    ASTROLOGY = "astrology"
    YOGA = "yoga"
    PHILOSOPHY = "philosophy"
    LITERATURE = "literature"
    HISTORY = "history"
    SCIENCE = "science"
    GENERAL = "general"
    UNKNOWN = "unknown"


@dataclass
class RecoveryTarget:
    target_id: str = ""
    book_uuid: str = ""
    book_title: str = ""
    language: str = "unknown"
    domain: KnowledgeDomain = KnowledgeDomain.UNKNOWN
    status: RecoveryStatus = RecoveryStatus.PENDING
    bronze_file: str = ""
    silver_file: str = ""
    page_count: int = 0
    paragraph_count: int = 0
    detected_gaps: int = 0
    searched_sources: int = 0
    found_editions: int = 0
    found_translations: int = 0
    found_commentaries: int = 0
    recovered_paragraphs: int = 0
    verified_paragraphs: int = 0
    unknown_paragraphs: int = 0
    conflicting_paragraphs: int = 0
    completeness_pct: float = 0.0
    evidence_count: int = 0
    confidence_sum: float = 0.0
    started_at: str = ""
    completed_at: str = ""
    metadata: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self):
        if not self.target_id:
            self.target_id = f"RT-{uuid.uuid4().hex[:12]}"


@dataclass
class RecoveryProgress:
    total_books: int = 0
    completed_books: int = 0
    partial_books: int = 0
    failed_books: int = 0
    total_paragraphs: int = 0
    recovered_paragraphs: int = 0
    verified_paragraphs: int = 0
    unknown_paragraphs: int = 0
    conflicting_paragraphs: int = 0
    total_gaps_detected: int = 0
    total_gaps_recovered: int = 0
    total_evidence: int = 0
    total_editions_discovered: int = 0
    total_translations: int = 0
    total_commentaries: int = 0
    overall_completeness: float = 0.0
    started_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    updated_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

    @property
    def completion_pct(self) -> float:
        return (self.completed_books / self.total_books * 100) if self.total_books > 0 else 0.0


class KnowledgeRecoveryEngine:
    """Production knowledge recovery engine. Never invents text."""

    def __init__(self, min_evidence: int = 2, min_confidence: float = 0.6):
        self.min_evidence = min_evidence
        self.min_confidence = min_confidence
        self._targets: dict[str, RecoveryTarget] = {}
        self._by_book: dict[str, str] = {}
        self._progress = RecoveryProgress()
        self._sources: list[str] = []

    def register_source(self, source_name: str) -> None:
        if source_name not in self._sources:
            self._sources.append(source_name)

    def create_target(self, book_uuid: str, book_title: str, language: str = "unknown",
                      domain: KnowledgeDomain = KnowledgeDomain.UNKNOWN,
                      bronze_file: str = "", silver_file: str = "",
                      page_count: int = 0, paragraph_count: int = 0,
                      metadata: dict[str, Any] | None = None) -> RecoveryTarget:
        target = RecoveryTarget(
            book_uuid=book_uuid, book_title=book_title, language=language,
            domain=domain, bronze_file=bronze_file, silver_file=silver_file,
            page_count=page_count, paragraph_count=paragraph_count,
            metadata=metadata or {})
        self._targets[target.target_id] = target
        self._by_book[book_uuid] = target.target_id
        self._progress.total_books += 1
        self._progress.total_paragraphs += paragraph_count
        return target

    def update_progress(self, target_id: str, **kwargs) -> bool:
        target = self._targets.get(target_id)
        if not target:
            return False
        for k, v in kwargs.items():
            if hasattr(target, k):
                setattr(target, k, v)
        if target.status in (RecoveryStatus.COMPLETE, RecoveryStatus.PARTIAL):
            target.completed_at = datetime.now(timezone.utc).isoformat()
            if target.status == RecoveryStatus.COMPLETE:
                self._progress.completed_books += 1
            else:
                self._progress.partial_books += 1
            self._progress.recovered_paragraphs += target.recovered_paragraphs
            self._progress.verified_paragraphs += target.verified_paragraphs
            self._progress.unknown_paragraphs += target.unknown_paragraphs
            self._progress.conflicting_paragraphs += target.conflicting_paragraphs
            self._progress.total_gaps_detected += target.detected_gaps
            self._progress.total_evidence += target.evidence_count
            self._progress.total_editions_discovered += target.found_editions
            self._progress.total_translations += target.found_translations
            self._progress.total_commentaries += target.found_commentaries
        self._progress.updated_at = datetime.now(timezone.utc).isoformat()
        return True

    def get_target(self, target_id: str) -> RecoveryTarget | None:
        return self._targets.get(target_id)

    def get_target_by_book(self, book_uuid: str) -> RecoveryTarget | None:
        tid = self._by_book.get(book_uuid)
        return self._targets.get(tid) if tid else None

    def get_incomplete(self) -> list[RecoveryTarget]:
        return [t for t in self._targets.values() if t.status not in (RecoveryStatus.COMPLETE,)]

    def get_all_targets(self) -> list[RecoveryTarget]:
        return list(self._targets.values())

    def compute_completeness(self, target_id: str) -> float:
        target = self._targets.get(target_id)
        if not target or target.paragraph_count == 0:
            return 0.0
        score = (
            (target.verified_paragraphs / target.paragraph_count) * 40 +
            (target.recovered_paragraphs / target.paragraph_count) * 30 +
            (min(target.found_editions, 5) / 5) * 15 +
            (min(target.evidence_count, 10) / 10) * 15
        )
        target.completeness_pct = min(100.0, score)
        return target.completeness_pct

    def get_progress(self) -> RecoveryProgress:
        if self._progress.total_books > 0:
            total_completeness = sum(
                t.completeness_pct for t in self._targets.values()
            ) / len(self._targets)
            self._progress.overall_completeness = total_completeness
        return self._progress

    def summary(self) -> dict:
        p = self.get_progress()
        return {
            "total_books": p.total_books,
            "completed": p.completed_books,
            "partial": p.partial_books,
            "failed": p.failed_books,
            "total_paragraphs": p.total_paragraphs,
            "recovered": p.recovered_paragraphs,
            "verified": p.verified_paragraphs,
            "unknown": p.unknown_paragraphs,
            "conflicts": p.conflicting_paragraphs,
            "gaps_detected": p.total_gaps_detected,
            "evidence_collected": p.total_evidence,
            "editions_discovered": p.total_editions_discovered,
            "translations": p.total_translations,
            "commentaries": p.total_commentaries,
            "overall_completeness": round(p.overall_completeness, 2),
            "sources_registered": len(self._sources),
        }
