"""Unit Graph — Knowledge graph nodes for every unit."""
from __future__ import annotations
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any

class NodeType(str, Enum):
    UNIT = "unit"
    BOOK = "book"
    CHAPTER = "chapter"
    VERSE = "verse"
    CONCEPT = "concept"
    ENTITY = "entity"
    SOURCE = "source"
    EDITION = "edition"

class EdgeType(str, Enum):
    CONTAINS = "contains"
    QUOTES = "quotes"
    REFERENCES = "references"
    EXPLAINS = "explains"
    TRANSLATED_BY = "translated_by"
    COMMENTED_BY = "commented_by"
    DERIVED_FROM = "derived_from"
    EDITION_OF = "edition_of"
    VARIANT_OF = "variant_of"
    CONTRADICTS = "contradicts"
    SUPPORTS = "supports"

@dataclass
class GraphNode:
    node_id: str = ""
    node_type: NodeType = NodeType.UNIT
    label: str = ""
    unit_id: str = ""
    confidence: float = 0.0
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    metadata: dict[str, Any] = field(default_factory=dict)
    def __post_init__(self):
        if not self.node_id:
            self.node_id = f"GN-{uuid.uuid4().hex[:12]}"

@dataclass
class GraphEdge:
    edge_id: str = ""
    source_node: str = ""
    target_node: str = ""
    edge_type: EdgeType = EdgeType.CONTAINS
    weight: float = 1.0
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    metadata: dict[str, Any] = field(default_factory=dict)
    def __post_init__(self):
        if not self.edge_id:
            self.edge_id = f"GE-{uuid.uuid4().hex[:12]}"

class UnitGraphEngine:
    def __init__(self):
        self._nodes: dict[str, GraphNode] = {}
        self._edges: dict[str, GraphEdge] = {}
        self._by_type: dict[str, list[str]] = {}
        self._outgoing: dict[str, list[str]] = {}
        self._incoming: dict[str, list[str]] = {}

    def add_node(self, node_type: NodeType, label: str = "",
                 unit_id: str = "", confidence: float = 0.0, **kwargs) -> GraphNode:
        n = GraphNode(node_type=node_type, label=label, unit_id=unit_id,
                      confidence=confidence, metadata=kwargs)
        self._nodes[n.node_id] = n
        self._by_type.setdefault(node_type.value, []).append(n.node_id)
        return n

    def add_edge(self, source_node: str, target_node: str,
                 edge_type: EdgeType, weight: float = 1.0, **kwargs) -> GraphEdge:
        if source_node not in self._nodes or target_node not in self._nodes:
            return GraphEdge()
        e = GraphEdge(source_node=source_node, target_node=target_node,
                      edge_type=edge_type, weight=weight, metadata=kwargs)
        self._edges[e.edge_id] = e
        self._outgoing.setdefault(source_node, []).append(e.edge_id)
        self._incoming.setdefault(target_node, []).append(e.edge_id)
        return e

    def get_node(self, node_id: str) -> GraphNode | None:
        return self._nodes.get(node_id)

    def get_edges_from(self, node_id: str) -> list[GraphEdge]:
        ids = self._outgoing.get(node_id, [])
        return [self._edges[eid] for eid in ids if eid in self._edges]

    def get_edges_to(self, node_id: str) -> list[GraphEdge]:
        ids = self._incoming.get(node_id, [])
        return [self._edges[eid] for eid in ids if eid in self._edges]

    def node_count(self) -> int:
        return len(self._nodes)

    def edge_count(self) -> int:
        return len(self._edges)

    def summary(self) -> dict:
        nc: dict[str, int] = {}
        for n in self._nodes.values():
            nc[n.node_type.value] = nc.get(n.node_type.value, 0) + 1
        ec: dict[str, int] = {}
        for e in self._edges.values():
            ec[e.edge_type.value] = ec.get(e.edge_type.value, 0) + 1
        return {"nodes": self.node_count(), "edges": self.edge_count(),
                "by_node_type": nc, "by_edge_type": ec}
