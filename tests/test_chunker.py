"""Tests for the semantic chunker."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from astrosage.chunking.chunker import SemanticChunker
from astrosage.models import Document, DocumentMetadata, PageContent


def test_chunker_empty_page():
    chunker = SemanticChunker(max_tokens=100)
    page = PageContent(page_number=1, text="")
    chunks = chunker._chunk_page(page, "doc_1", min_chunk_length=50)
    assert len(chunks) == 0


def test_chunker_short_page():
    chunker = SemanticChunker(max_tokens=100)
    page = PageContent(page_number=1, text="Short text.")
    chunks = chunker._chunk_page(page, "doc_1", min_chunk_length=50)
    assert len(chunks) == 0  # Too short for min_chunk_length


def test_chunker_paragraph_split():
    chunker = SemanticChunker(max_tokens=200, overlap_tokens=0)
    long_text = "\n\n".join([
        f"This is paragraph {i}. " * 20
        for i in range(5)
    ])
    doc = Document(
        metadata=DocumentMetadata(source_filename="test.pdf"),
        pages=[PageContent(page_number=1, text=long_text)],
    )
    chunks = chunker.chunk_document(doc, min_chunk_length=10)
    assert len(chunks) > 1


def test_chunker_preserves_page_numbers():
    chunker = SemanticChunker(max_tokens=200)
    doc = Document(
        metadata=DocumentMetadata(source_filename="test.pdf"),
        pages=[
            PageContent(page_number=1, text="Page 1 content. " * 30),
            PageContent(page_number=2, text="Page 2 content. " * 30),
        ],
    )
    chunks = chunker.chunk_document(doc)
    page_numbers = set()
    for c in chunks:
        page_numbers.update(c.page_numbers)
    assert 1 in page_numbers
    assert 2 in page_numbers


def test_chunker_assigns_ids():
    chunker = SemanticChunker(max_tokens=200)
    doc = Document(
        metadata=DocumentMetadata(source_filename="test.pdf"),
        pages=[PageContent(page_number=1, text="Test content. " * 30)],
    )
    chunks = chunker.chunk_document(doc)
    for chunk in chunks:
        assert chunk.chunk_id.startswith("chunk_")


def test_chunker_computes_sha256():
    chunker = SemanticChunker(max_tokens=200)
    doc = Document(
        metadata=DocumentMetadata(source_filename="test.pdf"),
        pages=[PageContent(page_number=1, text="Test content for hashing. " * 20)],
    )
    chunks = chunker.chunk_document(doc)
    for chunk in chunks:
        assert len(chunk.sha256) == 64
