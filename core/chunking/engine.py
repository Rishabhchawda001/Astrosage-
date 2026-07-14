"""
Chunking Engine — Semantic chunking of verified knowledge.

Chunks are NEVER fixed token windows. They follow document hierarchy,
semantic boundaries, knowledge boundaries, and linguistic structure.
Never splits a logical knowledge unit.
"""
from __future__ import annotations

import hashlib
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Optional


class ChunkType(str, Enum):
    BOOK = "book"
    VOLUME = "volume"
    SECTION = "section"
    CHAPTER = "chapter"
    SUBCHAPTER = "subchapter"
    VERSE = "verse"
    SLOKA = "sloka"
    PARAGRAPH = "paragraph"
    COMMENTARY = "commentary"
    FOOTNOTE = "footnote"
    APPENDIX = "appendix"
    GLOSSARY = "glossary"
    CONCEPT = "concept"
    DEFINITION = "definition"
    BIOGRAPHY = "biography"
    TIMELINE = "timeline"
    RELATIONSHIP = "relationship"
    KNOWLEDGE_UNIT = "knowledge_unit"


class ChunkBoundaryStrategy(str, Enum):
    HIERARCHY = "hierarchy"
    SEMANTIC = "semantic"
    VERSE = "verse"
    SECTION = "section"
    CONCEPT = "concept"
    EDITION = "edition"
    LANGUAGE = "language"
    COMMENTARY = "commentary"
    MANUAL = "manual"


@dataclass
class Chunk:
    """A permanent knowledge chunk — the fundamental unit of AstroSage knowledge."""
    chunk_id: str = ""
    canonical_id: str = ""
    passport_id: str = ""
    book_id: str = ""
    edition_id: str = ""
    language: str = ""
    script: str = ""
    chunk_type: ChunkType = ChunkType.KNOWLEDGE_UNIT
    text: str = ""
    text_hash: str = ""
    parent_id: str = ""
    child_ids: list[str] = field(default_factory=list)
    ancestor_ids: list[str] = field(default_factory=list)
    descendant_ids: list[str] = field(default_factory=list)
    hierarchy_path: str = ""
    evidence_refs: list[str] = field(default_factory=list)
    citation_refs: list[str] = field(default_factory=list)
    ontology_refs: list[str] = field(default_factory=list)
    graph_refs: list[str] = field(default_factory=list)
    confidence: float = 0.0
    trust_score: float = 0.0
    version: int = 1
    checksum: str = ""
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    updated_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    metadata: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self):
        if not self.chunk_id:
            self.chunk_id = f"CH-{uuid.uuid4().hex[:12]}"
        if not self.text_hash:
            self.text_hash = hashlib.sha256(self.text.encode("utf-8")).hexdigest()
        if not self.checksum:
            self.checksum = self.text_hash

    @property
    def word_count(self) -> int:
        return len(self.text.split()) if self.text else 0

    @property
    def char_count(self) -> int:
        return len(self.text)

    @property
    def is_leaf(self) -> bool:
        return len(self.child_ids) == 0

    @property
    def depth(self) -> int:
        return len(self.ancestor_ids)

    def add_child(self, child_id: str) -> None:
        if child_id not in self.child_ids:
            self.child_ids.append(child_id)

    def remove_child(self, child_id: str) -> None:
        if child_id in self.child_ids:
            self.child_ids.remove(child_id)

    def to_dict(self) -> dict[str, Any]:
        return {
            "chunk_id": self.chunk_id,
            "canonical_id": self.canonical_id,
            "passport_id": self.passport_id,
            "book_id": self.book_id,
            "edition_id": self.edition_id,
            "language": self.language,
            "chunk_type": self.chunk_type.value,
            "text_hash": self.text_hash,
            "parent_id": self.parent_id,
            "child_count": len(self.child_ids),
            "hierarchy_path": self.hierarchy_path,
            "confidence": self.confidence,
            "trust_score": self.trust_score,
            "version": self.version,
            "word_count": self.word_count,
            "created_at": self.created_at,
        }


@dataclass
class ChunkingConfig:
    """Configuration for chunking behavior."""
    strategy: ChunkBoundaryStrategy = ChunkBoundaryStrategy.HIERARCHY
    max_chunk_size: int = 5000
    min_chunk_size: int = 50
    preserve_verses: bool = True
    preserve_commentary: bool = True
    preserve_structure: bool = True
    languages: list[str] = field(default_factory=lambda: ["english", "hindi", "sanskrit"])
    chunk_types: list[ChunkType] = field(default_factory=lambda: list(ChunkType))
    metadata: dict[str, Any] = field(default_factory=dict)


class ChunkingEngine:
    """
    Production semantic chunking engine.

    Creates chunks from verified knowledge using hierarchy and semantic boundaries.
    Never uses fixed token windows.
    """

    def __init__(self, config: ChunkingConfig | None = None):
        self.config = config or ChunkingConfig()
        self._chunks: dict[str, Chunk] = {}

    def create_chunk(self, **kwargs) -> Chunk:
        chunk = Chunk(**kwargs)
        self._chunks[chunk.chunk_id] = chunk
        return chunk

    def create_hierarchical_chunk(
        self,
        text: str,
        chunk_type: ChunkType,
        language: str = "",
        parent_id: str = "",
        book_id: str = "",
        edition_id: str = "",
        passport_id: str = "",
        **kwargs,
    ) -> Chunk:
        chunk = Chunk(
            text=text,
            chunk_type=chunk_type,
            language=language,
            book_id=book_id,
            edition_id=edition_id,
            passport_id=passport_id,
            **kwargs,
        )
        if parent_id:
            chunk.parent_id = parent_id
            if parent_id in self._chunks:
                parent = self._chunks[parent_id]
                chunk.ancestor_ids = list(parent.ancestor_ids) + [parent.chunk_id]
                parent.add_child(chunk.chunk_id)
                chunk.hierarchy_path = f"{parent.hierarchy_path}/{chunk_type.value}"
        else:
            chunk.hierarchy_path = chunk_type.value

        self._chunks[chunk.chunk_id] = chunk
        return chunk

    def split_by_hierarchy(self, document_chunks: list[dict[str, Any]], book_id: str = "") -> list[Chunk]:
        """Split a document into hierarchical chunks based on structure markers."""
        results = []
        current_parent = ""
        current_type = ChunkType.BOOK
        for item in document_chunks:
            chunk_type = ChunkType(item.get("type", "paragraph"))
            chunk = self.create_hierarchical_chunk(
                text=item.get("text", ""),
                chunk_type=chunk_type,
                language=item.get("language", ""),
                parent_id=current_parent,
                book_id=book_id or item.get("book_id", ""),
                edition_id=item.get("edition_id", ""),
            )
            if chunk_type in (ChunkType.BOOK, ChunkType.CHAPTER, ChunkType.SECTION):
                current_parent = chunk.chunk_id
                current_type = chunk_type
            results.append(chunk)
        return results

    def split_by_verses(self, text: str, language: str = "", book_id: str = "", parent_id: str = "") -> list[Chunk]:
        """Split text into verse-based chunks."""
        import re
        patterns = {
            "sanskrit": "[॥।]+",
            "hindi": "[॥।]+",
            "english": "\n\n+",
        }
        pattern = patterns.get(language, "\n\n+")
        parts = [p.strip() for p in re.split(pattern, text) if p.strip()]
        chunks = []
        for i, part in enumerate(parts):
            chunk = self.create_hierarchical_chunk(
                text=part,
                chunk_type=ChunkType.VERSE if language in ("sanskrit", "hindi") else ChunkType.PARAGRAPH,
                language=language,
                parent_id=parent_id,
                book_id=book_id,
            )
            chunks.append(chunk)
        return chunks

    def get_chunk(self, chunk_id: str) -> Optional[Chunk]:
        return self._chunks.get(chunk_id)

    def get_children(self, chunk_id: str) -> list[Chunk]:
        chunk = self._chunks.get(chunk_id)
        if not chunk:
            return []
        return [self._chunks[cid] for cid in chunk.child_ids if cid in self._chunks]

    def get_ancestors(self, chunk_id: str) -> list[Chunk]:
        chunk = self._chunks.get(chunk_id)
        if not chunk:
            return []
        return [self._chunks[aid] for aid in chunk.ancestor_ids if aid in self._chunks]

    def get_descendants(self, chunk_id: str) -> list[Chunk]:
        result = []
        children = self.get_children(chunk_id)
        result.extend(children)
        for child in children:
            result.extend(self.get_descendants(child.chunk_id))
        return result

    def get_by_type(self, chunk_type: ChunkType) -> list[Chunk]:
        return [c for c in self._chunks.values() if c.chunk_type == chunk_type]

    def get_by_language(self, language: str) -> list[Chunk]:
        return [c for c in self._chunks.values() if c.language == language]

    def get_by_book(self, book_id: str) -> list[Chunk]:
        return [c for c in self._chunks.values() if c.book_id == book_id]

    def get_by_passport(self, passport_id: str) -> list[Chunk]:
        return [c for c in self._chunks.values() if c.passport_id == passport_id]

    def count(self) -> int:
        return len(self._chunks)

    def summary(self) -> dict:
        type_counts: dict[str, int] = {}
        lang_counts: dict[str, int] = {}
        for c in self._chunks.values():
            type_counts[c.chunk_type.value] = type_counts.get(c.chunk_type.value, 0) + 1
            lang_counts[c.language] = lang_counts.get(c.language, 0) + 1
        return {
            "total_chunks": self.count(),
            "by_type": type_counts,
            "by_language": lang_counts,
        }
