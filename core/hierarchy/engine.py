"""
Hierarchy Engine — Parent-child graph for document structure.

Every chunk knows its parent, children, ancestors, and descendants.
"""
from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from typing import Any, Optional

from core.chunking.engine import Chunk, ChunkType


@dataclass
class HierarchyNode:
    """A node in the document hierarchy tree."""
    node_id: str = ""
    chunk_id: str = ""
    parent_id: str = ""
    child_ids: list[str] = field(default_factory=list)
    depth: int = 0
    label: str = ""
    chunk_type: str = ""

    def __post_init__(self):
        if not self.node_id:
            self.node_id = f"HN-{uuid.uuid4().hex[:12]}"


class HierarchyEngine:
    """
    Production hierarchy engine.

    Maintains the parent-child graph for all chunks.
    Supports ancestor/descendant queries.
    """

    def __init__(self):
        self._nodes: dict[str, HierarchyNode] = {}
        self._chunk_to_node: dict[str, str] = {}
        self._roots: list[str] = []

    def register_chunk(self, chunk: Chunk) -> str:
        node = HierarchyNode(
            chunk_id=chunk.chunk_id,
            parent_id=chunk.parent_id,
            depth=len(chunk.ancestor_ids),
            label=f"{getattr(chunk.chunk_type, "value", chunk.chunk_type)}: {chunk.text[:50]}",
            chunk_type=getattr(chunk.chunk_type, "value", chunk.chunk_type),
        )
        self._nodes[node.node_id] = node
        self._chunk_to_node[chunk.chunk_id] = node.node_id

        if not chunk.parent_id:
            self._roots.append(node.node_id)
        elif chunk.parent_id in self._chunk_to_node:
            parent_node_id = self._chunk_to_node[chunk.parent_id]
            if parent_node_id in self._nodes:
                self._nodes[parent_node_id].child_ids.append(node.node_id)

        return node.node_id

    def get_node(self, node_id: str) -> Optional[HierarchyNode]:
        return self._nodes.get(node_id)

    def get_node_for_chunk(self, chunk_id: str) -> Optional[HierarchyNode]:
        node_id = self._chunk_to_node.get(chunk_id)
        if node_id:
            return self._nodes.get(node_id)
        return None

    def get_children(self, node_id: str) -> list[HierarchyNode]:
        node = self._nodes.get(node_id)
        if not node:
            return []
        return [self._nodes[cid] for cid in node.child_ids if cid in self._nodes]

    def get_ancestors(self, node_id: str) -> list[HierarchyNode]:
        result = []
        node = self._nodes.get(node_id)
        while node and node.parent_id:
            parent = self._chunk_to_node.get(node.parent_id)
            if parent and parent in self._nodes:
                result.append(self._nodes[parent])
                node = self._nodes[parent]
            else:
                break
        return result

    def get_descendants(self, node_id: str) -> list[HierarchyNode]:
        result = []
        children = self.get_children(node_id)
        result.extend(children)
        for child in children:
            result.extend(self.get_descendants(child.node_id))
        return result

    def get_roots(self) -> list[HierarchyNode]:
        return [self._nodes[rid] for rid in self._roots if rid in self._nodes]

    def get_depth(self, node_id: str) -> int:
        node = self._nodes.get(node_id)
        return node.depth if node else -1

    def get_max_depth(self) -> int:
        return max((n.depth for n in self._nodes.values()), default=0)

    def get_nodes_at_depth(self, depth: int) -> list[HierarchyNode]:
        return [n for n in self._nodes.values() if n.depth == depth]

    def get_subtree(self, node_id: str) -> dict[str, Any]:
        """Return subtree as nested dict."""
        node = self._nodes.get(node_id)
        if not node:
            return {}
        return {
            "node_id": node.node_id,
            "chunk_id": node.chunk_id,
            "label": node.label,
            "depth": node.depth,
            "children": [self.get_subtree(cid) for cid in node.child_ids],
        }

    def count(self) -> int:
        return len(self._nodes)

    def summary(self) -> dict:
        depth_counts: dict[int, int] = {}
        type_counts: dict[str, int] = {}
        for n in self._nodes.values():
            depth_counts[n.depth] = depth_counts.get(n.depth, 0) + 1
            type_counts[n.chunk_type] = type_counts.get(n.chunk_type, 0) + 1
        return {
            "total_nodes": self.count(),
            "total_roots": len(self._roots),
            "max_depth": self.get_max_depth(),
            "by_depth": depth_counts,
            "by_type": type_counts,
        }
