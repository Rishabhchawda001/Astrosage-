"""
Citation Management Engine.

Manages citations across the knowledge corpus. Tracks source references,
cross-references, and citation integrity.
"""
from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Optional


class CitationType(str, Enum):
    PRIMARY = "primary"
    SECONDARY = "secondary"
    CROSS_REFERENCE = "cross_reference"
    COMMENTARY = "commentary"
    TRANSLATION = "translation"
    ACADEMIC = "academic"
    EXTERNAL = "external"


class CitationStatus(str, Enum):
    VALID = "valid"
    BROKEN = "broken"
    UNVERIFIED = "unverified"
    CONFLICTED = "conflicted"


@dataclass
class Citation:
    citation_id: str = ""
    knowledge_uuid: str = ""
    book_uuid: str = ""
    citation_type: CitationType = CitationType.PRIMARY
    status: CitationStatus = CitationStatus.UNVERIFIED
    source_title: str = ""
    source_author: str = ""
    source_publisher: str = ""
    source_year: str = ""
    source_edition: str = ""
    source_language: str = ""
    source_isbn: str = ""
    source_url: str = ""
    source_doi: str = ""
    page_reference: str = ""
    chapter_reference: str = ""
    verse_reference: str = ""
    volume: str = ""
    confidence: float = 0.0
    verified: bool = False
    verified_at: str = ""
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    metadata: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self):
        if not self.citation_id:
            self.citation_id = f"CT-{uuid.uuid4().hex[:12]}"


class CitationEngine:
    """Production citation management engine."""

    def __init__(self):
        self._citations: dict[str, Citation] = {}
        self._by_knowledge: dict[str, list[str]] = {}
        self._by_book: dict[str, list[str]] = {}
        self._by_type: dict[str, list[str]] = {}
        self._by_status: dict[str, list[str]] = {}

    def add(self, knowledge_uuid: str, citation_type: CitationType = CitationType.PRIMARY,
            book_uuid: str = "", source_title: str = "", source_author: str = "",
            source_publisher: str = "", source_year: str = "", source_edition: str = "",
            source_language: str = "", page_reference: str = "", chapter_reference: str = "",
            verse_reference: str = "", confidence: float = 0.0, **kwargs) -> Citation:
        citation = Citation(
            knowledge_uuid=knowledge_uuid, book_uuid=book_uuid,
            citation_type=citation_type, source_title=source_title,
            source_author=source_author, source_publisher=source_publisher,
            source_year=source_year, source_edition=source_edition,
            source_language=source_language, page_reference=page_reference,
            chapter_reference=chapter_reference, verse_reference=verse_reference,
            confidence=confidence, metadata=kwargs)
        self._citations[citation.citation_id] = citation
        self._by_knowledge.setdefault(knowledge_uuid, []).append(citation.citation_id)
        if book_uuid:
            self._by_book.setdefault(book_uuid, []).append(citation.citation_id)
        self._by_type.setdefault(citation_type.value, []).append(citation.citation_id)
        self._by_status.setdefault(citation.status.value, []).append(citation.citation_id)
        return citation

    def verify(self, citation_id: str, verified: bool = True) -> bool:
        citation = self._citations.get(citation_id)
        if citation:
            citation.verified = verified
            citation.status = CitationStatus.VALID if verified else CitationStatus.BROKEN
            citation.verified_at = datetime.now(timezone.utc).isoformat()
            return True
        return False

    def get_citation(self, citation_id: str) -> Citation | None:
        return self._citations.get(citation_id)

    def get_by_knowledge(self, knowledge_uuid: str) -> list[Citation]:
        ids = self._by_knowledge.get(knowledge_uuid, [])
        return [self._citations[cid] for cid in ids if cid in self._citations]

    def get_by_book(self, book_uuid: str) -> list[Citation]:
        ids = self._by_book.get(book_uuid, [])
        return [self._citations[cid] for cid in ids if cid in self._citations]

    def get_broken(self) -> list[Citation]:
        return [c for c in self._citations.values() if c.status == CitationStatus.BROKEN]

    def get_unverified(self) -> list[Citation]:
        return [c for c in self._citations.values() if c.status == CitationStatus.UNVERIFIED]

    def citation_integrity(self, book_uuid: str) -> dict:
        book_cites = self.get_by_book(book_uuid)
        if not book_cites:
            return {"book_uuid": book_uuid, "total": 0, "verified": 0, "broken": 0, "integrity": 0.0}
        verified = sum(1 for c in book_cites if c.verified)
        broken = sum(1 for c in book_cites if c.status == CitationStatus.BROKEN)
        integrity = verified / len(book_cites) * 100
        return {"book_uuid": book_uuid, "total": len(book_cites),
                "verified": verified, "broken": broken, "integrity": integrity}

    def count(self) -> int:
        return len(self._citations)

    def summary(self) -> dict:
        tc: dict[str, int] = {}
        sc: dict[str, int] = {}
        for c in self._citations.values():
            tc[c.citation_type.value] = tc.get(c.citation_type.value, 0) + 1
            sc[c.status.value] = sc.get(c.status.value, 0) + 1
        return {"total": self.count(), "by_type": tc, "by_status": sc}
