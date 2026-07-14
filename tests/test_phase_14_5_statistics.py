"""Phase 14.5 — Recovery Statistics Engine Tests."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))


class TestRecoveryStatistics:
    def test_imports(self):
        from core.recovery_statistics.engine import RecoveryStatisticsEngine, RecoveryStats
        assert RecoveryStatisticsEngine is not None

    def test_record_stats(self):
        from core.recovery_statistics.engine import RecoveryStatisticsEngine
        engine = RecoveryStatisticsEngine()
        stats = engine.record("BK-001", book_title="Test", language="english",
                              total_paragraphs=100, evidence_collected=20,
                              editions_discovered=3, paragraphs_verified=80)
        assert stats.book_uuid == "BK-001"
        assert stats.completeness_pct == 80.0

    def test_get_by_book(self):
        from core.recovery_statistics.engine import RecoveryStatisticsEngine
        engine = RecoveryStatisticsEngine()
        engine.record("BK-010", book_title="Book", total_paragraphs=50)
        stats = engine.get_by_book("BK-010")
        assert stats is not None

    def test_corpus_summary(self):
        from core.recovery_statistics.engine import RecoveryStatisticsEngine
        engine = RecoveryStatisticsEngine()
        engine.record("BK-020", book_title="A", total_paragraphs=100,
                      paragraphs_verified=80, evidence_collected=10)
        engine.record("BK-021", book_title="B", total_paragraphs=200,
                      paragraphs_verified=150, evidence_collected=30)
        s = engine.corpus_summary()
        assert s["total_books"] == 2
        assert s["total_paragraphs"] == 300
        assert s["evidence_collected"] == 40

    def test_empty_summary(self):
        from core.recovery_statistics.engine import RecoveryStatisticsEngine
        engine = RecoveryStatisticsEngine()
        s = engine.corpus_summary()
        assert s["total_books"] == 0

    def test_count(self):
        from core.recovery_statistics.engine import RecoveryStatisticsEngine
        engine = RecoveryStatisticsEngine()
        assert engine.count() == 0
        engine.record("BK-030")
        assert engine.count() == 1
