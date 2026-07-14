"""Phase 14 — Gap Reconstruction Engine Tests."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))


class TestReconstruction:
    def test_imports(self):
        from core.reconstruction.engine import ReconstructionEngine, RecoveryType, RecoveryFragment
        assert ReconstructionEngine is not None

    def test_create_candidate(self):
        from core.reconstruction.engine import ReconstructionEngine, RecoveryType
        engine = ReconstructionEngine(min_evidence=2, min_confidence=0.6)
        f = engine.create_candidate("KU-001", RecoveryType.MISSING_PAGE,
                                    original_text="", recovered_text="recovered content",
                                    confidence=0.8, edition_ids=["ED-001"])
        assert f.knowledge_uuid == "KU-001"
        assert f.recovery_type == RecoveryType.MISSING_PAGE
        assert f.confidence == 0.8

    def test_verify_candidate(self):
        from core.reconstruction.engine import ReconstructionEngine, RecoveryType, RecoveryStatus
        engine = ReconstructionEngine(min_evidence=2, min_confidence=0.6)
        f = engine.create_candidate("KU-002", RecoveryType.BROKEN_OCR, confidence=0.9)
        result = engine.verify(f.fragment_id, verified=True, reason="Cross-edition match")
        assert result is True
        assert engine._fragments[f.fragment_id].status == RecoveryStatus.VERIFIED

    def test_reject_candidate(self):
        from core.reconstruction.engine import ReconstructionEngine, RecoveryType, RecoveryStatus
        engine = ReconstructionEngine(min_evidence=2, min_confidence=0.6)
        f = engine.create_candidate("KU-003", RecoveryType.ENCODING_CORRUPTION, confidence=0.7)
        result = engine.verify(f.fragment_id, verified=False, reason="No corroborating source")
        assert result is True
        assert engine._fragments[f.fragment_id].status == RecoveryStatus.REJECTED

    def test_get_fragments(self):
        from core.reconstruction.engine import ReconstructionEngine, RecoveryType
        engine = ReconstructionEngine()
        engine.create_candidate("KU-010", RecoveryType.MISSING_VERSE, confidence=0.8)
        engine.create_candidate("KU-010", RecoveryType.CUT_SENTENCE, confidence=0.6)
        fragments = engine.get_fragments("KU-010")
        assert len(fragments) == 2

    def test_get_verified(self):
        from core.reconstruction.engine import ReconstructionEngine, RecoveryType, RecoveryStatus
        engine = ReconstructionEngine()
        f1 = engine.create_candidate("KU-020", RecoveryType.TABLE, confidence=0.9)
        f2 = engine.create_candidate("KU-021", RecoveryType.FOOTNOTE, confidence=0.7)
        engine.verify(f1.fragment_id, verified=True)
        verified = engine.get_verified()
        assert len(verified) == 1

    def test_low_confidence_candidate(self):
        from core.reconstruction.engine import ReconstructionEngine, RecoveryType, RecoveryStatus
        engine = ReconstructionEngine(min_confidence=0.6)
        f = engine.create_candidate("KU-030", RecoveryType.PARTIAL_EXTRACTION, confidence=0.3)
        assert f.status == RecoveryStatus.UNKNOWN

    def test_summary(self):
        from core.reconstruction.engine import ReconstructionEngine, RecoveryType
        engine = ReconstructionEngine()
        engine.create_candidate("KU-040", RecoveryType.MISSING_PARAGRAPH, confidence=0.8)
        engine.create_candidate("KU-041", RecoveryType.CUT_SENTENCE, confidence=0.7)
        s = engine.summary()
        assert s["total"] == 2
        assert "by_type" in s
        assert "by_status" in s

    def test_count(self):
        from core.reconstruction.engine import ReconstructionEngine, RecoveryType
        engine = ReconstructionEngine()
        assert engine.count() == 0
        engine.create_candidate("KU-050", RecoveryType.APPENDIX, confidence=0.8)
        assert engine.count() == 1

    def test_recovery_type_values(self):
        from core.reconstruction.engine import RecoveryType
        types = [t.value for t in RecoveryType]
        assert "missing_page" in types
        assert "broken_ocr" in types
        assert "footnote" in types
        assert "metadata" in types
        assert len(types) >= 14

    def test_all_recovery_types(self):
        from core.reconstruction.engine import ReconstructionEngine, RecoveryType
        engine = ReconstructionEngine()
        for rt in RecoveryType:
            f = engine.create_candidate("KU-060", rt, confidence=0.8)
            assert f.fragment_id is not None
        assert engine.count() == len(RecoveryType)
