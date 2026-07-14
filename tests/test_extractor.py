"""Tests for document extraction."""
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from astrosage.ingestion.extractor import (
    detect_document_type,
    detect_script,
    extract_text_file,
    _is_native_pdf,
)
from astrosage.models import DocumentType, Script


def test_detect_document_type_pdf():
    assert detect_document_type(Path("test.pdf")) == DocumentType.PDF


def test_detect_document_type_docx():
    assert detect_document_type(Path("test.docx")) == DocumentType.DOCX


def test_detect_document_type_txt():
    assert detect_document_type(Path("test.txt")) == DocumentType.TXT


def test_detect_document_type_unknown():
    assert detect_document_type(Path("test.xyz")) == DocumentType.UNKNOWN


def test_detect_script_devanagari():
    text = "नमस्ते भारत"
    assert detect_script(text) == Script.DEVANAGARI


def test_detect_script_latin():
    text = "Hello World this is English text"
    assert detect_script(text) == Script.LATIN


def test_detect_script_mixed():
    text = "Hello नमस्ते World भारत"
    assert detect_script(text) == Script.MIXED


def test_detect_script_empty():
    assert detect_script("") == Script.UNKNOWN


def test_extract_text_file():
    with tempfile.NamedTemporaryFile(
        mode="w", suffix=".txt", delete=False, encoding="utf-8"
    ) as f:
        f.write("This is a test document.\n\nSecond paragraph.")
        tmp_path = Path(f.name)

    try:
        doc = extract_text_file(tmp_path)
        assert len(doc.pages) == 1
        assert "test document" in doc.pages[0].text
        assert doc.metadata.document_type == DocumentType.TXT
    finally:
        tmp_path.unlink()


def test_extract_markdown():
    with tempfile.NamedTemporaryFile(
        mode="w", suffix=".md", delete=False, encoding="utf-8"
    ) as f:
        f.write("# Title\n\nSome content here.\n\n## Section\n\nMore content.")
        tmp_path = Path(f.name)

    try:
        doc = extract_text_file(tmp_path)
        assert doc.metadata.document_type == DocumentType.MARKDOWN
        assert "Title" in doc.pages[0].text
    finally:
        tmp_path.unlink()
