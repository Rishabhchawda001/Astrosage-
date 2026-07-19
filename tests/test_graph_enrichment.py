"""Tests for the Knowledge Graph Enrichment Engine."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))


class TestGraphEnrichment:
    def test_imports(self):
        from core.graph_enrichment.enrichment import GraphEnrichmentEngine
        assert GraphEnrichmentEngine is not None

    def test_init(self):
        from core.graph_enrichment.enrichment import GraphEnrichmentEngine
        engine = GraphEnrichmentEngine()
        assert engine is not None

    def test_load_graph(self):
        from core.graph_enrichment.enrichment import GraphEnrichmentEngine
        engine = GraphEnrichmentEngine()
        engine.load()
        assert engine._loaded
        assert engine._graph is not None

    def test_analyze(self):
        from core.graph_enrichment.enrichment import GraphEnrichmentEngine
        engine = GraphEnrichmentEngine()
        engine.load()
        report = engine.analyze()
        assert report.total_edges_analyzed > 0
        assert report.mentioned_in_edges > 0
        assert len(report.proposed_enrichments) > 0

    def test_enrichment_proposals_have_guid(self):
        from core.graph_enrichment.enrichment import GraphEnrichmentEngine
        engine = GraphEnrichmentEngine()
        engine.load()
        report = engine.analyze()
        for proposal in report.proposed_enrichments:
            assert proposal.edge_guid != ""
            assert proposal.current_type == "MENTIONED_IN"
            assert proposal.proposed_type != "MENTIONED_IN"

    def test_confidence_range(self):
        from core.graph_enrichment.enrichment import GraphEnrichmentEngine
        engine = GraphEnrichmentEngine()
        engine.load()
        report = engine.analyze()
        for proposal in report.proposed_enrichments:
            assert 0.0 <= proposal.confidence <= 1.0

    def test_type_distribution(self):
        from core.graph_enrichment.enrichment import GraphEnrichmentEngine
        engine = GraphEnrichmentEngine()
        engine.load()
        report = engine.analyze()
        assert "MENTIONED_IN" in report.type_distribution
        assert report.type_distribution["MENTIONED_IN"] > 0

    def test_confidence_stats(self):
        from core.graph_enrichment.enrichment import GraphEnrichmentEngine
        engine = GraphEnrichmentEngine()
        engine.load()
        report = engine.analyze()
        assert "mean" in report.confidence_stats
        assert "min" in report.confidence_stats
        assert "max" in report.confidence_stats
        assert report.confidence_stats["mean"] > 0

    def test_enrichment_rules_cover_types(self):
        from core.graph_enrichment.enrichment import GraphEnrichmentEngine
        engine = GraphEnrichmentEngine()
        assert len(engine.ENRICHMENT_RULES) > 0

    def test_propose_enrichments_person_scripture(self):
        from core.graph_enrichment.enrichment import GraphEnrichmentEngine
        engine = GraphEnrichmentEngine()
        engine.load()
        # Find a Person-Scripture MENTIONED_IN edge
        for edge in engine._graph.get("edges", []):
            if edge["type"] == "MENTIONED_IN":
                src = engine._node_index.get(edge["source_GUID"], {})
                tgt = engine._node_index.get(edge["target_GUID"], {})
                if src.get("type") == "Person" and tgt.get("type") == "Scripture":
                    proposals = engine._propose_enrichments(edge)
                    assert len(proposals) > 0
                    assert proposals[0].proposed_type in ["TEACHES", "COMPILER_OF", "AUTHOR_OF", "MENTIONS"]
                    break

    def test_name_pattern_detection(self):
        from core.graph_enrichment.enrichment import GraphEnrichmentEngine
        engine = GraphEnrichmentEngine()
        engine.load()
        # Test name pattern matching
        assert "son" in engine.NAME_PATTERNS
        assert "father" in engine.NAME_PATTERNS
        assert "teacher" in engine.NAME_PATTERNS
