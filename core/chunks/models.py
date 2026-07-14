"""
Chunk Models — Data models for chunks and chunk metadata.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from core.chunking.engine import Chunk, ChunkType


@dataclass
class ChunkMetadata:
    """Extended metadata for a chunk."""
    chunk_id: str = ""
    source_file: str = ""
    page_start: int = 0
    page_end: int = 0
    column: str = ""
    bbox: str = ""
    ocr_confidence: float = 0.0
    parser_confidence: float = 0.0
    original_ocr: str = ""
    recovered_text: str = ""
    pipeline_version: str = ""
    processing_timestamp: str = ""
    embedding_ready: bool = False
    indexed: bool = False
    graph_linked: bool = False
    extra: dict[str, Any] = field(default_factory=dict)


@dataclass
class ChunkEmbeddingInterface:
    """Interface data for future embedding generation."""
    chunk_id: str = ""
    text: str = ""
    context: str = ""
    metadata: dict[str, Any] = field(default_factory=dict)
    hierarchy_path: str = ""
    language: str = ""
    chunk_type: str = ""
    evidence_refs: list[str] = field(default_factory=list)
    graph_refs: list[str] = field(default_factory=list)
    passport_id: str = ""

    def to_embedding_input(self) -> dict[str, Any]:
        return {
            "id": self.chunk_id,
            "text": self.text,
            "context": self.context,
            "metadata": self.metadata,
            "hierarchy_path": self.hierarchy_path,
            "language": self.language,
        }


@dataclass
class ChunkSearchInterface:
    """Interface data for future search integration."""
    chunk_id: str = ""
    text: str = ""
    language: str = ""
    chunk_type: str = ""
    hierarchy_path: str = ""
    confidence: float = 0.0
    trust_score: float = 0.0
    evidence_refs: list[str] = field(default_factory=list)
    graph_refs: list[str] = field(default_factory=list)
    ontology_refs: list[str] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_search_index(self) -> dict[str, Any]:
        return {
            "chunk_id": self.chunk_id,
            "text": self.text,
            "language": self.language,
            "chunk_type": self.chunk_type,
            "hierarchy_path": self.hierarchy_path,
            "confidence": self.confidence,
        }
