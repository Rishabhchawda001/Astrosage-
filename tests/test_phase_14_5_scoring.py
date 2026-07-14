"""Phase 14.5 — Recovery Scoring Engine Tests."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))


class TestRecoveryScoring:
    def test_imports(self):
        from core.recovery_scoring.engine import RecoveryScoringEngine, RecoveryScore
        assert RecoveryScoringEngine is not None

    def test_compute_score(self):
        from core.recovery_scoring.engine import RecoveryScoringEngine
        engine = RecoveryScoringEngine()
        score = engine.compute("BK-001", book_title="Test Book",
                               total_paragraphs=100, verified_paragraphs=80,
                               recovered_paragraphs=10, editions_found=3,
                               translations_found=2, evidence_count=15,
                               confidence_values=[0.9, 0.85])
        assert score.book_uuid == "BK-001"
        assert score.knowledge_completeness == 80.0
        assert score.recovery_pct == 90.0

    def test_get_by_book(self):
        from core.recovery_scoring.engine import RecoveryScoringEngine
        engine = RecoveryScoringEngine()
        engine.compute("BK-010", book_title="Book A", total_paragraphs=50)
        score = engine.get_by_book("BK-010")
        assert score is not None

    def test_corpus_summary(self):
        from core.recovery_scoring.engine import RecoveryScoringEngine
        engine = RecoveryScoringEngine()
        engine.compute("BK-020", total_paragraphs=100, verified_paragraphs=80)
        engine.compute("BK-021", total_paragraphs=200, verified_paragraphs=150)
        s = engine.corpus_summary()
        assert s["total_books_scored"] == 2
        assert s["total_paragraphs"] == 300
        assert s["total_verified"] == 230

    def test_empty_summary(self):
        from core.recovery_scoring.engine import RecoveryScoringEngine
        engine = RecoveryScoringEngine()
        s = engine.corpus_summary()
        assert s["total_books_scored"] == 0

    def test_count(self):
        from core.recovery_scoring.engine import RecoveryScoringEngine
        engine = RecoveryScoringEngine()
        assert engine.count() == 0
        engine.compute("BK-030", total_paragraphs=10)
        assert engine.count() == 1
