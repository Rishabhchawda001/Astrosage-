"""
Provenance Graph — Traceability for every artifact.

Every object in the Knowledge Lake must be traceable:

  Source PDF → Extracted Text → Structured Markdown → Chunk → Embedding → Vector → Retrieved Context → Answer

The provenance graph records every transformation, including:
  - What was the input
  - What transformation was applied
  - What version of the tool was used
  - What was the output
  - Timestamp of the operation
  - Any errors or warnings
"""
from __future__ import annotations

import hashlib
import json
import time
from dataclasses import dataclass, field, asdict
from pathlib import Path
from typing import Optional, Any


@dataclass
class ProvenanceNode:
    """A single node in the provenance graph."""
    node_id: str
    node_type: str  # source, extraction, ocr, parse, chunk, embed, index, retrieval, answer
    artifact_id: str  # Registry ID (BOOK-xxx, PAGE-xxx, CHUNK-xxx, etc.)
    parent_node_id: Optional[str] = None
    input_path: str = ""
    output_path: str = ""
    pipeline_name: str = ""
    pipeline_version: str = ""
    timestamp: float = 0.0
    duration_seconds: float = 0.0
    success: bool = True
    error_message: str = ""
    metadata: dict = field(default_factory=dict)
    
    def __post_init__(self):
        if self.timestamp == 0.0:
            self.timestamp = time.time()


@dataclass
class ProvenanceEdge:
    """A directed edge in the provenance graph."""
    from_node: str
    to_node: str
    relationship: str  # "produced", "derived_from", "transformed_by"
    metadata: dict = field(default_factory=dict)


class ProvenanceGraph:
    """
    Directed acyclic graph (DAG) of all data transformations.
    
    Enables:
    - Tracing any answer back to its source document
    - Understanding which documents contributed to a result
    - Debugging quality issues by tracing through the pipeline
    - Reproducing any intermediate artifact
    """
    
    def __init__(self):
        self._nodes: dict[str, ProvenanceNode] = {}
        self._edges: list[ProvenanceEdge] = []
        self._node_counter = 0
    
    def _next_id(self) -> str:
        self._node_counter += 1
        return f"PV-{self._node_counter:08d}"
    
    def add_source(
        self,
        artifact_id: str,
        input_path: str,
        metadata: Optional[dict] = None,
    ) -> str:
        """Record a source document entry."""
        node_id = self._next_id()
        self._nodes[node_id] = ProvenanceNode(
            node_id=node_id,
            node_type="source",
            artifact_id=artifact_id,
            input_path=input_path,
            metadata=metadata or {},
        )
        return node_id
    
    def add_extraction(
        self,
        artifact_id: str,
        parent_node_id: str,
        input_path: str,
        output_path: str,
        pipeline_name: str,
        pipeline_version: str,
        duration: float = 0.0,
        metadata: Optional[dict] = None,
    ) -> str:
        """Record a text extraction step."""
        node_id = self._next_id()
        self._nodes[node_id] = ProvenanceNode(
            node_id=node_id,
            node_type="extraction",
            artifact_id=artifact_id,
            parent_node_id=parent_node_id,
            input_path=input_path,
            output_path=output_path,
            pipeline_name=pipeline_name,
            pipeline_version=pipeline_version,
            duration_seconds=duration,
            metadata=metadata or {},
        )
        self._edges.append(ProvenanceEdge(
            from_node=parent_node_id,
            to_node=node_id,
            relationship="produced",
        ))
        return node_id
    
    def add_ocr(
        self,
        artifact_id: str,
        parent_node_id: str,
        input_path: str,
        output_path: str,
        engine: str,
        confidence: float,
        duration: float = 0.0,
    ) -> str:
        """Record an OCR step."""
        node_id = self._next_id()
        self._nodes[node_id] = ProvenanceNode(
            node_id=node_id,
            node_type="ocr",
            artifact_id=artifact_id,
            parent_node_id=parent_node_id,
            input_path=input_path,
            output_path=output_path,
            pipeline_name=f"ocr_{engine}",
            pipeline_version="0.1.0",
            duration_seconds=duration,
            metadata={"engine": engine, "confidence": confidence},
        )
        self._edges.append(ProvenanceEdge(
            from_node=parent_node_id,
            to_node=node_id,
            relationship="transformed_by",
            metadata={"engine": engine},
        ))
        return node_id
    
    def add_chunk(
        self,
        artifact_id: str,
        parent_node_id: str,
        output_path: str,
        chunk_index: int,
        total_chunks: int,
    ) -> str:
        """Record a chunking step."""
        node_id = self._next_id()
        self._nodes[node_id] = ProvenanceNode(
            node_id=node_id,
            node_type="chunk",
            artifact_id=artifact_id,
            parent_node_id=parent_node_id,
            output_path=output_path,
            pipeline_name="semantic_chunker",
            pipeline_version="0.1.0",
            metadata={"chunk_index": chunk_index, "total_chunks": total_chunks},
        )
        self._edges.append(ProvenanceEdge(
            from_node=parent_node_id,
            to_node=node_id,
            relationship="derived_from",
        ))
        return node_id
    
    def trace_to_source(self, node_id: str) -> list[ProvenanceNode]:
        """Trace an artifact back to its source document."""
        path = []
        current = node_id
        while current:
            node = self._nodes.get(current)
            if not node:
                break
            path.append(node)
            current = node.parent_node_id
        return list(reversed(path))
    
    def get_node(self, node_id: str) -> Optional[ProvenanceNode]:
        return self._nodes.get(node_id)
    
    def get_children(self, node_id: str) -> list[ProvenanceNode]:
        child_ids = [e.to_node for e in self._edges if e.from_node == node_id]
        return [self._nodes[cid] for cid in child_ids if cid in self._nodes]
    
    @property
    def total_nodes(self) -> int:
        return len(self._nodes)
    
    @property
    def total_edges(self) -> int:
        return len(self._edges)
    
    def summary(self) -> dict:
        types = {}
        for n in self._nodes.values():
            types[n.node_type] = types.get(n.node_type, 0) + 1
        return {
            "total_nodes": self.total_nodes,
            "total_edges": self.total_edges,
            "by_type": types,
        }
    
    def save(self, filepath: Path):
        """Save the provenance graph to JSON."""
        data = {
            "nodes": {nid: asdict(n) for nid, n in self._nodes.items()},
            "edges": [asdict(e) for e in self._edges],
            "summary": self.summary(),
        }
        filepath.parent.mkdir(parents=True, exist_ok=True)
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
    
    def load(self, filepath: Path):
        """Load the provenance graph from JSON."""
        with open(filepath, "r", encoding="utf-8") as f:
            data = json.load(f)
        
        self._nodes = {}
        for nid, ndata in data.get("nodes", {}).items():
            self._nodes[nid] = ProvenanceNode(**ndata)
        
        self._edges = [ProvenanceEdge(**e) for e in data.get("edges", [])]
        self._node_counter = len(self._nodes)
