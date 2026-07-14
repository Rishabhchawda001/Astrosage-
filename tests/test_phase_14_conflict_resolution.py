"""Phase 14 — Conflict Resolution Engine Tests."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))


class TestConflictResolution:
    def test_imports(self):
        from core.conflict_resolution.engine import ConflictResolutionEngine, Conflict, ConflictType
        assert ConflictResolutionEngine is not None

    def test_detect_conflict(self):
        from core.conflict_resolution.engine import ConflictResolutionEngine, ConflictType, ConflictSeverity
        engine = ConflictResolutionEngine()
        c = engine.detect("KU-001", ConflictType.TRANSLATION,
                          text_a="Original verse text", text_b="Different translation",
                          source_a="Edition A", source_b="Edition B")
        assert c.conflict_id is not None
        assert c.conflict_type == ConflictType.TRANSLATION

    def test_auto_classify_severity(self):
        from core.conflict_resolution.engine import ConflictResolutionEngine, ConflictType, ConflictSeverity
        engine = ConflictResolutionEngine(auto_classify=True)
        c = engine.detect("KU-002", ConflictType.SEMANTIC,
                          text_a="word1 word2 word3 word4 word5",
                          text_b="completely different text here now")
        assert c.severity in [ConflictSeverity.MINOR, ConflictSeverity.MODERATE,
                              ConflictSeverity.MAJOR, ConflictSeverity.CRITICAL]

    def test_similar_text_minor_severity(self):
        from core.conflict_resolution.engine import ConflictResolutionEngine, ConflictType, ConflictSeverity
        engine = ConflictResolutionEngine(auto_classify=True)
        c = engine.detect("KU-003", ConflictType.OCR,
                          text_a="one two three four five",
                          text_b="one two three four five")
        assert c.severity == ConflictSeverity.MINOR

    def test_resolve_conflict(self):
        from core.conflict_resolution.engine import ConflictResolutionEngine, ConflictType, ConflictStatus
        engine = ConflictResolutionEngine()
        c = engine.detect("KU-004", ConflictType.PUBLISHER, title="Publisher difference")
        result = engine.resolve(c.conflict_id, resolution="Edition B is authoritative",
                                resolved_by="expert_reviewer")
        assert result is True
        assert engine._conflicts[c.conflict_id].status == ConflictStatus.RESOLVED

    def test_get_conflicts(self):
        from core.conflict_resolution.engine import ConflictResolutionEngine, ConflictType
        engine = ConflictResolutionEngine()
        engine.detect("KU-010", ConflictType.TRANSLATION)
        engine.detect("KU-010", ConflictType.COMMENTARY)
        engine.detect("KU-011", ConflictType.OCR)
        conflicts = engine.get_conflicts("KU-010")
        assert len(conflicts) == 2

    def test_get_unresolved(self):
        from core.conflict_resolution.engine import ConflictResolutionEngine, ConflictType
        engine = ConflictResolutionEngine()
        c1 = engine.detect("KU-020", ConflictType.HISTORICAL)
        c2 = engine.detect("KU-021", ConflictType.METADATA)
        engine.resolve(c1.conflict_id, "Resolved")
        unresolved = engine.get_unresolved()
        assert len(unresolved) == 1

    def test_get_by_severity(self):
        from core.conflict_resolution.engine import ConflictResolutionEngine, ConflictType, ConflictSeverity
        engine = ConflictResolutionEngine(auto_classify=False)
        engine.detect("KU-030", ConflictType.TRANSLATION, severity=ConflictSeverity.CRITICAL)
        engine.detect("KU-031", ConflictType.OCR, severity=ConflictSeverity.MINOR)
        critical = engine.get_by_severity(ConflictSeverity.CRITICAL)
        assert len(critical) == 1

    def test_summary(self):
        from core.conflict_resolution.engine import ConflictResolutionEngine, ConflictType
        engine = ConflictResolutionEngine()
        engine.detect("KU-040", ConflictType.TRANSLATION)
        engine.detect("KU-041", ConflictType.OCR)
        engine.detect("KU-042", ConflictType.SEMANTIC)
        s = engine.summary()
        assert s["total"] == 3
        assert "by_type" in s
        assert "by_severity" in s

    def test_count(self):
        from core.conflict_resolution.engine import ConflictResolutionEngine, ConflictType
        engine = ConflictResolutionEngine()
        assert engine.count() == 0
        engine.detect("KU-050", ConflictType.NUMBERING)
        assert engine.count() == 1

    def test_all_conflict_types(self):
        from core.conflict_resolution.engine import ConflictResolutionEngine, ConflictType
        engine = ConflictResolutionEngine()
        for ct in ConflictType:
            engine.detect("KU-060", ct)
        assert engine.count() == len(ConflictType)
