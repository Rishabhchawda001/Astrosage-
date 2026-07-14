"""Phase 16 — Alignment, Variants, Reconstruction, Confidence, Graph, Relationships, Validation, Statistics Tests."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))


class TestUnitAlignment:
    def test_align(self):
        from core.unit_alignment.engine import UnitAlignmentEngine
        engine = UnitAlignmentEngine()
        rec = engine.align("KU-001", "KU-002", alignment_type="translation",
                           source_language="sanskrit", target_language="english")
        assert rec.record_id is not None

    def test_get_alignments(self):
        from core.unit_alignment.engine import UnitAlignmentEngine
        engine = UnitAlignmentEngine()
        engine.align("KU-001", "KU-002", alignment_type="translation")
        engine.align("KU-001", "KU-003", alignment_type="commentary")
        aligns = engine.get_alignments("KU-001")
        assert len(aligns) == 2

    def test_summary(self):
        from core.unit_alignment.engine import UnitAlignmentEngine
        engine = UnitAlignmentEngine()
        engine.align("KU-010", "KU-011", alignment_type="translation")
        s = engine.summary()
        assert s["total"] == 1


class TestUnitVariants:
    def test_add(self):
        from core.unit_variants.engine import UnitVariantEngine
        engine = UnitVariantEngine()
        v = engine.add("KU-001", text="original text", is_primary=True)
        assert v.variant_id is not None
        assert v.is_primary is True

    def test_get_primary(self):
        from core.unit_variants.engine import UnitVariantEngine
        engine = UnitVariantEngine()
        engine.add("KU-002", text="primary", is_primary=True)
        engine.add("KU-002", text="secondary", variant_type="edition_variant")
        primary = engine.get_primary("KU-002")
        assert primary.text == "primary"

    def test_get_variants(self):
        from core.unit_variants.engine import UnitVariantEngine
        engine = UnitVariantEngine()
        engine.add("KU-003", text="V1")
        engine.add("KU-003", text="V2")
        vs = engine.get_variants("KU-003")
        assert len(vs) == 2

    def test_summary(self):
        from core.unit_variants.engine import UnitVariantEngine
        engine = UnitVariantEngine()
        engine.add("KU-004", text="V1")
        s = engine.summary()
        assert s["total"] == 1


class TestUnitReconstruction:
    def test_create_candidate(self):
        from core.unit_reconstruction.engine import UnitReconstructionEngine
        engine = UnitReconstructionEngine()
        r = engine.create_candidate("KU-001", original_text="old", recovered_text="new",
                                    confidence=0.8, sources=["src1"])
        assert r.recovery_id is not None

    def test_verify(self):
        from core.unit_reconstruction.engine import UnitReconstructionEngine, RecoveryStatus
        engine = UnitReconstructionEngine()
        r = engine.create_candidate("KU-002", confidence=0.9)
        engine.verify(r.recovery_id, verified=True, reason="Confirmed")
        assert r.status == RecoveryStatus.VERIFIED

    def test_summary(self):
        from core.unit_reconstruction.engine import UnitReconstructionEngine
        engine = UnitReconstructionEngine()
        engine.create_candidate("KU-003", confidence=0.8)
        s = engine.summary()
        assert s["total"] == 1


class TestUnitConfidence:
    def test_compute(self):
        from core.unit_confidence.engine import UnitConfidenceEngine
        engine = UnitConfidenceEngine()
        cs = engine.compute("KU-001", evidence_score=0.8, trust_score=0.7,
                            agreement_score=0.9)
        assert cs.overall_confidence > 0

    def test_get(self):
        from core.unit_confidence.engine import UnitConfidenceEngine
        engine = UnitConfidenceEngine()
        engine.compute("KU-002", evidence_score=0.5)
        cs = engine.get("KU-002")
        assert cs is not None

    def test_summary(self):
        from core.unit_confidence.engine import UnitConfidenceEngine
        engine = UnitConfidenceEngine()
        engine.compute("KU-003", evidence_score=0.8, trust_score=0.7)
        s = engine.summary()
        assert s["total"] == 1
        assert s["mean_confidence"] > 0


class TestUnitGraph:
    def test_add_node(self):
        from core.unit_graph.engine import UnitGraphEngine, NodeType
        engine = UnitGraphEngine()
        n = engine.add_node(NodeType.UNIT, label="Test", unit_id="KU-001")
        assert n.node_id is not None

    def test_add_edge(self):
        from core.unit_graph.engine import UnitGraphEngine, NodeType, EdgeType
        engine = UnitGraphEngine()
        n1 = engine.add_node(NodeType.BOOK, label="Book")
        n2 = engine.add_node(NodeType.UNIT, label="Unit")
        e = engine.add_edge(n1.node_id, n2.node_id, EdgeType.CONTAINS)
        assert e.edge_id is not None

    def test_get_edges(self):
        from core.unit_graph.engine import UnitGraphEngine, NodeType, EdgeType
        engine = UnitGraphEngine()
        n1 = engine.add_node(NodeType.BOOK, label="B")
        n2 = engine.add_node(NodeType.UNIT, label="U1")
        n3 = engine.add_node(NodeType.UNIT, label="U2")
        engine.add_edge(n1.node_id, n2.node_id, EdgeType.CONTAINS)
        engine.add_edge(n1.node_id, n3.node_id, EdgeType.CONTAINS)
        edges = engine.get_edges_from(n1.node_id)
        assert len(edges) == 2

    def test_summary(self):
        from core.unit_graph.engine import UnitGraphEngine, NodeType, EdgeType
        engine = UnitGraphEngine()
        n1 = engine.add_node(NodeType.BOOK, label="B")
        n2 = engine.add_node(NodeType.UNIT, label="U")
        engine.add_edge(n1.node_id, n2.node_id, EdgeType.CONTAINS)
        s = engine.summary()
        assert s["nodes"] == 2
        assert s["edges"] == 1


class TestUnitRelationships:
    def test_add(self):
        from core.unit_relationships.engine import UnitRelationshipEngine
        engine = UnitRelationshipEngine()
        r = engine.add("KU-001", "KU-002", "translated_by")
        assert r.relationship_id is not None

    def test_find_related(self):
        from core.unit_relationships.engine import UnitRelationshipEngine
        engine = UnitRelationshipEngine()
        engine.add("KU-001", "KU-002", "translated_by")
        engine.add("KU-003", "KU-001", "commented_by")
        related = engine.find_related("KU-001")
        assert len(related) == 2

    def test_summary(self):
        from core.unit_relationships.engine import UnitRelationshipEngine
        engine = UnitRelationshipEngine()
        engine.add("KU-010", "KU-011", "references")
        s = engine.summary()
        assert s["total"] == 1


class TestUnitValidation:
    def test_validate_pass(self):
        from core.unit_validation.engine import UnitValidationEngine, ValidationStatus
        engine = UnitValidationEngine(min_evidence=2)
        r = engine.validate("KU-001", "evidence", evidence_count=5)
        assert r.status == ValidationStatus.PASSED

    def test_validate_fail(self):
        from core.unit_validation.engine import UnitValidationEngine, ValidationStatus
        engine = UnitValidationEngine(min_evidence=3)
        r = engine.validate("KU-002", "evidence", evidence_count=1)
        assert r.status == ValidationStatus.FAILED

    def test_get_failed(self):
        from core.unit_validation.engine import UnitValidationEngine
        engine = UnitValidationEngine(min_evidence=5)
        engine.validate("KU-010", "evidence", evidence_count=1)
        engine.validate("KU-011", "evidence", evidence_count=10)
        failed = engine.get_failed()
        assert len(failed) == 1

    def test_summary(self):
        from core.unit_validation.engine import UnitValidationEngine
        engine = UnitValidationEngine(min_evidence=1)
        engine.validate("KU-020", "confidence", confidence=0.9)
        s = engine.summary()
        assert s["total"] == 1


class TestUnitStatistics:
    def test_record(self):
        from core.unit_statistics.engine import UnitStatisticsEngine
        engine = UnitStatisticsEngine()
        stats = engine.record("BK-001", book_title="Test",
                              total_units=100, verified_units=80)
        assert stats.total_units == 100
        assert stats.completeness_pct == 80.0

    def test_corpus_summary(self):
        from core.unit_statistics.engine import UnitStatisticsEngine
        engine = UnitStatisticsEngine()
        engine.record("BK-010", total_units=100, verified_units=80)
        engine.record("BK-011", total_units=200, verified_units=150)
        s = engine.corpus_summary()
        assert s["total_books"] == 2
        assert s["total_units"] == 300

    def test_count(self):
        from core.unit_statistics.engine import UnitStatisticsEngine
        engine = UnitStatisticsEngine()
        engine.record("BK-020")
        assert engine.count() == 1
