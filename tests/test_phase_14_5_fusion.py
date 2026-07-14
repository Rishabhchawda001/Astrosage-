"""Phase 14.5 — Source Fusion Engine Tests."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))


class TestSourceFusion:
    def test_imports(self):
        from core.source_fusion.engine import SourceFusionEngine, FusedEvidence
        assert SourceFusionEngine is not None

    def test_fuse_majority_vote(self):
        from core.source_fusion.engine import SourceFusionEngine, FusionStrategy
        engine = SourceFusionEngine()
        result = engine.fuse("KU-001",
                             texts=["text A", "text A", "text B"],
                             strategy=FusionStrategy.MAJORITY_VOTE)
        assert result.fused_text == "text A"
        assert result.source_count == 2
        assert result.duplicates_removed == 1  # one duplicate "text A" removed

    def test_fuse_remove_duplicates(self):
        from core.source_fusion.engine import SourceFusionEngine
        engine = SourceFusionEngine()
        result = engine.fuse("KU-002",
                             texts=["same text", "same text", "same text"])
        assert result.source_count == 1
        assert result.duplicates_removed == 2

    def test_fuse_concatenate(self):
        from core.source_fusion.engine import SourceFusionEngine, FusionStrategy
        engine = SourceFusionEngine()
        result = engine.fuse("KU-003",
                             texts=["Line 1", "Line 2", "Line 3"],
                             strategy=FusionStrategy.CONCATENATE)
        assert "Line 1" in result.fused_text
        assert "Line 2" in result.fused_text

    def test_fuse_best_source(self):
        from core.source_fusion.engine import SourceFusionEngine, FusionStrategy
        engine = SourceFusionEngine()
        result = engine.fuse("KU-004",
                             texts=["first source", "second source"],
                             strategy=FusionStrategy.BEST_SOURCE)
        assert result.fused_text == "first source"

    def test_get_fused(self):
        from core.source_fusion.engine import SourceFusionEngine
        engine = SourceFusionEngine()
        engine.fuse("KU-010", texts=["A", "B"])
        engine.fuse("KU-010", texts=["C", "D"])
        fused = engine.get_fused("KU-010")
        assert len(fused) == 2

    def test_summary(self):
        from core.source_fusion.engine import SourceFusionEngine, FusionStrategy
        engine = SourceFusionEngine()
        engine.fuse("KU-020", texts=["A", "B"], strategy=FusionStrategy.MAJORITY_VOTE)
        engine.fuse("KU-021", texts=["C"], strategy=FusionStrategy.CONCATENATE)
        s = engine.summary()
        assert s["total"] == 2

    def test_count(self):
        from core.source_fusion.engine import SourceFusionEngine
        engine = SourceFusionEngine()
        assert engine.count() == 0
        engine.fuse("KU-030", texts=["A"])
        assert engine.count() == 1
