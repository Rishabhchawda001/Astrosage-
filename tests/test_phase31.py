"""
Phase 3.1 — Document Forensics & Classifier Validation Tests.
"""
import json
import sys
from pathlib import Path
from collections import Counter

import pytest

BASE = Path(__file__).parent.parent
FORENSICS_DIR = BASE / "knowledge" / "benchmarks" / "forensics"
RAW_DIR = BASE / "knowledge" / "raw" / "source_library"

sys.path.insert(0, str(BASE / "src"))


def _get_small_pdf():
    """Find a small PDF for testing (< 100KB)."""
    pdfs = sorted(RAW_DIR.rglob("*.pdf"))
    for fp in pdfs:
        if fp.stat().st_size < 100_000:
            return fp
    if pdfs:
        return pdfs[0]
    return None


class TestPageClassifier:
    def test_classifier_imports(self):
        from astrosage.forensics.page_classifier import classify_page, PageSignals, classify_document_pages
        assert classify_page is not None
        assert classify_document_pages is not None

    def test_page_signals_dataclass(self):
        from astrosage.forensics.page_classifier import PageSignals
        ps = PageSignals(page_number=1)
        assert ps.page_number == 1
        assert ps.page_class == "unknown"
        assert ps.confidence == 0.0

    def test_classify_document_returns_list(self):
        from astrosage.forensics.page_classifier import classify_document_pages
        pdf = _get_small_pdf()
        if pdf is None:
            pytest.skip("No PDFs found")
        results = classify_document_pages(pdf)
        assert isinstance(results, list)
        assert len(results) > 0

    def test_classification_valid_classes(self):
        from astrosage.forensics.page_classifier import classify_document_pages
        valid_classes = {"native_text", "scanned_image", "ocr_overlay", "mixed_content", "blank", "unknown"}
        pdf = _get_small_pdf()
        if pdf is None:
            pytest.skip("No PDFs found")
        results = classify_document_pages(pdf)
        for r in results:
            assert r.page_class in valid_classes

    def test_confidence_is_bounded(self):
        from astrosage.forensics.page_classifier import classify_document_pages
        pdf = _get_small_pdf()
        if pdf is None:
            pytest.skip("No PDFs found")
        results = classify_document_pages(pdf)
        for r in results:
            assert 0.0 <= r.confidence <= 1.0

    def test_evidence_list_populated(self):
        from astrosage.forensics.page_classifier import classify_document_pages
        pdf = _get_small_pdf()
        if pdf is None:
            pytest.skip("No PDFs found")
        results = classify_document_pages(pdf)
        classified = [r for r in results if r.page_class != "unknown"]
        for r in classified:
            assert len(r.classification_evidence) > 0


class TestPDFAnalyzer:
    def test_analyzer_imports(self):
        from astrosage.forensics.pdf_analyzer import analyze_pdf_forensics, PageForensics
        assert analyze_pdf_forensics is not None

    def test_pdf_forensics_returns_dict(self):
        from astrosage.forensics.pdf_analyzer import analyze_pdf_forensics
        pdf = _get_small_pdf()
        if pdf is None:
            pytest.skip("No PDFs found")
        result = analyze_pdf_forensics(pdf)
        assert isinstance(result, dict)
        assert "total_pages" in result
        assert "document_class" in result

    def test_forensic_classes_valid(self):
        from astrosage.forensics.pdf_analyzer import analyze_pdf_forensics
        valid = {"born_digital", "scanned", "ocr_overlay", "hybrid", "converted", "unknown"}
        pdf = _get_small_pdf()
        if pdf is None:
            pytest.skip("No PDFs found")
        result = analyze_pdf_forensics(pdf)
        assert result["document_class"] in valid


class TestVisualValidator:
    def test_validator_imports(self):
        from astrosage.forensics.visual_validator import generate_visual_samples, generate_validation_report
        assert generate_visual_samples is not None


class TestForensicPipelineOutputs:
    def test_forensic_results_exist(self):
        assert (FORENSICS_DIR / "forensic_results.json").exists()

    def test_forensic_results_valid(self):
        results_file = FORENSICS_DIR / "forensic_results.json"
        data = json.loads(results_file.read_text())
        assert isinstance(data, list)
        assert len(data) > 100  # Should have processed most PDFs

    def test_evidence_summary_exists(self):
        assert (FORENSICS_DIR / "evidence_summary.json").exists()

    def test_evidence_summary_valid(self):
        evidence = json.loads((FORENSICS_DIR / "evidence_summary.json").read_text())
        for key in ["total_pdfs", "total_pages_sampled", "page_class_distribution",
                     "document_class_distribution", "conclusion", "verdict"]:
            assert key in evidence, f"Missing key: {key}"

    def test_verdict_valid(self):
        evidence = json.loads((FORENSICS_DIR / "evidence_summary.json").read_text())
        assert evidence["verdict"] in {"corroborated", "partially_corroborated", "disproved"}

    def test_document_classes_diverse(self):
        data = json.loads((FORENSICS_DIR / "forensic_results.json").read_text())
        doc_classes = Counter(r.get("document_class", "error") for r in data)
        assert len(doc_classes) >= 2

    def test_scanned_content_detected(self):
        """Phase 3.1 key finding: scanned content must exist."""
        evidence = json.loads((FORENSICS_DIR / "evidence_summary.json").read_text())
        scanned_pct = evidence.get("scanned_pct", 0) + evidence.get("ocr_overlay_pct", 0)
        assert scanned_pct > 0, "No scanned content detected"

    def test_percentage_sum_approximately_100(self):
        evidence = json.loads((FORENSICS_DIR / "evidence_summary.json").read_text())
        dist = evidence.get("page_class_distribution", {})
        total_pct = sum(v.get("pct", 0) for v in dist.values())
        assert 99.0 <= total_pct <= 101.0, f"Percentages: {total_pct}"

    def test_report_exists(self):
        assert (BASE / "knowledge" / "reports" / "FORENSIC_INVESTIGATION_REPORT.md").exists()

    def test_adr_007_exists(self):
        assert (BASE / "adrs" / "ADR-007-forensic-validation.md").exists()

    def test_unicode_quality_exists(self):
        assert (FORENSICS_DIR / "unicode_quality.json").exists()

    def test_visual_samples_exist(self):
        assert (FORENSICS_DIR / "visual_samples" / "visual_validation.json").exists()


class TestPhase3Contradiction:
    def test_phase3_claim_disproved(self):
        """Phase 3 claimed zero scanned PDFs — Phase 3.1 should disprove."""
        evidence = json.loads((FORENSICS_DIR / "evidence_summary.json").read_text())
        assert evidence["verdict"] != "corroborated"

    def test_scanned_percentage_above_zero(self):
        evidence = json.loads((FORENSICS_DIR / "evidence_summary.json").read_text())
        assert evidence.get("scanned_pct", 0) > 0

    def test_native_percentage_above_zero(self):
        evidence = json.loads((FORENSICS_DIR / "evidence_summary.json").read_text())
        assert evidence.get("native_text_pct", 0) > 0
