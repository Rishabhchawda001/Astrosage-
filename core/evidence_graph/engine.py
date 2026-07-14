"""
Evidence Graph Engine — Complete evidence graph linking every paragraph to sources.

Every paragraph links to sources, editions, publishers, translations,
commentaries, citations, knowledge passport, and confidence.
"""
from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Optional


class NodeType(str, Enum):
    PARAGRAPH = "paragraph"
    SOURCE = "source"
    EDITION = "edition"
    PUBLISHER = "publisher"
    TRANSLATION = "translation"
    COMMENTARY = "commentary"
    CITATION = "citation"
    PASSPORT = "passport"
    BOOK = "book"
    CHAPTER = "chapter"
    VERSE = "verse"


class EdgeType(str, Enum):
    SUPPORTS = "supports"
    CONTRADICTS = "contradicts"
    DERIVED_FROM = "derived_from"
    TRANSLATION_OF = "translation_of"
    COMMENTARY_ON = "commentary_on"
    CITES = "cites"
    EVIDENCE_FOR = "evidence_for"
    VERSION_OF = "version_of"
    CONFLICTS_WITH = "conflicts_with"


@dataclass
class EvidenceNode:
    node_id: str = ""
    node_type: NodeType = NodeType.PARAGRAPH
    label: str = ""
    confidence: float = 0.0
    evidence_count: int = 0
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    metadata: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self):
        if not self.node_id:
            self.node_id = f"EN-{uuid.uuid4().hex[:12]}"


@dataclass
class EvidenceEdge:
    edge_id: str = ""
    source_node: str = ""
    target_node: str = ""
    edge_type: EdgeType = EdgeType.SUPPORTS
    weight: float = 1.0
    evidence_ids: list[str] = field(default_factory=list)
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    metadata: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self):
        if not self.edge_id:
            self.edge_id = f"EE-{uuid.uuid4().hex[:12]}"


class EvidenceGraphEngine:
    """Production evidence graph engine."""

    def __init__(self):
        self._nodes: dict[str, EvidenceNode] = {}
        self._edges: dict[str, EvidenceEdge] = {}
        self._by_type: dict[str, list[str]] = {}
        self._outgoing: dict[str, list[str]] = {}
        self._incoming: dict[str, list[str]] = {}

    def add_node(self, node_type: NodeType, label: str = "",
                 confidence: float = 0.0, evidence_count: int = 0,
                 **kwargs) -> EvidenceNode:
        node = EvidenceNode(node_type=node_type, label=label,
                           confidence=confidence, evidence_count=evidence_count,
                           metadata=kwargs)
        self._nodes[node.node_id] = node
        self._by_type.setdefault(node_type.value, []).append(node.node_id)
        return node

    def add_edge(self, source_node: str, target_node: str,
                 edge_type: EdgeType, weight: float = 1.0,
                 evidence_ids: list[str] | None = None, **kwargs) -> EvidenceEdge:
        if source_node not in self._nodes or target_node not in self._nodes:
            return EvidenceEdge()
        edge = EvidenceEdge(source_node=source_node, target_node=target_node,
                           edge_type=edge_type, weight=weight,
                           evidence_ids=evidence_ids or [], metadata=kwargs)
        self._edges[edge.edge_id] = edge
        self._outgoing.setdefault(source_node, []).append(edge.edge_id)
        self._incoming.setdefault(target_node, []).append(edge.edge_id)
        return edge

    def get_node(self, node_id: str) -> EvidenceNode | None:
        return self._nodes.get(node_id)

    def get_edges_from(self, node_id: str) -> list[EvidenceEdge]:
        ids = self._outgoing.get(node_id, [])
        return [self._edges[eid] for eid in ids if eid in self._edges]

    def get_edges_to(self, node_id: str) -> list[EvidenceEdge]:
        ids = self._incoming.get(node_id, [])
        return [self._edges[eid] for eid in ids if eid in self._edges]

    def get_nodes_by_type(self, node_type: NodeType) -> list[EvidenceNode]:
        ids = self._by_type.get(node_type.value, [])
        return [self._nodes[nid] for nid in ids if nid in self._nodes]

    def find_supporting_evidence(self, paragraph_id: str) -> list[EvidenceEdge]:
        return [e for e in self.get_edges_from(paragraph_id)
                if e.edge_type in (EdgeType.SUPPORTS, EdgeType.EVIDENCE_FOR)]

    def find_contradictions(self, paragraph_id: str) -> list[EvidenceEdge]:
        return [e for e in self.get_edges_from(paragraph_id)
                if e.edge_type in (EdgeType.CONTRADICTS, EdgeType.CONFLICTS_WITH)]

    def node_count(self) -> int:
        return len(self._nodes)

    def edge_count(self) -> int:
        return len(self._edges)

    def summary(self) -> dict:
        tc: dict[str, int] = {}
        for n in self._nodes.values():
            tc[n.node_type.value] = tc.get(n.node_type.value, 0) + 1
        ec: dict[str, int] = {}
        for e in self._edges.values():
            ec[e.edge_type.value] = ec.get(e.edge_type.value, 0) + 1
        return {"nodes": self.node_count(), "edges": self.edge_count(),
                "by_node_type": tc, "by_edge_type": ec}
