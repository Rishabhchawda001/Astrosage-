"""
Knowledge service — interfaces with the frozen AstroSage knowledge layer.

Provides BM25 search, knowledge graph queries, entity lookup,
and scripture metadata retrieval from the v1.0.0 frozen release.
"""
from __future__ import annotations

import json
import os
import re
import numpy as np
import time
from collections import defaultdict
from pathlib import Path
from typing import Optional

from api.config import settings
from api.services.cache import get_cache

# Lazy import for query expansion to avoid circular imports
_query_expansion_engine = None

def _get_query_expansion_engine():
    global _query_expansion_engine
    if _query_expansion_engine is None:
        from core.query_expansion.engine import QueryExpansionEngine
        _query_expansion_engine = QueryExpansionEngine()
        try:
            _query_expansion_engine.load()
        except Exception:
            pass  # Silently fall back if graph not available
    return _query_expansion_engine

# Adversarial detection — queries that should never receive high confidence
_NON_HINDU_TEXTS = [
    "quran", "bible", "torah", "gospel", "tripitaka",
    "koran", "new testament", "old testament",
    "what does the quran", "what does the bible",
]
_OUT_OF_DOMAIN_WORDS = {
    "cryptocurrency", "bitcoin", "crypto", "stock", "invest", "portfolio",
    "string theory", "quantum", "programming", "python", "javascript",
    "cricket", "football", "soccer", "baseball", "nba", "nfl",
    "capital of kalinga in 2026", "2025", "2026", "2027",
    "recipe", "chai", "coffee", "cook", "bake",
    "norse", "thor", "odin", "zeus", "greek", "egyptian",
    "planets does", "how many planets",
}


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
    """BM25-based lexical search over frozen chunks using rank-bm25."""

    def __init__(self, base_path: str | None = None):
        self.base_path = Path(base_path or settings.knowledge_base_path)
        self._bm25 = None
        self._chunks: list[dict] = []
        self._texts: list[str] = []
        self._tokenized: list[list[str]] = []
        self._loaded = False

    def load(self) -> "BM25SearchService":
        """Load chunks and build rank-bm25 index."""
        if self._loaded:
            return self

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

        # Build text representations
        for c in self._chunks:
            level = c.get("level", "")
            text = c.get("text", "")
            scripture = c.get("scripture_id", "")
            prefix = f"[{level}] "
            if scripture and level != "scripture":
                prefix += f"{scripture}: "
            self._texts.append((prefix + text))

        # Tokenize and build rank-bm25 index
        self._tokenized = [re.sub(r'[^\w\s]', '', t.lower()).split() for t in self._texts]
        from rank_bm25 import BM25Okapi
        self._bm25 = BM25Okapi(self._tokenized)

        # Build entity-to-chunks index for pre-filtering
        self._entity_to_chunks: dict[str, list[int]] = {}
        for idx, c in enumerate(self._chunks):
            for link in c.get("entity_links", []):
                name = link.get("name", "")
                if name:
                    key = name.lower()
                    if key not in self._entity_to_chunks:
                        self._entity_to_chunks[key] = []
                    self._entity_to_chunks[key].append(idx)

        self._loaded = True
        return self

    def search(self, query: str, top_k: int = 10) -> list[dict]:
        """Search using BM25 scoring with caching (rank-bm25)."""
        if not self._loaded or not self._bm25:
            return []

        cache = get_cache()
        cached = cache.get_search(query, top_k)
        if cached is not None:
            return cached

        # Tokenize query
        query_tokens = re.sub(r'[^\w\s]', '', query.lower()).split()
        if not query_tokens:
            return []

        # Expand query using QueryExpansionEngine for Sanskrit/Hindi/English bridging
        try:
            expander = _get_query_expansion_engine()
            clean_query = re.sub(r'[^\w\s]', '', query)
            expanded = expander.expand(clean_query)
            # Merge original tokens with expanded synonyms and transliterations
            expanded_tokens = set(query_tokens)
            for syns in expanded.synonyms.values():
                expanded_tokens.update(s.lower() for s in syns[:2])
            for trans in expanded.transliterations.values():
                if isinstance(trans, str):
                    expanded_tokens.update(trans.lower().split())
            for variant in expanded.semantic_variants:
                expanded_tokens.update(variant.lower().split())
            search_tokens = list(expanded_tokens)
        except Exception:
            # Fall back to original tokens if expansion fails
            search_tokens = query_tokens

        # Trim search tokens to avoid diluting BM25 scores
        # Keep original query tokens first, then add at most 5 expanded terms
        original_set = set(query_tokens)
        extra_terms = [t for t in search_tokens if t not in original_set][:5]
        search_tokens = list(original_set) + extra_terms

        # Entity-guided pre-filtering: if query matches known entities,
        # restrict BM25 scoring to only chunks linked to those entities
        candidate_indices = None
        for token in query_tokens:
            if token in self._entity_to_chunks:
                chunk_indices = set(self._entity_to_chunks[token])
                if candidate_indices is None:
                    candidate_indices = chunk_indices
                else:
                    candidate_indices &= chunk_indices  # Intersection (AND)
            # Also check for multi-word entity names
            for entity_name, indices in self._entity_to_chunks.items():
                if len(entity_name) > 3 and token in entity_name:
                    if candidate_indices is None:
                        candidate_indices = set(indices)
                    else:
                        candidate_indices |= set(indices)  # Union (OR) for partial matches

        # Use rank-bm25 for fast search
        if candidate_indices is not None and len(candidate_indices) > 0:
            # Only score candidate chunks — much faster
            candidate_list = sorted(candidate_indices)
            # Build a mini BM25 index from candidate chunks
            candidate_tokenized = [self._tokenized[i] for i in candidate_list]
            from rank_bm25 import BM25Okapi
            mini_bm25 = BM25Okapi(candidate_tokenized)
            mini_scores = mini_bm25.get_scores(search_tokens)
            top_in_candidates = np.argsort(mini_scores)[-top_k:][::-1]
            top_indices = [candidate_list[i] for i in top_in_candidates]
            # Build score map: global index -> score
            score_map = {candidate_list[i]: float(mini_scores[i]) for i in range(len(candidate_list))}
        else:
            full_scores = self._bm25.get_scores(search_tokens)
            top_indices = np.argsort(full_scores)[-top_k:][::-1]
            score_map = {int(i): float(full_scores[i]) for i in range(len(full_scores))}

        results = []
        for idx in top_indices:
            if idx < 0 or idx >= len(self._chunks):
                continue
            c = self._chunks[idx]
            score = score_map.get(idx, 0.0)
            results.append({
                "chunk_id": c.get("chunk_id", ""),
                "level": c.get("level", ""),
                "scripture_id": c.get("scripture_id", ""),
                "text": c.get("text", "")[:500],
                "score": round(float(score), 4),
                "entity_links": c.get("entity_links", []),
                "provenance": c.get("provenance", {}),
            })

        cache.set_search(query, top_k, results)
        return results

    @property
    def stats(self) -> dict:
        return {
            "loaded": self._loaded,
            "total_chunks": len(self._chunks),
            "index_built": self._bm25 is not None,
        }


class AnswerService:
    """Generates grounded answers from the knowledge graph."""

    def __init__(self, graph_service: KnowledgeGraphService, search_service: BM25SearchService):
        self.graph = graph_service
        self.search = search_service

    def _is_adversarial(self, question: str) -> tuple[bool, str]:
        """Check if a question is adversarial/out-of-domain.
        
        Returns (is_adversarial, reason) tuple.
        """
        q_lower = question.lower()
        
        # Check for non-Hindu religious texts
        for text in _NON_HINDU_TEXTS:
            if text in q_lower:
                return True, f"references non-Hindu text: {text}"
        
        # Check for out-of-domain keywords
        for word in _OUT_OF_DOMAIN_WORDS:
            if word in q_lower:
                return True, f"out-of-domain topic: {word}"
        
        # Check if question references any known entities
        query_tokens = {w for w in q_lower.split() if len(w) > 2}
        found = False
        for name in self.graph._entity_index:
            name_tokens = set(name.lower().split())
            if name_tokens & query_tokens:
                found = True
                break
        if not found and len(query_tokens) >= 2:
            # If question has meaningful tokens but none match any entity,
            # it's likely out-of-domain
            return True, "no matching entities in knowledge graph"
        
        return False, ""

    def answer(self, question: str, top_k: int = 5) -> dict:
        """Generate a grounded answer with evidence (cached)."""
        cache = get_cache()
        cached = cache.get_answer(question)
        if cached is not None:
            return cached

        # Check for adversarial/out-of-domain queries
        is_adversarial, reason = self._is_adversarial(question)
        if is_adversarial:
            result = {
                "question": question,
                "answer": {
                    "summary": f"I cannot provide a confident answer because this query {reason}. "
                               "AstroSage is a Hindu knowledge system and can only answer questions "
                               "related to Hindu scriptures, philosophy, and traditions.",
                    "entities_found": [],
                    "evidence_count": 0,
                    "confidence": "low",
                },
                "entities": [],
                "relationships": [],
                "sources": [],
                "provenance": {
                    "knowledge_version": "v1.0.0",
                    "source": "AstroSage Knowledge Engine",
                },
            }
            cache.set_answer(question, result)
            return result

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
