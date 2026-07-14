"""Phase 2 tests — Knowledge Lake foundation."""
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))


def test_knowledge_registry_book():
    from astrosage.registry.registry import KnowledgeRegistry
    reg = KnowledgeRegistry()
    bid = reg.register_book("abc123sha", {"title": "Test Book"})
    assert bid.startswith("BOOK-")
    assert reg.total_entries == 1
    assert len(reg.books) == 1


def test_knowledge_registry_idempotent():
    from astrosage.registry.registry import KnowledgeRegistry
    reg = KnowledgeRegistry()
    bid1 = reg.register_book("same_sha", {"title": "Book"})
    bid2 = reg.register_book("same_sha", {"title": "Book"})
    assert bid1 == bid2
    assert reg.total_entries == 1


def test_knowledge_registry_hierarchy():
    from astrosage.registry.registry import KnowledgeRegistry
    reg = KnowledgeRegistry()
    bid = reg.register_book("sha1", {"title": "Book"})
    pid = reg.register_page(bid, 1, {"text": "page 1"})
    cid = reg.register_chunk(bid, 0, "chunk text here", {"page": 1})
    assert pid.startswith("PAGE-")
    assert cid.startswith("CHUNK-")
    assert reg.total_entries == 3
    assert len(reg.get_book_pages(bid)) == 1


def test_knowledge_registry_summary():
    from astrosage.registry.registry import KnowledgeRegistry
    reg = KnowledgeRegistry()
    reg.register_book("sha1", {})
    reg.register_book("sha2", {})
    bid = reg.register_book("sha3", {})
    reg.register_page(bid, 1, {})
    summary = reg.summary()
    assert summary["books"] == 3
    assert summary["pages"] == 1


def test_classifier_text_file():
    from astrosage.classifier.classifier import classify_document
    with tempfile.NamedTemporaryFile(suffix=".txt", delete=False, mode="w") as f:
        f.write("Hello world test content")
        tmp = Path(f.name)
    try:
        result = classify_document(tmp)
        assert result.file_type == "text"
        assert result.is_valid
        assert not result.is_pdf
        assert not result.ocr_required
    finally:
        tmp.unlink()


def test_classifier_pdf():
    from astrosage.classifier.classifier import classify_document
    # Create a minimal PDF
    with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False, mode="wb") as f:
        f.write(b"%PDF-1.4\n1 0 obj<</Type/Catalog>>endobj\nxref\n0 0\ntrailer<</Root 1 0 R>>\nstartxref\n0\n%%EOF")
        tmp = Path(f.name)
    try:
        result = classify_document(tmp)
        assert result.is_pdf
        assert result.extension == ".pdf"
    finally:
        tmp.unlink()


def test_classifier_docx():
    from astrosage.classifier.classifier import classify_document
    # Create a minimal DOCX (ZIP with word/ content)
    import zipfile
    with tempfile.NamedTemporaryFile(suffix=".docx", delete=False) as f:
        tmp = Path(f.name)
    with zipfile.ZipFile(tmp, "w") as zf:
        zf.writestr("word/document.xml", "<w:document><w:body><w:p>Hello</w:p></w:body></w:document>")
    try:
        result = classify_document(tmp)
        assert result.file_type == "docx"
    finally:
        tmp.unlink()


def test_language_detection_english():
    from astrosage.language.detector import detect_language
    result = detect_language(
        "This is a test document in English with some content.",
        filename="test_english.txt",
    )
    assert result.primary_language == "english"
    assert result.primary_script == "latin"
    assert result.confidence > 0.5


def test_language_detection_devanagari():
    from astrosage.language.detector import detect_language
    result = detect_language(
        "यह एक हिंदी दस्तावेज़ है। इसमें कई शब्द हैं।",
        filename="hindi_test.txt",
    )
    assert result.primary_script == "devanagari"
    assert result.confidence > 0.5


def test_language_detection_filename():
    from astrosage.language.detector import detect_language
    result = detect_language(
        "Some text content",
        filename="Ayurveda_hindi_book.pdf",
        filepath="knowledge/raw/source_library/Ayurveda hindi/",
    )
    assert result.primary_language in ("hindi", "english")


def test_ocr_router_native_pdf():
    from astrosage.ocr_router.router import route_document, ExtractionRoute
    from astrosage.classifier.classifier import ClassificationResult
    
    cls = ClassificationResult(
        filepath="test.pdf", filename="test.pdf", extension=".pdf",
        mime_type="application/pdf", file_type="pdf",
        is_pdf=True, pdf_type="native", is_native_pdf=True,
        page_count=100, has_extractable_text=True,
    )
    decision = route_document(cls)
    assert decision.route == ExtractionRoute.DIRECT_TEXT
    assert not decision.needs_ocr


def test_ocr_router_scanned_pdf():
    from astrosage.ocr_router.router import route_document, ExtractionRoute
    from astrosage.classifier.classifier import ClassificationResult
    
    cls = ClassificationResult(
        filepath="test.pdf", filename="test.pdf", extension=".pdf",
        mime_type="application/pdf", file_type="pdf",
        is_pdf=True, pdf_type="scanned", is_scanned_pdf=True,
        page_count=50, has_extractable_text=False, ocr_required=True,
    )
    decision = route_document(cls)
    assert decision.route == ExtractionRoute.OCR_FULL
    assert decision.needs_ocr
    assert len(decision.ocr_pages) == 50


def test_ocr_router_docx():
    from astrosage.ocr_router.router import route_document, ExtractionRoute
    from astrosage.classifier.classifier import ClassificationResult
    
    cls = ClassificationResult(
        filepath="test.docx", filename="test.docx", extension=".docx",
        mime_type="application/docx", file_type="docx",
    )
    decision = route_document(cls)
    assert decision.route == ExtractionRoute.DOCX_EXTRACT
    assert not decision.needs_ocr


def test_provenance_graph():
    from astrosage.provenance.graph import ProvenanceGraph
    graph = ProvenanceGraph()
    
    src = graph.add_source("BOOK-001", "/path/to/file.pdf")
    ext = graph.add_extraction(
        "BOOK-001", src, "/path/to/file.pdf", "/path/to/extracted.txt",
        "pymupdf", "0.1.0",
    )
    
    assert graph.total_nodes == 2
    assert graph.total_edges == 1
    
    path = graph.trace_to_source(ext)
    assert len(path) == 2
    assert path[0].node_type == "source"
    assert path[1].node_type == "extraction"


def test_version_registry():
    from astrosage.versioning.versions import VersionRegistry
    vr = VersionRegistry()
    version = vr.get_version("classifier")
    assert version == "0.1.0"
    
    manifest = vr.save_version_manifest()
    assert manifest.exists()


def test_duplicate_detection_sha256():
    from astrosage.duplicate_detection.detector import detect_sha256_duplicates
    import hashlib
    
    with tempfile.NamedTemporaryFile(suffix=".txt", delete=False, mode="w") as f1:
        f1.write("identical content for testing")
        tmp1 = Path(f1.name)
    
    with tempfile.NamedTemporaryFile(suffix=".txt", delete=False, mode="w") as f2:
        f2.write("identical content for testing")
        tmp2 = Path(f2.name)
    
    with tempfile.NamedTemporaryFile(suffix=".txt", delete=False, mode="w") as f3:
        f3.write("different content here")
        tmp3 = Path(f3.name)
    
    try:
        groups = detect_sha256_duplicates([tmp1, tmp2, tmp3])
        assert len(groups) == 1  # One duplicate group
        assert len(groups[0].files) == 2  # Two files in the group
        assert groups[0].similarity == 1.0
    finally:
        tmp1.unlink()
        tmp2.unlink()
        tmp3.unlink()


def test_manifest_csv_exists():
    manifest = Path("knowledge/reports/manifest.csv")
    assert manifest.exists()
    import csv
    with open(manifest) as f:
        reader = csv.DictReader(f)
        rows = list(reader)
    assert len(rows) == 751
    # Check required fields exist
    required_fields = {"uuid", "sha256", "original_filename", "language", "extension"}
    assert required_fields.issubset(set(rows[0].keys()))
