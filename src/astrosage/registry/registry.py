"""
Knowledge Registry — Permanent ID system for the AstroSage Knowledge Engine.

Every artifact receives a permanent, traceable ID:
  BOOK-000001 → PAGE-000001 → SECTION-000001 → CHUNK-000001 → EMBEDDING-000001

IDs are deterministic: based on SHA256 of source content.
If the same document is re-imported, it keeps the same ID.
This makes the registry idempotent and reproducible.
"""
from __future__ import annotations

import hashlib
import re
from dataclasses import dataclass, field
from typing import Optional


# ── ID Generation ──────────────────────────────────────────────────────────

def _deterministic_id(prefix: str, content: str, counter: int) -> str:
    """
    Generate a deterministic ID from content hash.
    
    The counter ensures uniqueness within the same content scope.
    ID format: PREFIX-XXXXXXXX (8-char hex from SHA256)
    """
    hash_input = f"{prefix}:{content}:{counter}".encode("utf-8")
    hash_hex = hashlib.sha256(hash_input).hexdigest()[:8]
    return f"{prefix.upper()}-{hash_hex}"


def book_id(sha256: str) -> str:
    """Generate a stable BOOK ID from SHA256."""
    return _deterministic_id("BOOK", sha256, 0)


def page_id(book_id_val: str, page_number: int) -> str:
    """Generate a stable PAGE ID."""
    return _deterministic_id("PAGE", f"{book_id_val}:{page_number}", 0)


def section_id(book_id_val: str, section_path: str) -> str:
    """Generate a stable SECTION ID."""
    return _deterministic_id("SECTION", f"{book_id_val}:{section_path}", 0)


def chunk_id(book_id_val: str, chunk_index: int, text_hash: str) -> str:
    """Generate a stable CHUNK ID."""
    return _deterministic_id("CHUNK", f"{book_id_val}:{chunk_index}:{text_hash}", 0)


def embedding_id(chunk_id_val: str) -> str:
    """Generate a stable EMBEDDING ID."""
    return _deterministic_id("EMBED", chunk_id_val, 0)


def answer_id(query_hash: str, context_hash: str) -> str:
    """Generate a stable ANSWER ID."""
    return _deterministic_id("ANSWER", f"{query_hash}:{context_hash}", 0)


# ── Registry ───────────────────────────────────────────────────────────────

@dataclass
class RegistryEntry:
    """A single entry in the Knowledge Registry."""
    artifact_id: str
    artifact_type: str  # BOOK, PAGE, SECTION, CHUNK, EMBEDDING, ANSWER
    parent_id: Optional[str] = None
    source_sha256: str = ""
    source_path: str = ""
    metadata: dict = field(default_factory=dict)


class KnowledgeRegistry:
    """
    Permanent ID registry for all knowledge artifacts.
    
    Design principles:
    1. IDs are deterministic (same content = same ID)
    2. IDs are immutable (never change once assigned)
    3. Every artifact traces to its source document
    4. Registry is reproducible from raw data alone
    """
    
    def __init__(self):
        self._entries: dict[str, RegistryEntry] = {}
        self._content_to_id: dict[str, str] = {}  # SHA256 → artifact_id
        self._next_counter: dict[str, int] = {}  # prefix → next counter
    
    def register_book(self, sha256: str, metadata: dict) -> str:
        """Register a book/document and return its BOOK ID."""
        if sha256 in self._content_to_id:
            return self._content_to_id[sha256]
        
        bid = book_id(sha256)
        self._entries[bid] = RegistryEntry(
            artifact_id=bid,
            artifact_type="BOOK",
            source_sha256=sha256,
            source_path=metadata.get("source_path", ""),
            metadata=metadata,
        )
        self._content_to_id[sha256] = bid
        return bid
    
    def register_page(self, book_id_val: str, page_number: int, metadata: dict) -> str:
        """Register a page and return its PAGE ID."""
        pid = page_id(book_id_val, page_number)
        self._entries[pid] = RegistryEntry(
            artifact_id=pid,
            artifact_type="PAGE",
            parent_id=book_id_val,
            source_sha256=metadata.get("sha256", ""),
            source_path=metadata.get("source_path", ""),
            metadata=metadata,
        )
        return pid
    
    def register_section(
        self, book_id_val: str, section_path: str, metadata: dict
    ) -> str:
        """Register a section and return its SECTION ID."""
        sid = section_id(book_id_val, section_path)
        self._entries[sid] = RegistryEntry(
            artifact_id=sid,
            artifact_type="SECTION",
            parent_id=book_id_val,
            source_sha256=metadata.get("sha256", ""),
            metadata=metadata,
        )
        return sid
    
    def register_chunk(
        self, book_id_val: str, chunk_index: int, text: str, metadata: dict
    ) -> str:
        """Register a chunk and return its CHUNK ID."""
        text_hash = hashlib.sha256(text.encode("utf-8")).hexdigest()[:16]
        cid = chunk_id(book_id_val, chunk_index, text_hash)
        self._entries[cid] = RegistryEntry(
            artifact_id=cid,
            artifact_type="CHUNK",
            parent_id=book_id_val,
            source_sha256=text_hash,
            metadata={**metadata, "text_preview": text[:200]},
        )
        return cid
    
    def register_embedding(self, chunk_id_val: str, metadata: dict) -> str:
        """Register an embedding and return its EMBEDDING ID."""
        eid = embedding_id(chunk_id_val)
        self._entries[eid] = RegistryEntry(
            artifact_id=eid,
            artifact_type="EMBEDDING",
            parent_id=chunk_id_val,
            metadata=metadata,
        )
        return eid
    
    def get_entry(self, artifact_id: str) -> Optional[RegistryEntry]:
        return self._entries.get(artifact_id)
    
    def get_children(self, artifact_id: str) -> list[RegistryEntry]:
        return [e for e in self._entries.values() if e.parent_id == artifact_id]
    
    def get_book_pages(self, book_id_val: str) -> list[RegistryEntry]:
        return [e for e in self._entries.values() if e.parent_id == book_id_val and e.artifact_type == "PAGE"]
    
    def get_book_chunks(self, book_id_val: str) -> list[RegistryEntry]:
        """Get all chunks for a book (recursive through sections)."""
        pages = self.get_book_pages(book_id_val)
        chunks = []
        for page in pages:
            children = self.get_children(page.artifact_id)
            for child in children:
                if child.artifact_type == "CHUNK":
                    chunks.append(child)
                # Also check for section → chunk
                grandchildren = self.get_children(child.artifact_id)
                for gc in grandchildren:
                    if gc.artifact_type == "CHUNK":
                        chunks.append(gc)
        return chunks
    
    @property
    def total_entries(self) -> int:
        return len(self._entries)
    
    @property
    def books(self) -> list[RegistryEntry]:
        return [e for e in self._entries.values() if e.artifact_type == "BOOK"]
    
    @property
    def pages(self) -> list[RegistryEntry]:
        return [e for e in self._entries.values() if e.artifact_type == "PAGE"]
    
    @property
    def chunks(self) -> list[RegistryEntry]:
        return [e for e in self._entries.values() if e.artifact_type == "CHUNK"]
    
    def to_dict(self) -> dict:
        """Serialize registry to dict."""
        return {
            aid: {
                "artifact_id": e.artifact_id,
                "artifact_type": e.artifact_type,
                "parent_id": e.parent_id,
                "source_sha256": e.source_sha256,
                "source_path": e.source_path,
                "metadata": e.metadata,
            }
            for aid, e in self._entries.items()
        }
    
    def summary(self) -> dict:
        """Get registry statistics."""
        types = {}
        for e in self._entries.values():
            types[e.artifact_type] = types.get(e.artifact_type, 0) + 1
        return {
            "total_entries": self.total_entries,
            "by_type": types,
            "books": len(self.books),
            "pages": len(self.pages),
            "chunks": len(self.chunks),
        }
