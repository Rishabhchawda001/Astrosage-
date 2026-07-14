"""Phase 3.5 — Production Pipeline Validation Tests."""
import json
import sys
from pathlib import Path

import pytest

BASE = Path(__file__).parent.parent
sys.path.insert(0, str(BASE / "src"))


class TestSampler:
    def test_sampler_imports(self):
        from astrosage.production.sampler import build_validation_corpus
        assert build_validation_corpus is not None

    def test_sampler_returns_samples_and_summary(self):
        from astrosage.production.sampler import build_validation_corpus
        samples, summary = build_validation_corpus(
            forensics_results_path=BASE / "knowledge" / "benchmarks" / "forensics" / "forensic_results.json",
            raw_dir=BASE / "knowledge" / "raw" / "source_library",
            manifest_path=BASE / "knowledge" / "reports" / "manifest.csv",
            max_samples=10,
        )
        assert len(samples) > 0
        assert "total_selected" in summary
        assert "by_class" in summary

    def test_sampler_covers_all_classes(self):
        from astrosage.production.sampler import build_validation_corpus
        samples, summary = build_validation_corpus(
            forensics_results_path=BASE / "knowledge" / "benchmarks" / "forensics" / "forensic_results.json",
            raw_dir=BASE / "knowledge" / "raw" / "source_library",
            manifest_path=BASE / "knowledge" / "reports" / "manifest.csv",
            max_samples=20,
        )
        classes = set(s["document_class"] for s in samples)
        assert "native_text" in classes
        assert "scanned_image" in classes


class TestPipelineOutputs:
    def test_bronze_files_exist(self):
        bronze = list((BASE / "knowledge" / "bronze" / "extracted_text").glob("*.txt"))
        assert len(bronze) >= 30

    def test_silver_files_exist(self):
        silver = list((BASE / "knowledge" / "silver" / "structured_documents").glob("*.md"))
        assert len(silver) >= 30

    def test_bronze_silver_counts_match(self):
        bronze = list((BASE / "knowledge" / "bronze" / "extracted_text").glob("*.txt"))
        silver = list((BASE / "knowledge" / "silver" / "structured_documents").glob("*.md"))
        assert len(bronze) == len(silver)

    def test_bronze_files_not_empty(self):
        bronze = list((BASE / "knowledge" / "bronze" / "extracted_text").glob("*.txt"))
        empty = [f for f in bronze if f.stat().st_size < 10]
        # Allow up to 2% empty bronze files (legitimate edge cases: fully scanned PDFs
        # where OCR did not produce extractable text)
        threshold = max(1, len(bronze) * 0.02)
        assert len(empty) <= threshold, f"Too many empty bronze files ({len(empty)}/{len(bronze)}): {empty[:5]}"

    def test_bronze_has_page_markers(self):
        bronze = list((BASE / "knowledge" / "bronze" / "extracted_text").glob("*.txt"))
        for f in bronze[:5]:
            content = f.read_text(encoding="utf-8", errors="replace")
            assert "=== PAGE" in content, f"{f.name} missing page markers"

    def test_silver_has_headers(self):
        silver = list((BASE / "knowledge" / "silver" / "structured_documents").glob("*.md"))
        for f in silver[:5]:
            content = f.read_text(encoding="utf-8", errors="replace")
            assert content.startswith("# "), f"{f.name} missing header"


class TestValidationReport:
    def test_report_exists(self):
        report = BASE / "knowledge" / "reports" / "production" / "PRODUCTION_VALIDATION_REPORT.md"
        assert report.exists()

    def test_report_has_go_nogo(self):
        report = (BASE / "knowledge" / "reports" / "production" / "PRODUCTION_VALIDATION_REPORT.md").read_text()
        assert "GO" in report

    def test_report_json_exists(self):
        report = BASE / "knowledge" / "benchmarks" / "production" / "pipeline_report.json"
        assert report.exists()

    def test_report_json_valid(self):
        report = json.loads((BASE / "knowledge" / "benchmarks" / "production" / "pipeline_report.json").read_text())
        assert report["go_nogo"]["recommendation"] == "GO"
        assert report["documents"]["processed"] >= 30
        assert report["documents"]["failure_rate_pct"] <= 10


class TestADRs:
    def test_adr_008_exists(self):
        adr = BASE / "adrs" / "ADR-008-production-pipeline-lock.md"
        assert adr.exists()

    def test_adr_008_locked_components(self):
        adr = (BASE / "adrs" / "ADR-008-production-pipeline-lock.md").read_text()
        assert "LOCKED" in adr
        assert "v1.0" in adr


class TestUnicodeIntegrity:
    def test_no_broken_unicode_in_bronze(self):
        bronze = list((BASE / "knowledge" / "bronze" / "extracted_text").glob("*.txt"))
        broken = 0
        for f in bronze[:20]:
            content = f.read_text(encoding="utf-8", errors="replace")
            if "\ufffd" in content:
                broken += 1
        assert broken == 0, f"{broken} bronze files have broken Unicode"

    def test_devanagari_preserved(self):
        bronze = list((BASE / "knowledge" / "bronze" / "extracted_text").glob("*.txt"))
        devanagari_found = False
        for f in bronze:
            content = f.read_text(encoding="utf-8", errors="replace")
            dev_count = sum(1 for ch in content if 0x0900 <= ord(ch) <= 0x097F)
            if dev_count > 100:
                devanagari_found = True
                break
        assert devanagari_found, "No Devanagari text found in bronze outputs"
