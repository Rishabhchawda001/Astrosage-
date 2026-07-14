"""Phase 14.5 — Knowledge Recovery Engine Tests."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))


class TestKnowledgeRecovery:
    def test_imports(self):
        from core.knowledge_recovery.engine import KnowledgeRecoveryEngine, RecoveryTarget, RecoveryProgress
        assert KnowledgeRecoveryEngine is not None

    def test_create_target(self):
        from core.knowledge_recovery.engine import KnowledgeRecoveryEngine, KnowledgeDomain
        engine = KnowledgeRecoveryEngine()
        target = engine.create_target("BK-001", "Bhagavad Gita", language="sanskrit",
                                      domain=KnowledgeDomain.VEDIC)
        assert target.book_uuid == "BK-001"
        assert target.book_title == "Bhagavad Gita"

    def test_update_progress(self):
        from core.knowledge_recovery.engine import KnowledgeRecoveryEngine, RecoveryStatus
        engine = KnowledgeRecoveryEngine()
        target = engine.create_target("BK-002", "Test Book", paragraph_count=100)
        engine.update_progress(target.target_id, recovered_paragraphs=80,
                               verified_paragraphs=60, evidence_count=5)
        updated = engine.get_target(target.target_id)
        assert updated.recovered_paragraphs == 80

    def test_compute_completeness(self):
        from core.knowledge_recovery.engine import KnowledgeRecoveryEngine
        engine = KnowledgeRecoveryEngine()
        target = engine.create_target("BK-003", "Book", paragraph_count=100)
        engine.update_progress(target.target_id, verified_paragraphs=80,
                               recovered_paragraphs=10, found_editions=3,
                               evidence_count=15)
        pct = engine.compute_completeness(target.target_id)
        assert pct > 0

    def test_register_source(self):
        from core.knowledge_recovery.engine import KnowledgeRecoveryEngine
        engine = KnowledgeRecoveryEngine()
        engine.register_source("archive.org")
        engine.register_source("open_library")
        assert len(engine._sources) == 2

    def test_get_incomplete(self):
        from core.knowledge_recovery.engine import KnowledgeRecoveryEngine, RecoveryStatus
        engine = KnowledgeRecoveryEngine()
        t1 = engine.create_target("BK-010", "Book A")
        t2 = engine.create_target("BK-011", "Book B")
        engine.update_progress(t1.target_id, status=RecoveryStatus.COMPLETE)
        incomplete = engine.get_incomplete()
        assert len(incomplete) == 1

    def test_summary(self):
        from core.knowledge_recovery.engine import KnowledgeRecoveryEngine
        engine = KnowledgeRecoveryEngine()
        engine.create_target("BK-020", "Book", paragraph_count=50)
        s = engine.summary()
        assert s["total_books"] == 1
        assert "overall_completeness" in s

    def test_get_target_by_book(self):
        from core.knowledge_recovery.engine import KnowledgeRecoveryEngine
        engine = KnowledgeRecoveryEngine()
        engine.create_target("BK-030", "Book X")
        target = engine.get_target_by_book("BK-030")
        assert target is not None
        assert target.book_title == "Book X"
