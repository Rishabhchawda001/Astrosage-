"""
Knowledge Unit Engine — Atomic knowledge objects.

Decomposes every book into independent knowledge units:
character, word, sentence, verse, paragraph, section, chapter,
commentary, footnote, citation, metadata, concept, entity, relationship.
"""
from __future__ import annotations

import hashlib
import re
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Optional


class UnitType(str, Enum):
    CHARACTER = "character"
    WORD = "word"
    COMPOUND_WORD = "compound_word"
    SANSKRIT_PADA = "sanskrit_pada"
    VERSE_LINE = "verse_line"
    VERSE = "verse"
    SLOKA = "sloka"
    SENTENCE = "sentence"
    COMMENTARY_SENTENCE = "commentary_sentence"
    PARAGRAPH = "paragraph"
    SECTION = "section"
    CHAPTER = "chapter"
    BOOK = "book"
    FOOTNOTE = "footnote"
    CITATION = "citation"
    METADATA = "metadata"
    CROSS_REFERENCE = "cross_reference"
    HEADING = "heading"
    TABLE = "table"
    FIGURE = "figure"
    CAPTION = "caption"
    CONCEPT = "concept"
    ENTITY = "entity"


class UnitStatus(str, Enum):
    ORIGINAL = "original"
    VERIFIED = "verified"
    RECOVERED = "recovered"
    CONFLICTED = "conflicted"
    UNKNOWN = "unknown"
    REVIEW = "review"
    CANONICAL = "canonical"


@dataclass
class AtomicUnit:
    unit_id: str = ""
    unit_type: UnitType = UnitType.PARAGRAPH
    book_uuid: str = ""
    edition_uuid: str = ""
    chapter: str = ""
    section: str = ""
    page: int = 0
    paragraph_index: int = 0
    sentence_index: int = 0
    verse_number: str = ""
    text: str = ""
    text_hash: str = ""
    language: str = "unknown"
    status: UnitStatus = UnitStatus.ORIGINAL
    confidence: float = 0.0
    evidence_count: int = 0
    source_ids: list[str] = field(default_factory=list)
    variant_count: int = 0
    checksum: str = ""
    version: int = 1
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    updated_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    metadata: dict[str, Any] = field(default_factory=dict)
    parent_id: str = ""
    child_ids: list[str] = field(default_factory=list)

    def __post_init__(self):
        if not self.unit_id:
            self.unit_id = f"KU-{uuid.uuid4().hex[:12]}"
        if not self.text_hash and self.text:
            self.text_hash = hashlib.sha256(self.text.encode("utf-8")).hexdigest()[:16]
        if not self.checksum:
            self.checksum = self.text_hash


VERSE_PATTERN = re.compile(
    r'(?:^|\n)(?:Verse|Sloka|Shloka|Shlok|Verse\s+\d+|Sloka\s+\d+)[\s:：\-]*(\d+[a-z]?)\b',
    re.IGNORECASE)
SENTENCE_SPLIT = re.compile(r'(?<=[.!?।।])\s+')


def extract_units_from_text(text: str, book_uuid: str = "",
                            language: str = "unknown") -> list[AtomicUnit]:
    """Extract atomic knowledge units from text."""
    units = []
    paragraphs = [p.strip() for p in re.split(r'\n\s*\n', text) if p.strip()]

    for pidx, para in enumerate(paragraphs):
        para_id = f"KU-{uuid.uuid4().hex[:12]}"
        units.append(AtomicUnit(
            unit_id=para_id, unit_type=UnitType.PARAGRAPH,
            book_uuid=book_uuid, text=para, language=language,
            paragraph_index=pidx))

        if len(para) > 200:
            sentences = [s.strip() for s in SENTENCE_SPLIT.split(para) if s.strip()]
            for sidx, sent in enumerate(sentences):
                units.append(AtomicUnit(
                    unit_type=UnitType.SENTENCE, book_uuid=book_uuid,
                    text=sent, language=language, paragraph_index=pidx,
                    sentence_index=sidx, parent_id=para_id))

        words = para.split()
        if len(words) > 3:
            for word in words:
                if len(word) > 3:
                    units.append(AtomicUnit(
                        unit_type=UnitType.WORD, book_uuid=book_uuid,
                        text=word, language=language, paragraph_index=pidx,
                        parent_id=para_id))

        verse_matches = list(VERSE_PATTERN.finditer(para))
        if verse_matches:
            for vm in verse_matches:
                units.append(AtomicUnit(
                    unit_type=UnitType.VERSE, book_uuid=book_uuid,
                    text=vm.group(0).strip(), verse_number=vm.group(1),
                    language=language, paragraph_index=pidx,
                    parent_id=para_id))

    return units


class KnowledgeUnitEngine:
    """Production knowledge unit engine."""

    def __init__(self):
        self._units: dict[str, AtomicUnit] = {}
        self._by_book: dict[str, list[str]] = {}
        self._by_type: dict[str, list[str]] = {}
        self._by_status: dict[str, list[str]] = {}
        self._by_parent: dict[str, list[str]] = {}

    def add_unit(self, unit: AtomicUnit) -> AtomicUnit:
        self._units[unit.unit_id] = unit
        if unit.book_uuid:
            self._by_book.setdefault(unit.book_uuid, []).append(unit.unit_id)
        self._by_type.setdefault(unit.unit_type.value, []).append(unit.unit_id)
        self._by_status.setdefault(unit.status.value, []).append(unit.unit_id)
        if unit.parent_id:
            self._by_parent.setdefault(unit.parent_id, []).append(unit.unit_id)
        return unit

    def extract_from_text(self, text: str, book_uuid: str = "",
                          language: str = "unknown") -> list[AtomicUnit]:
        raw = extract_units_from_text(text, book_uuid, language)
        for u in raw:
            self.add_unit(u)
        return raw

    def get_unit(self, unit_id: str) -> AtomicUnit | None:
        return self._units.get(unit_id)

    def get_by_book(self, book_uuid: str) -> list[AtomicUnit]:
        ids = self._by_book.get(book_uuid, [])
        return [self._units[uid] for uid in ids if uid in self._units]

    def get_by_type(self, unit_type: UnitType) -> list[AtomicUnit]:
        ids = self._by_type.get(unit_type.value, [])
        return [self._units[uid] for uid in ids if uid in self._units]

    def get_by_status(self, status: UnitStatus) -> list[AtomicUnit]:
        ids = self._by_status.get(status.value, [])
        return [self._units[uid] for uid in ids if uid in self._units]

    def get_children(self, parent_id: str) -> list[AtomicUnit]:
        ids = self._by_parent.get(parent_id, [])
        return [self._units[uid] for uid in ids if uid in self._units]

    def update_status(self, unit_id: str, status: UnitStatus, confidence: float = 0.0) -> bool:
        unit = self._units.get(unit_id)
        if unit:
            old_status = unit.status.value
            unit.status = status
            if confidence > 0:
                unit.confidence = confidence
            unit.updated_at = datetime.now(timezone.utc).isoformat()
            if old_status in self._by_status:
                self._by_status[old_status] = [
                    uid for uid in self._by_status[old_status] if uid != unit_id]
            self._by_status.setdefault(status.value, []).append(unit_id)
            return True
        return False

    def count(self) -> int:
        return len(self._units)

    def summary(self) -> dict:
        tc: dict[str, int] = {}
        sc: dict[str, int] = {}
        for u in self._units.values():
            tc[u.unit_type.value] = tc.get(u.unit_type.value, 0) + 1
            sc[u.status.value] = sc.get(u.status.value, 0) + 1
        return {"total": self.count(), "by_type": tc, "by_status": sc,
                "books": len(self._by_book)}
