"""Phase 14.5 — Knowledge Passport Engine Tests."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))


class TestKnowledgePassports:
    def test_imports(self):
        from core.knowledge_passports.engine import KnowledgePassportEngine, KnowledgePassport
        assert KnowledgePassportEngine is not None

    def test_create_passport(self):
        from core.knowledge_passports.engine import KnowledgePassportEngine
        engine = KnowledgePassportEngine()
        p = engine.create("KU-001", book_uuid="BK-001", language="sanskrit")
        assert p.passport_id is not None
        assert p.knowledge_uuid == "KU-001"

    def test_add_evidence(self):
        from core.knowledge_passports.engine import KnowledgePassportEngine
        engine = KnowledgePassportEngine()
        engine.create("KU-002", book_uuid="BK-002")
        result = engine.add_evidence("KU-002", "EV-001")
        assert result is True

    def test_add_conflict(self):
        from core.knowledge_passports.engine import KnowledgePassportEngine, PassportStatus
        engine = KnowledgePassportEngine()
        engine.create("KU-003")
        engine.add_conflict("KU-003", {"type": "translation", "source": "ed_A"})
        p = engine.get_by_knowledge("KU-003")
        assert p.verification_status == PassportStatus.CONFLICTED

    def test_verify(self):
        from core.knowledge_passports.engine import KnowledgePassportEngine, PassportStatus
        engine = KnowledgePassportEngine()
        engine.create("KU-004")
        engine.verify("KU-004", PassportStatus.VERIFIED, confidence=0.9)
        p = engine.get_by_knowledge("KU-004")
        assert p.verification_status == PassportStatus.VERIFIED
        assert p.confidence == 0.9

    def test_flag_for_review(self):
        from core.knowledge_passports.engine import KnowledgePassportEngine
        engine = KnowledgePassportEngine()
        engine.create("KU-005")
        engine.flag_for_review("KU-005", notes="Needs expert review")
        p = engine.get_by_knowledge("KU-005")
        assert p.human_review_flag is True

    def test_get_by_book(self):
        from core.knowledge_passports.engine import KnowledgePassportEngine
        engine = KnowledgePassportEngine()
        engine.create("KU-010", book_uuid="BK-010")
        engine.create("KU-011", book_uuid="BK-010")
        engine.create("KU-012", book_uuid="BK-011")
        passports = engine.get_by_book("BK-010")
        assert len(passports) == 2

    def test_summary(self):
        from core.knowledge_passports.engine import KnowledgePassportEngine, PassportStatus
        engine = KnowledgePassportEngine()
        engine.create("KU-020")
        engine.verify("KU-020", PassportStatus.VERIFIED)
        s = engine.summary()
        assert s["total"] == 1
        assert s["by_verification_status"]["verified"] == 1

    def test_count(self):
        from core.knowledge_passports.engine import KnowledgePassportEngine
        engine = KnowledgePassportEngine()
        assert engine.count() == 0
        engine.create("KU-030")
        assert engine.count() == 1
