"""
AstroSage Knowledge Engine — Core data models.

All models use Pydantic v2 for validation and serialization.
Every entity has a persistent ID, SHA256 hash, and full provenance chain.
"""
from __future__ import annotations

import hashlib
import uuid
from datetime import datetime, timezone
from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field, computed_field


def generate_id(prefix: str = "doc") -> str:
    return f"{prefix}_{uuid.uuid4().hex[:12]}"


def now_utc() -> str:
    return datetime.now(timezone.utc).isoformat()


# ── Enums ──────────────────────────────────────────────────────────────────

class DocumentType(str, Enum):
    PDF = "pdf"
    DOCX = "docx"
    EPUB = "epub"
    TXT = "txt"
    MARKDOWN = "markdown"
    IMAGE = "image"
    ZIP = "zip"
    UNKNOWN = "unknown"


class OCRStatus(str, Enum):
    NOT_NEEDED = "not_needed"
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    REVIEW_NEEDED = "review_needed"


class Script(str, Enum):
    DEVANAGARI = "devanagari"
    LATIN = "latin"
    MIXED = "mixed"
    UNKNOWN = "unknown"


class Confidence(str, Enum):
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


# ── Document Models ────────────────────────────────────────────────────────

class DocumentMetadata(BaseModel):
    """Full metadata for a document in the knowledge base."""
    document_id: str = Field(default_factory=lambda: generate_id("doc"))
    sha256: str = ""
    source_filename: str = ""
    source_path: str = ""
    source_gdrive_id: str = ""
    book_title: str = ""
    author: str = ""
    publisher: str = ""
    edition: str = ""
    language: str = ""
    script: Script = Script.UNKNOWN
    document_type: DocumentType = DocumentType.UNKNOWN
    ocr_status: OCRStatus = OCRStatus.NOT_NEEDED
    ocr_confidence: float = 0.0
    ocr_engine: str = ""
    import_timestamp: str = Field(default_factory=now_utc)
    pipeline_version: str = "0.1.0"
    page_count: int = 0
    file_size_bytes: int = 0
    last_modified: str = ""
    tags: list[str] = Field(default_factory=list)
    folder_path: str = ""


class PageContent(BaseModel):
    """Content extracted from a single page."""
    page_number: int
    text: str = ""
    has_images: bool = False
    has_tables: bool = False
    ocr_confidence: float = 0.0
    ocr_engine: str = ""
    language_detected: str = ""


class Document(BaseModel):
    """A complete document with all its pages."""
    metadata: DocumentMetadata
    pages: list[PageContent] = Field(default_factory=list)

    @computed_field
    @property
    def full_text(self) -> str:
        return "\n\n".join(p.text for p in self.pages if p.text)

    @computed_field
    @property
    def word_count(self) -> int:
        return len(self.full_text.split())


# ── Chunk Models ───────────────────────────────────────────────────────────

class Chunk(BaseModel):
    """A semantic chunk of text with full provenance."""
    chunk_id: str = Field(default_factory=lambda: generate_id("chunk"))
    document_id: str
    text: str
    page_numbers: list[int] = Field(default_factory=list)
    chapter: str = ""
    section: str = ""
    subsection: str = ""
    start_char: int = 0
    end_char: int = 0
    token_count: int = 0
    language: str = ""
    sha256: str = ""

    def compute_sha256(self) -> str:
        self.sha256 = hashlib.sha256(self.text.encode("utf-8")).hexdigest()
        return self.sha256


# ── Query Models ───────────────────────────────────────────────────────────

class QueryRequest(BaseModel):
    query: str
    top_k: int = 10
    rerank_top_k: int = 5
    filters: dict = Field(default_factory=dict)
    language_preference: str = ""
    include_metadata: bool = True


class RetrievalResult(BaseModel):
    chunk: Chunk
    score: float
    rank: int
    source_metadata: Optional[DocumentMetadata] = None
    confidence: Confidence = Confidence.MEDIUM


class QueryResponse(BaseModel):
    query: str
    results: list[RetrievalResult]
    grounding: GroundingResult = Field(default_factory=lambda: GroundingResult())
    processing_time_ms: float = 0


class GroundingResult(BaseModel):
    """Result of grounding verification."""
    is_grounded: bool = False
    grounded_sentences: list[str] = Field(default_factory=list)
    ungrounded_sentences: list[str] = Field(default_factory=list)
    overall_confidence: Confidence = Confidence.LOW
    citations: list[Citation] = Field(default_factory=list)


class Citation(BaseModel):
    """A citation pointing to specific source material."""
    document_id: str
    document_title: str
    page_numbers: list[int] = Field(default_factory=list)
    chapter: str = ""
    section: str = ""
    text_snippet: str = ""
    confidence: Confidence = Confidence.MEDIUM


# ── Pipeline Models ────────────────────────────────────────────────────────

class IngestionStatus(BaseModel):
    """Status of the ingestion pipeline."""
    total_documents: int = 0
    ingested: int = 0
    ocr_pending: int = 0
    ocr_completed: int = 0
    ocr_failed: int = 0
    indexed: int = 0
    failed: int = 0
    last_run: str = ""
    errors: list[str] = Field(default_factory=list)


class BenchmarkResult(BaseModel):
    """Result of a technology benchmark."""
    technology: str
    category: str  # ocr, embedding, retrieval, etc.
    metric: str
    value: float
    unit: str = ""
    notes: str = ""
    timestamp: str = Field(default_factory=now_utc)
