"""Phase 14 — Truth Decision Engine Tests."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))


class TestTruthDecision:
    def test_imports(self):
        from core.truth.engine import TruthEngine, TruthDecision, TruthVerdict
        assert TruthEngine is not None

    def test_accept_high_confidence(self):
        from core.truth.engine import TruthEngine, TruthDecision
        engine = TruthEngine(auto_accept_threshold=0.85, auto_review_threshold=0.5)
        verdict = engine.decide("KU-001", confidence=0.9, evidence_count=3, source_count=2)
        assert verdict.decision == TruthDecision.ACCEPTED

    def test_reject_low_confidence(self):
        from core.truth.engine import TruthEngine, TruthDecision
        engine = TruthEngine(auto_accept_threshold=0.85, auto_review_threshold=0.5)
        verdict = engine.decide("KU-002", confidence=0.2, evidence_count=1, source_count=1)
        assert verdict.decision == TruthDecision.UNKNOWN

    def test_needs_review_moderate(self):
        from core.truth.engine import TruthEngine, TruthDecision
        engine = TruthEngine(auto_accept_threshold=0.85, auto_review_threshold=0.5)
        verdict = engine.decide("KU-003", confidence=0.6, evidence_count=1)
        assert verdict.decision == TruthDecision.NEEDS_REVIEW

    def test_conflict_triggers_review(self):
        from core.truth.engine import TruthEngine, TruthDecision
        engine = TruthEngine(auto_accept_threshold=0.85, auto_review_threshold=0.5)
        verdict = engine.decide("KU-004", confidence=0.95, evidence_count=5, conflict_count=2)
        assert verdict.decision == TruthDecision.NEEDS_REVIEW

    def test_get_verdict(self):
        from core.truth.engine import TruthEngine
        engine = TruthEngine()
        engine.decide("KU-010", confidence=0.8, evidence_count=2)
        v = engine.get_verdict("KU-010")
        assert v is not None
        assert v.knowledge_uuid == "KU-010"

    def test_get_by_decision(self):
        from core.truth.engine import TruthEngine, TruthDecision
        engine = TruthEngine(auto_accept_threshold=0.85)
        engine.decide("KU-020", confidence=0.9, evidence_count=3)
        engine.decide("KU-021", confidence=0.2, evidence_count=1)
        accepted = engine.get_by_decision(TruthDecision.ACCEPTED)
        assert len(accepted) == 1

    def test_summary(self):
        from core.truth.engine import TruthEngine
        engine = TruthEngine()
        engine.decide("KU-030", confidence=0.9, evidence_count=3)
        engine.decide("KU-031", confidence=0.3, evidence_count=1)
        s = engine.summary()
        assert s["total"] == 2
        assert "by_decision" in s

    def test_count(self):
        from core.truth.engine import TruthEngine
        engine = TruthEngine()
        assert engine.count() == 0
        engine.decide("KU-040", confidence=0.8, evidence_count=2)
        assert engine.count() == 1

    def test_verdict_has_explanation(self):
        from core.truth.engine import TruthEngine
        engine = TruthEngine()
        v = engine.decide("KU-050", confidence=0.9, evidence_count=3, explanation="Custom reason")
        assert v.explanation == "Custom reason"
