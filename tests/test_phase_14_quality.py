"""Phase 14 — Quality Metrics Engine Tests."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))


class TestQuality:
    def test_imports(self):
        from core.quality.engine import QualityEngine, QualityScore
        assert QualityEngine is not None

    def test_compute_score(self):
        from core.quality.engine import QualityEngine
        engine = QualityEngine()
        score = engine.compute(scope="book", scope_id="BK-001",
                               total_paragraphs=100, verified_paragraphs=80,
                               canonical_paragraphs=75, confidence_values=[0.9, 0.8, 0.85],
                               evidence_coverage=90.0)
        assert score.overall_score > 0
        assert score.truth_pct == 80.0

    def test_overall_score_range(self):
        from core.quality.engine import QualityEngine
        engine = QualityEngine()
        score = engine.compute(scope="corpus", scope_id="full",
                               total_paragraphs=1000, verified_paragraphs=900,
                               canonical_paragraphs=850,
                               confidence_values=[0.95, 0.9, 0.85, 0.8],
                               ocr_completeness=95.0, reconstruction_pct=80.0,
                               citation_pct=70.0, evidence_coverage=85.0,
                               edition_coverage=60.0, language_coverage=50.0)
        assert 0 <= score.overall_score <= 1.0

    def test_confidence_stats(self):
        from core.quality.engine import QualityEngine
        engine = QualityEngine()
        score = engine.compute(scope="chapter", scope_id="CH-001",
                               confidence_values=[0.5, 0.7, 0.9])
        import pytest
        assert score.confidence_mean == pytest.approx(0.7)
        assert score.confidence_min == 0.5
        assert score.confidence_max == 0.9

    def test_empty_confidence(self):
        from core.quality.engine import QualityEngine
        engine = QualityEngine()
        score = engine.compute(scope="page", scope_id="PG-001")
        assert score.confidence_mean == 0.0
        assert score.confidence_min == 0.0

    def test_get_by_scope(self):
        from core.quality.engine import QualityEngine
        engine = QualityEngine()
        engine.compute(scope="book", scope_id="BK-001", total_paragraphs=50)
        engine.compute(scope="book", scope_id="BK-002", total_paragraphs=60)
        engine.compute(scope="chapter", scope_id="CH-001", total_paragraphs=10)
        books = engine.get_by_scope("book")
        assert len(books) == 2

    def test_corpus_summary(self):
        from core.quality.engine import QualityEngine
        engine = QualityEngine()
        engine.compute(scope="book", scope_id="BK-001",
                       total_paragraphs=100, verified_paragraphs=80)
        engine.compute(scope="book", scope_id="BK-002",
                       total_paragraphs=200, verified_paragraphs=150)
        s = engine.corpus_summary()
        assert s["total_scores"] == 2
        assert s["total_paragraphs"] == 300
        assert s["verified_paragraphs"] == 230

    def test_empty_summary(self):
        from core.quality.engine import QualityEngine
        engine = QualityEngine()
        s = engine.corpus_summary()
        assert s["total_scores"] == 0
        assert s["mean_overall"] == 0.0

    def test_count(self):
        from core.quality.engine import QualityEngine
        engine = QualityEngine()
        assert engine.count() == 0
        engine.compute(scope="page", scope_id="PG-001")
        assert engine.count() == 1

    def test_custom_weights(self):
        from core.quality.engine import QualityEngine
        engine = QualityEngine(weights={"ocr_completeness": 0.5, "reconstruction_pct": 0.5})
        score = engine.compute(scope="test", scope_id="T-001",
                               ocr_completeness=100.0, reconstruction_pct=100.0)
        assert score.overall_score > 0.9
