"""
Hybrid retrieval pipeline: BM25 + Vector + Cross-Encoder Reranking.

Evidence-based approach: hybrid search consistently outperforms
either method alone across benchmarks.
"""
from __future__ import annotations

import logging
import re
import time
from typing import Optional

from ..models import (
    Chunk,
    Citation,
    Confidence,
    DocumentMetadata,
    QueryRequest,
    QueryResponse,
    RetrievalResult,
)
from ..embedding.embedder import Embedder
from ..storage.vector_store import VectorStore

logger = logging.getLogger(__name__)


class BM25Index:
    """Lightweight BM25 index using rank_bm25."""

    def __init__(self):
        self._bm25 = None
        self._chunks: list[Chunk] = []

    def build(self, chunks: list[Chunk]):
        from rank_bm25 import BM25Okapi

        self._chunks = chunks
        tokenized = [self._tokenize(c.text) for c in chunks]
        self._bm25 = BM25Okapi(tokenized)
        logger.info(f"BM25 index built: {len(chunks)} chunks")

    def search(self, query: str, top_k: int = 20) -> list[tuple[Chunk, float]]:
        if self._bm25 is None:
            return []
        tokenized_query = self._tokenize(query)
        scores = self._bm25.get_scores(tokenized_query)
        top_indices = scores.argsort()[::-1][:top_k]
        return [(self._chunks[i], float(scores[i])) for i in top_indices if scores[i] > 0]

    def _tokenize(self, text: str) -> list[str]:
        # Basic tokenization: lowercase, split on whitespace and punctuation
        # Works for both Latin and Devanagari
        tokens = re.findall(r"\w+", text.lower())
        return tokens


class HybridRetriever:
    """
    Hybrid retrieval: vector search + BM25 + cross-encoder reranking.
    """

    def __init__(
        self,
        vector_store: VectorStore,
        embedder: Embedder,
        bm25_index: Optional[BM25Index] = None,
        use_reranker: bool = True,
    ):
        self.vector_store = vector_store
        self.embedder = embedder
        self.bm25_index = bm25_index or BM25Index()
        self.use_reranker = use_reranker
        self._reranker = None

    def _load_reranker(self):
        if self._reranker is not None:
            return
        if not self.use_reranker:
            return

        try:
            from sentence_transformers import CrossEncoder

            self._reranker = CrossEncoder(
                "cross-encoder/ms-marco-MiniLM-L-6-v2",
                max_length=512,
            )
            logger.info("Cross-encoder reranker loaded")
        except Exception as e:
            logger.warning(f"Reranker not available: {e}")
            self.use_reranker = False

    def search(self, request: QueryRequest) -> QueryResponse:
        """Execute hybrid search."""
        start = time.time()

        # Step 1: Vector search
        vector_results = self._vector_search(request.query, request.top_k * 2, request.filters)

        # Step 2: BM25 search
        bm25_results = self.bm25_index.search(request.query, request.top_k * 2)

        # Step 3: Score fusion (RRF - Reciprocal Rank Fusion)
        fused = self._reciprocal_rank_fusion(vector_results, bm25_results, k=60)

        # Step 4: Take top candidates
        candidates = fused[: request.top_k * 2]

        # Step 5: Rerank
        if self.use_reranker and len(candidates) > 0:
            candidates = self._rerank(request.query, candidates)

        # Step 6: Return top-k results
        results = []
        for rank, (chunk, score) in enumerate(candidates[: request.top_k]):
            confidence = self._score_to_confidence(score)
            results.append(
                RetrievalResult(
                    chunk=chunk,
                    score=score,
                    rank=rank + 1,
                    confidence=confidence,
                )
            )

        elapsed_ms = (time.time() - start) * 1000

        return QueryResponse(
            query=request.query,
            results=results,
            processing_time_ms=elapsed_ms,
        )

    def _vector_search(
        self,
        query: str,
        top_k: int,
        filters: Optional[dict],
    ) -> list[tuple[Chunk, float]]:
        query_emb = self.embedder.embed_query(query)
        dense_emb = query_emb.get("dense")
        if dense_emb is None:
            return []
        dense_emb = dense_emb[0] if len(dense_emb.shape) > 1 else dense_emb

        hits = self.vector_store.search(dense_emb, top_k, filters)

        results = []
        for hit in hits:
            chunk = Chunk(
                chunk_id=hit["chunk_id"],
                document_id=hit.get("metadata", {}).get("document_id", ""),
                text=hit["text"],
                page_numbers=hit.get("metadata", {}).get("page_numbers", []),
                chapter=hit.get("metadata", {}).get("chapter", ""),
                section=hit.get("metadata", {}).get("section", ""),
                token_count=hit.get("metadata", {}).get("token_count", 0),
            )
            results.append((chunk, hit["score"]))

        return results

    def _reciprocal_rank_fusion(
        self,
        vector_results: list[tuple[Chunk, float]],
        bm25_results: list[tuple[Chunk, float]],
        k: int = 60,
    ) -> list[tuple[Chunk, float]]:
        """Fuse results from multiple retrieval methods using RRF."""
        chunk_scores: dict[str, float] = {}
        chunk_map: dict[str, Chunk] = {}

        # Vector scores
        for rank, (chunk, score) in enumerate(vector_results):
            cid = chunk.chunk_id
            chunk_map[cid] = chunk
            chunk_scores[cid] = chunk_scores.get(cid, 0) + 1.0 / (k + rank + 1)

        # BM25 scores
        for rank, (chunk, score) in enumerate(bm25_results):
            cid = chunk.chunk_id
            chunk_map[cid] = chunk
            chunk_scores[cid] = chunk_scores.get(cid, 0) + 1.0 / (k + rank + 1)

        # Sort by fused score
        sorted_ids = sorted(chunk_scores.keys(), key=lambda x: chunk_scores[x], reverse=True)
        return [(chunk_map[cid], chunk_scores[cid]) for cid in sorted_ids]

    def _rerank(
        self, query: str, candidates: list[tuple[Chunk, float]]
    ) -> list[tuple[Chunk, float]]:
        """Rerank candidates using cross-encoder."""
        self._load_reranker()

        if self._reranker is None:
            return candidates

        pairs = [(query, c.text[:512]) for c, _ in candidates]
        scores = self._reranker.predict(pairs)

        reranked = [
            (candidates[i][0], float(scores[i]))
            for i in range(len(candidates))
        ]
        reranked.sort(key=lambda x: x[1], reverse=True)
        return reranked

    def _score_to_confidence(self, score: float) -> Confidence:
        if score > 0.8:
            return Confidence.HIGH
        elif score > 0.5:
            return Confidence.MEDIUM
        else:
            return Confidence.LOW

    def build_bm25_index(self, chunks: list[Chunk]):
        """Build the BM25 index from chunks."""
        self.bm25_index.build(chunks)
