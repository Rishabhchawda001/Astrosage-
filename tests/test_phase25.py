"""Phase 2.5 tests — Corpus Intelligence & Quality Analysis."""
import csv
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))


def test_corpus_intelligence_exists():
    f = Path("knowledge/reports/corpus_intelligence.json")
    assert f.exists()
    data = json.load(open(f))
    assert data["total_files"] == 751
    assert data["total_size_bytes"] > 0
    assert data["pdf_count"] > 0


def test_corpus_intelligence_markdown():
    f = Path("knowledge/reports/CORPUS_INTELLIGENCE.md")
    assert f.exists()
    content = f.read_text()
    assert "Total files" in content
    assert "751" in content


def test_quality_scores_exist():
    f = Path("knowledge/reports/quality_scores.csv")
    assert f.exists()
    with open(f) as fh:
        reader = csv.DictReader(fh)
        rows = list(reader)
    assert len(rows) == 751
    # Check required fields
    required = {"filename", "overall_score", "metadata_completeness", "ocr_readiness"}
    assert required.issubset(set(rows[0].keys()))


def test_quality_summary():
    f = Path("knowledge/reports/quality_summary.json")
    assert f.exists()
    data = json.load(open(f))
    assert data["total_documents"] == 751
    assert 0 <= data["average_score"] <= 100
    assert "score_distribution" in data


def test_metadata_validation():
    f = Path("knowledge/reports/metadata_validation.json")
    assert f.exists()
    data = json.load(open(f))
    assert data["total_documents"] == 751
    assert "completeness" in data


def test_metadata_issues_csv():
    f = Path("knowledge/reports/metadata_issues.csv")
    assert f.exists()
    with open(f) as fh:
        rows = list(csv.DictReader(fh))
    assert len(rows) > 0  # Should have some issues
    required = {"filename", "field", "severity", "message"}
    assert required.issubset(set(rows[0].keys()))


def test_semantic_analysis():
    f = Path("knowledge/reports/semantic_analysis.json")
    assert f.exists()
    data = json.load(open(f))
    assert data["total_entities_found"] > 0
    assert data["unique_terms"] > 0
    assert len(data["scriptures"]) > 0
    assert len(data["people"]) > 0
    assert len(data["concepts"]) > 0


def test_graph_entities():
    f = Path("knowledge/reports/graph_entities.json")
    assert f.exists()
    entities = json.load(open(f))
    assert len(entities) > 0
    # Each entity has required fields
    for e in entities[:10]:
        assert "name" in e
        assert "type" in e
        assert "frequency" in e


def test_golden_eval_dataset():
    f = Path("knowledge/reports/golden_eval_dataset.json")
    assert f.exists()
    questions = json.load(open(f))
    assert len(questions) >= 500  # At least 500 questions
    # Each question has required fields
    for q in questions[:5]:
        assert "question_id" in q
        assert "question" in q
        assert "expected_answer" in q
        assert "topic" in q
        assert "difficulty" in q


def test_golden_eval_csv():
    f = Path("knowledge/reports/golden_eval_dataset.csv")
    assert f.exists()
    with open(f) as fh:
        rows = list(csv.DictReader(fh))
    assert len(rows) >= 500


def test_eval_summary():
    f = Path("knowledge/reports/eval_summary.json")
    assert f.exists()
    data = json.load(open(f))
    assert data["total_questions"] >= 500


def test_search_baseline():
    f = Path("knowledge/benchmarks/search_baseline.json")
    assert f.exists()
    data = json.load(open(f))
    assert "filename" in data
    assert "metadata" in data
    assert "bm25" in data
    # Each method has metrics
    for method in ["filename", "metadata", "bm25"]:
        assert "avg_latency_ms" in data[method]
        assert "recall_rate" in data[method]


def test_search_baseline_detail():
    f = Path("knowledge/benchmarks/search_baseline_detail.json")
    assert f.exists()
    data = json.load(open(f))
    assert len(data) > 0
    assert "method" in data[0]
    assert "query" in data[0]


def test_corpus_health_dashboard():
    f = Path("knowledge/reports/corpus_health_dashboard.json")
    assert f.exists()
    data = json.load(open(f))
    assert "library" in data
    assert "processing" in data
    assert "quality" in data
    assert "languages" in data
    assert data["library"]["total_files"] == 751
