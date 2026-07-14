"""
Canonical Layer — Layer 3 of the Knowledge Lake.

Never overwrites Bronze or Silver.
Creates a new verified canonical layer.
"""
from __future__ import annotations

import hashlib
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional


@dataclass
class CanonicalParagraph:
    paragraph_id: str = ""
    knowledge_uuid: str = ""
    book_uuid: str = ""
    chapter: str = ""
    page: int = 0
    paragraph_index: int = 0
    text: str = ""
    text_hash: str = ""
    language: str = ""
    confidence: float = 0.0
    evidence_count: int = 0
    edition_count: int = 0
    truth_status: str = "pending"
    provenance: list[str] = field(default_factory=list)
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    metadata: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self):
        if not self.paragraph_id:
            self.paragraph_id = f"CP-{uuid.uuid4().hex[:12]}"
        if not self.text_hash and self.text:
            self.text_hash = hashlib.sha256(self.text.encode("utf-8")).hexdigest()[:16]


class CanonicalEngine:
    """Production canonical layer engine. Creates Layer 3 without modifying Layers 1-2."""

    def __init__(self, canonical_dir: str = "knowledge/canonical"):
        self.canonical_dir = Path(canonical_dir)
        self.canonical_dir.mkdir(parents=True, exist_ok=True)
        self._paragraphs: dict[str, CanonicalParagraph] = {}
        self._by_book: dict[str, list[str]] = {}
        self._by_knowledge: dict[str, list[str]] = {}

    def add_paragraph(self, **kwargs) -> CanonicalParagraph:
        p = CanonicalParagraph(**kwargs)
        self._paragraphs[p.paragraph_id] = p
        self._by_book.setdefault(p.book_uuid, []).append(p.paragraph_id)
        self._by_knowledge.setdefault(p.knowledge_uuid, []).append(p.paragraph_id)
        return p

    def get_paragraph(self, paragraph_id: str) -> Optional[CanonicalParagraph]:
        return self._paragraphs.get(paragraph_id)

    def get_by_book(self, book_uuid: str) -> list[CanonicalParagraph]:
        ids = self._by_book.get(book_uuid, [])
        return [self._paragraphs[pid] for pid in ids if pid in self._paragraphs]

    def get_by_knowledge(self, knowledge_uuid: str) -> list[CanonicalParagraph]:
        ids = self._by_knowledge.get(knowledge_uuid, [])
        return [self._paragraphs[pid] for pid in ids if pid in self._paragraphs]

    def count(self) -> int: return len(self._paragraphs)

    def summary(self) -> dict:
        ts: dict[str, int] = {}
        for p in self._paragraphs.values(): ts[p.truth_status] = ts.get(p.truth_status, 0) + 1
        return {"total_paragraphs": self.count(), "by_truth_status": ts, "books": len(self._by_book)}
