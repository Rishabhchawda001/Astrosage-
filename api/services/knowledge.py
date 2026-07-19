"""
Knowledge service — interfaces with the frozen AstroSage knowledge layer.

Provides BM25 search, knowledge graph queries, entity lookup,
and scripture metadata retrieval from the v1.0.0 frozen release.
"""
from __future__ import annotations

import json
import os
import re
import time
import numpy as np
from collections import defaultdict
from pathlib import Path
from typing import Optional

from api.config import settings


class KnowledgeGraphService:
    """Service for querying the frozen knowledge graph."""

    def __init__(self, base_path: str | None = None):
        self.base_path = Path(base_path or settings.knowledge_base_path)
        self._graph: dict | None = None
        self._entities: list[dict] = []
        self._entity_index: dict[str, dict] = {}  # name.lower() -> entity
        self._scriptures: list[dict] = []
        self._scripture_index: dict[str, dict] = {}  # id.lower() -> scripture
        self._edges: list[dict] = []
        self._edges_by_entity: dict[str, list[dict]] = defaultdict(list)
        self._loaded = False

    def load(self) -> "KnowledgeGraphService":
        """Load the knowledge graph into memory."""
        if self._loaded:
            return self

        graph_path = self.base_path / "graph" / "graph.json"
        with open(graph_path) as f:
            self._graph = json.load(f)

        for node in self._graph.get("nodes", []):
            name = node.get("name", "")
            if name:
                self._entity_index[name.lower()] = node
            if node.get("type") == "Scripture":
                self._scriptures.append(node)
                sid = node.get("id", "").lower()
                self._scripture_index[sid] = node
            else:
                self._entities.append(node)

        for edge in self._graph.get("edges", []):
            self._edges.append(edge)
            src = edge.get("source_GUID", "")
            tgt = edge.get("target_GUID", "")
            self._edges_by_entity[src].append(edge)
            self._edges_by_entity[tgt].append(edge)

        self._loaded = True
        return self

    def find_entity(self, name: str) -> dict | None:
        """Find entity by exact name (case-insensitive)."""
        return self._entity_index.get(name.lower())

    def search_entities(self, query: str, limit: int = 10) -> list[dict]:
        """Search entities by name substring match."""
        q = query.lower()
        results = []
        for name, entity in self._entity_index.items():
            if q in name:
                results.append({
                    "name": entity.get("name", ""),
                    "type": entity.get("type", ""),
                    "guid": entity.get("GUID", ""),
                    "total_mentions": entity.get("total_mentions", 0),
                })
            if len(results) >= limit:
                break
        return results

    def get_entity_relationships(self, entity_guid: str) -> list[dict]:
        """Get all relationships for an entity."""
        edges = self._edges_by_entity.get(entity_guid, [])
        results = []
        seen = set()
        for edge in edges:
            if edge.get("GUID") in seen:
                continue
            seen.add(edge.get("GUID"))
            src_guid = edge.get("source_GUID", "")
            tgt_guid = edge.get("target_GUID", "")
            is_source = src_guid == entity_guid
            other_guid = tgt_guid if is_source else src_guid
            other_entity = self._entity_index.get(
                self._get_name_for_guid(other_guid, "").lower()
            )
            results.append({
                "type": edge.get("type", ""),
                "direction": "outgoing" if is_source else "incoming",
                "target_guid": other_guid,
                "target_name": self._get_name_for_guid(other_guid, "unknown"),
                "target_type": other_entity.get("type", "") if other_entity else "",
                "confidence": edge.get("confidence", 0),
            })
        return results

    def get_entity_detail(self, guid: str) -> dict | None:
        """Get full entity details by GUID."""
        for node in self._graph.get("nodes", []) if self._graph else []:
            if node.get("GUID") == guid:
                return node
        return None

    def get_scripture(self, scripture_id: str) -> dict | None:
        """Get scripture metadata by ID (case-insensitive)."""
        return self._scripture_index.get(scripture_id.lower())

    def list_scriptures(self) -> list[dict]:
        """List all indexed scriptures."""
        return [
            {
                "id": s.get("id", ""),
                "name": s.get("canonical_name", s.get("id", "")),
                "type": s.get("type", ""),
                "verses": s.get("total_verses", 0),
                "coverage": s.get("coverage", 0),
                "source": s.get("primary_source", ""),
                "certification": s.get("certification", ""),
            }
            for s in self._scriptures
        ]

    def find_path(self, start_guid: str, end_guid: str, max_depth: int = 3) -> list[str] | None:
        """BFS path finding between two entities."""
        if max_depth <= 0:
            return None
        visited = {start_guid}
        queue: list[tuple[str, list[str]]] = [(start_guid, [start_guid])]
        while queue:
            current, path = queue.pop(0)
            if current == end_guid:
                return path
            if len(path) > max_depth:
                continue
            for edge in self._edges_by_entity.get(current, []):
                next_guid = (
                    edge["target_GUID"]
                    if edge["source_GUID"] == current
                    else edge["source_GUID"]
                )
                if next_guid not in visited:
                    visited.add(next_guid)
                    queue.append((next_guid, path + [next_guid]))
        return None

    def _get_name_for_guid(self, guid: str, default: str = "") -> str:
        """Look up entity name by GUID."""
        for name, entity in self._entity_index.items():
            if entity.get("GUID") == guid:
                return entity.get("name", default)
        # Check scriptures
        for sid, s in self._scripture_index.items():
            if s.get("GUID") == guid:
                return s.get("canonical_name", s.get("id", default))
        return default

    @property
    def stats(self) -> dict:
        return {
            "entities": len(self._entities),
            "scriptures": len(self._scriptures),
            "edges": len(self._edges),
            "edge_types": len(set(e.get("type", "") for e in self._edges)),
            "node_types": len(set(n.get("type", "") for n in self._graph.get("nodes", []))) if self._graph else 0,
        }


class BM25SearchService:
    """BM25-based lexical search over frozen chunks."""

    def __init__(self, base_path: str | None = None):
        self.base_path = Path(base_path or settings.knowledge_base_path)
        self._bm25_data: dict | None = None
        self._chunks: list[dict] = []
        self._loaded = False

    def load(self) -> "BM25SearchService":
        """Load BM25 index and chunks."""
        if self._loaded:
            return self

        # Load BM25 data
        bm25_path = self.base_path / "retrieval" / "bm25_index.json"
        with open(bm25_path) as f:
            self._bm25_data = json.load(f)

        # Load chunks
        chunks_dir = self.base_path / "chunks"
        for fname in ["scripture_chunks.json", "dialogue_chunks.json",
                       "entity_chunks.json", "event_chunks.json"]:
            fpath = chunks_dir / fname
            if fpath.exists():
                with open(fpath) as f:
                    self._chunks.extend(json.load(f))

        verses_dir = chunks_dir / "verses"
        if verses_dir.is_dir():
            for fname in sorted(os.listdir(verses_dir)):
                if fname.endswith(".json"):
                    with open(verses_dir / fname) as f:
                        self._chunks.extend(json.load(f))

        # Build text representations for BM25 scoring
        self._texts: list[str] = []
        for c in self._chunks:
            level = c.get("level", "")
            text = c.get("text", "")
            scripture = c.get("scripture_id", "")
            prefix = f"[{level}] "
            if scripture and level != "scripture":
                prefix += f"{scripture}: "
            self._texts.append(prefix + text)

        self._loaded = True
        return self

    def _tokenize(self, text: str) -> list[str]:
        """Simple word tokenization."""
        return re.findall(r'\w+', text.lower())

    def search(self, query: str, top_k: int = 10) -> list[dict]:
        """Search using BM25 scoring."""
        if not self._loaded or not self._bm25_data:
            return []

        query_tokens = self._tokenize(query)
        N = self._bm25_data["N"]
        doc_freqs = self._bm25_data["doc_freqs"]
        doc_lengths = self._bm25_data["doc_lengths"]
        avg_dl = self._bm25_data["avg_dl"]
        k1 = self._bm25_data["k1"]
        b = self._bm25_data["b"]

        scores = np.zeros(N)
        for qt in query_tokens:
            if qt not in doc_freqs:
                continue
            df = doc_freqs[qt]
            idf = np.log((N - df + 0.5) / (df + 0.5) + 1)
            for i in range(N):
                # Count tf in this document text
                tf = self._texts[i].lower().count(qt)
                if tf > 0:
                    dl = doc_lengths[i]
                    numerator = tf * (k1 + 1)
                    denominator = tf + k1 * (1 - b + b * dl / avg_dl)
                    scores[i] += idf * numerator / denominator

        top_indices = np.argsort(scores)[::-1]
        results = []
        for idx in top_indices:
            if scores[idx] <= 0:
                continue
            if len(results) >= top_k:
                break
            c = self._chunks[idx]
            results.append({
                "chunk_id": c.get("chunk_id", ""),
                "level": c.get("level", ""),
                "scripture_id": c.get("scripture_id", ""),
                "text": c.get("text", "")[:500],
                "score": round(float(scores[idx]), 4),
                "entity_links": c.get("entity_links", []),
                "provenance": c.get("provenance", {}),
            })

        return results

    @property
    def stats(self) -> dict:
        if not self._bm25_data:
            return {"loaded": False}
        return {
            "loaded": True,
            "total_chunks": self._bm25_data["N"],
            "vocabulary_size": len(self._bm25_data["doc_freqs"]),
            "avg_doc_length": round(self._bm25_data["avg_dl"], 1),
        }


class AnswerService:
    """Generates grounded answers from the knowledge graph."""

    def __init__(self, graph_service: KnowledgeGraphService, search_service: BM25SearchService):
        self.graph = graph_service
        self.search = search_service

    def answer(self, question: str, top_k: int = 5) -> dict:
        """Generate a grounded answer with evidence."""
        # Search for relevant chunks
        search_results = self.search.search(question, top_k=top_k * 3)

        # Find matching entities in the graph
        found_entities: list[dict] = []
        query_lower = question.lower()
        for name, entity in self.graph._entity_index.items():
            words = name.split()
            if any(w in query_lower for w in words if len(w) > 2):
                found_entities.append({
                    "name": entity.get("name", ""),
                    "type": entity.get("type", ""),
                    "guid": entity.get("GUID", ""),
                })
            if len(found_entities) >= 5:
                break

        # Get relationships for found entities
        relationships: list[dict] = []
        for fe in found_entities:
            rels = self.graph.get_entity_relationships(fe.get("guid", ""))
            relationships.extend([r for r in rels if r not in relationships])

        # Build evidence
        evidence = [
            {
                "text": r.get("text", "")[:200],
                "scripture": r.get("scripture_id", ""),
                "level": r.get("level", ""),
                "score": r.get("score", 0),
            }
            for r in search_results[:top_k]
        ]

        confidence = "high" if len(evidence) >= 3 and len(found_entities) >= 1 else \
            "medium" if len(evidence) >= 2 else "low"

        return {
            "question": question,
            "answer": {
                "summary": f"Based on {len(evidence)} sources from the knowledge base.",
                "entities_found": [e["name"] for e in found_entities],
                "evidence_count": len(evidence),
                "confidence": confidence,
            },
            "entities": found_entities[:5],
            "relationships": relationships[:10],
            "sources": evidence[:top_k],
            "provenance": {
                "knowledge_version": "v1.0.0",
                "source": "AstroSage Knowledge Engine",
            },
        }
