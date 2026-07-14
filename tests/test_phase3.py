"""Phase 3 tests — Document Intelligence Lab."""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))


def test_benchmark_samples_exist():
    f = Path("knowledge/benchmarks/sample_corpus/benchmark_samples.json")
    assert f.exists()
    samples = json.load(open(f))
    assert len(samples) >= 10


def test_sample_catalog():
    f = Path("knowledge/benchmarks/sample_corpus/SAMPLE_CATALOG.md")
    assert f.exists()
    content = f.read_text()
    assert "Benchmark Sample Dataset" in content


def test_ocr_benchmark_results():
    f = Path("knowledge/benchmarks/ocr_results/ocr_benchmark_results.json")
    assert f.exists()
    results = json.load(open(f))
    assert len(results) > 0
    # Check required fields
    for r in results[:3]:
        assert "engine" in r
        assert "filename" in r
        assert "success" in r
        assert "processing_time_seconds" in r


def test_ocr_benchmark_summary():
    f = Path("knowledge/benchmarks/ocr_results/ocr_benchmark_summary.json")
    assert f.exists()
    summary = json.load(open(f))
    assert "pymupdf" in summary
    assert summary["pymupdf"]["success_rate"] == 100.0
    assert summary["pymupdf"]["avg_confidence"] > 0.9


def test_parser_benchmark_results():
    f = Path("knowledge/benchmarks/parser_results/parser_benchmark_results.json")
    assert f.exists()
    results = json.load(open(f))
    assert len(results) > 0


def test_parser_benchmark_summary():
    f = Path("knowledge/benchmarks/parser_results/parser_benchmark_summary.json")
    assert f.exists()
    summary = json.load(open(f))
    assert "pymupdf" in summary
    assert summary["pymupdf"]["success_rate"] == 100.0


def test_pipeline_recommendation():
    f = Path("knowledge/benchmarks/pipeline_recommendation.json")
    assert f.exists()
    data = json.load(open(f))
    assert "recommended_pipeline" in data
    assert "ocr_engine_rankings" in data
    assert "parser_rankings" in data
    assert "rationale" in data
    assert "hardware_requirements" in data
    assert len(data["ocr_engine_rankings"]) >= 1


def test_adr_006():
    f = Path("adrs/ADR-006-document-pipeline.md")
    assert f.exists()
    content = f.read_text()
    assert "PyMuPDF" in content
    assert "Status" in content


def test_ocr_benchmark_report():
    f = Path("knowledge/reports/OCR_BENCHMARK_REPORT.md")
    assert f.exists()
    content = f.read_text()
    assert "OCR Benchmark Report" in content
    assert "PyMuPDF" in content


def test_parser_benchmark_report():
    f = Path("knowledge/reports/PARSER_BENCHMARK_REPORT.md")
    assert f.exists()
    content = f.read_text()
    assert "Parser Benchmark Report" in content


def test_production_pipeline_report():
    f = Path("knowledge/reports/PRODUCTION_PIPELINE_RECOMMENDATION.md")
    assert f.exists()
    content = f.read_text()
    assert "Production Pipeline" in content
    assert "Hardware" in content
