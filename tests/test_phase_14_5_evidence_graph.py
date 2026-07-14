"""Phase 14.5 — Evidence Graph Engine Tests."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))


class TestEvidenceGraph:
    def test_imports(self):
        from core.evidence_graph.engine import EvidenceGraphEngine, EvidenceNode, EvidenceEdge
        assert EvidenceGraphEngine is not None

    def test_add_node(self):
        from core.evidence_graph.engine import EvidenceGraphEngine, NodeType
        engine = EvidenceGraphEngine()
        node = engine.add_node(NodeType.PARAGRAPH, label="Test paragraph")
        assert node.node_id is not None
        assert node.node_type == NodeType.PARAGRAPH

    def test_add_edge(self):
        from core.evidence_graph.engine import EvidenceGraphEngine, NodeType, EdgeType
        engine = EvidenceGraphEngine()
        n1 = engine.add_node(NodeType.PARAGRAPH, label="P1")
        n2 = engine.add_node(NodeType.SOURCE, label="S1")
        edge = engine.add_edge(n1.node_id, n2.node_id, EdgeType.EVIDENCE_FOR)
        assert edge.edge_id is not None

    def test_get_edges_from(self):
        from core.evidence_graph.engine import EvidenceGraphEngine, NodeType, EdgeType
        engine = EvidenceGraphEngine()
        n1 = engine.add_node(NodeType.BOOK, label="Book")
        n2 = engine.add_node(NodeType.SOURCE, label="Source")
        n3 = engine.add_node(NodeType.EDITION, label="Edition")
        engine.add_edge(n1.node_id, n2.node_id, EdgeType.EVIDENCE_FOR)
        engine.add_edge(n1.node_id, n3.node_id, EdgeType.SUPPORTS)
        edges = engine.get_edges_from(n1.node_id)
        assert len(edges) == 2

    def test_get_nodes_by_type(self):
        from core.evidence_graph.engine import EvidenceGraphEngine, NodeType
        engine = EvidenceGraphEngine()
        engine.add_node(NodeType.BOOK, label="B1")
        engine.add_node(NodeType.BOOK, label="B2")
        engine.add_node(NodeType.SOURCE, label="S1")
        books = engine.get_nodes_by_type(NodeType.BOOK)
        assert len(books) == 2

    def test_find_supporting_evidence(self):
        from core.evidence_graph.engine import EvidenceGraphEngine, NodeType, EdgeType
        engine = EvidenceGraphEngine()
        p = engine.add_node(NodeType.PARAGRAPH, label="P1")
        s = engine.add_node(NodeType.SOURCE, label="S1")
        engine.add_edge(p.node_id, s.node_id, EdgeType.SUPPORTS)
        supporting = engine.find_supporting_evidence(p.node_id)
        assert len(supporting) == 1

    def test_find_contradictions(self):
        from core.evidence_graph.engine import EvidenceGraphEngine, NodeType, EdgeType
        engine = EvidenceGraphEngine()
        p = engine.add_node(NodeType.PARAGRAPH, label="P1")
        s = engine.add_node(NodeType.SOURCE, label="S1")
        engine.add_edge(p.node_id, s.node_id, EdgeType.CONTRADICTS)
        contradictions = engine.find_contradictions(p.node_id)
        assert len(contradictions) == 1

    def test_summary(self):
        from core.evidence_graph.engine import EvidenceGraphEngine, NodeType, EdgeType
        engine = EvidenceGraphEngine()
        n1 = engine.add_node(NodeType.BOOK, label="B1")
        n2 = engine.add_node(NodeType.SOURCE, label="S1")
        engine.add_edge(n1.node_id, n2.node_id, EdgeType.SUPPORTS)
        s = engine.summary()
        assert s["nodes"] == 2
        assert s["edges"] == 1
