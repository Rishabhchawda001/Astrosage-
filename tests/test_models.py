"""Tests for core data models."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from astrosage.models import (
    Chunk,
    Citation,
    Confidence,
    Document,
    DocumentMetadata,
    DocumentType,
    GroundingResult,
    OCRStatus,
    PageContent,
    QueryRequest,
    QueryResponse,
    RetrievalResult,
    Script,
    generate_id,
)


def test_generate_id():
    id1 = generate_id("doc")
    id2 = generate_id("doc")
    assert id1.startswith("doc_")
    assert id1 != id2


def test_document_metadata_defaults():
    meta = DocumentMetadata()
    assert meta.document_id.startswith("doc_")
    assert meta.document_type == DocumentType.UNKNOWN
    assert meta.ocr_status == OCRStatus.NOT_NEEDED


def test_page_content():
    page = PageContent(page_number=1, text="Hello world")
    assert page.page_number == 1
    assert page.text == "Hello world"


def test_document_full_text():
    doc = Document(
        metadata=DocumentMetadata(source_filename="test.pdf"),
        pages=[
            PageContent(page_number=1, text="Page one content"),
            PageContent(page_number=2, text="Page two content"),
        ],
    )
    assert "Page one content" in doc.full_text
    assert "Page two content" in doc.full_text
    assert doc.word_count == 6


def test_chunk_sha256():
    chunk = Chunk(document_id="doc_123", text="Test text for hashing")
    sha = chunk.compute_sha256()
    assert len(sha) == 64  # SHA256 hex digest


def test_query_request():
    req = QueryRequest(query="What is Ayurveda?")
    assert req.top_k == 10
    assert req.rerank_top_k == 5


def test_retrieval_result():
    result = RetrievalResult(
        chunk=Chunk(document_id="doc_1", text="test"),
        score=0.95,
        rank=1,
        confidence=Confidence.HIGH,
    )
    assert result.score == 0.95
    assert result.confidence == Confidence.HIGH


def test_citation():
    citation = Citation(
        document_id="doc_1",
        document_title="Bhagavad Gita",
        page_numbers=[1, 2],
        text_snippet="In the beginning...",
        confidence=Confidence.HIGH,
    )
    assert citation.document_title == "Bhagavad Gita"
