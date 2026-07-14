"""
Vector storage layer using Qdrant (production) or Chroma (dev).

Provides vector search, metadata filtering, and index management.
"""
from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Any, Optional

from ..models import Chunk, DocumentMetadata

logger = logging.getLogger(__name__)

COLLECTION_NAME = "astrosage_knowledge"


class VectorStore:
    """Vector store abstraction supporting Qdrant and Chroma backends."""

    def __init__(
        self,
        backend: str = "chroma",
        persist_dir: str = "./knowledge/indexes",
        qdrant_url: str = "http://localhost:6333",
    ):
        self.backend = backend
        self.persist_dir = Path(persist_dir)
        self.persist_dir.mkdir(parents=True, exist_ok=True)
        self.qdrant_url = qdrant_url
        self._client = None

    def connect(self):
        if self.backend == "qdrant":
            self._connect_qdrant()
        else:
            self._connect_chroma()

    def _connect_qdrant(self):
        from qdrant_client import QdrantClient
        from qdrant_client.models import Distance, VectorParams

        self._client = QdrantClient(url=self.qdrant_url)
        collections = [c.name for c in self._client.get_collections().collections]
        if COLLECTION_NAME not in collections:
            self._client.create_collection(
                collection_name=COLLECTION_NAME,
                vectors_config=VectorParams(size=1024, distance=Distance.COSINE),
            )
        logger.info(f"Connected to Qdrant: {self.qdrant_url}")

    def _connect_chroma(self):
        import chromadb

        self._client = chromadb.PersistentClient(path=str(self.persist_dir))
        self._collection = self._client.get_or_create_collection(
            name=COLLECTION_NAME,
            metadata={"hnsw:space": "cosine"},
        )
        logger.info(f"Connected to Chroma at {self.persist_dir}")

    def upsert_chunks(
        self,
        chunks: list[Chunk],
        dense_embeddings: Any,
        sparse_embeddings: Optional[Any] = None,
        metadata_list: Optional[list[dict]] = None,
    ):
        """Insert or update chunks with their embeddings."""
        if self.backend == "qdrant":
            self._upsert_qdrant(chunks, dense_embeddings)
        else:
            self._upsert_chroma(chunks, dense_embeddings, metadata_list)

    def _upsert_chroma(
        self,
        chunks: list[Chunk],
        embeddings: Any,
        metadata_list: Optional[list[dict]] = None,
    ):
        ids = [c.chunk_id for c in chunks]
        documents = [c.text for c in chunks]
        metadatas = metadata_list or [
            {
                "document_id": c.document_id,
                "page_numbers": json.dumps(c.page_numbers),
                "chapter": c.chapter,
                "section": c.section,
                "token_count": c.token_count,
                "sha256": c.sha256,
            }
            for c in chunks
        ]
        embedding_list = embeddings.tolist() if hasattr(embeddings, "tolist") else list(embeddings)

        self._collection.upsert(
            ids=ids,
            documents=documents,
            embeddings=embedding_list,
            metadatas=metadatas,
        )

    def _upsert_qdrant(self, chunks: list[Chunk], embeddings: Any):
        from qdrant_client.models import PointStruct

        points = []
        for i, chunk in enumerate(chunks):
            points.append(
                PointStruct(
                    id=hash(chunk.chunk_id) % (2**63),
                    vector=embeddings[i].tolist() if hasattr(embeddings[i], "tolist") else embeddings[i],
                    payload={
                        "chunk_id": chunk.chunk_id,
                        "document_id": chunk.document_id,
                        "text": chunk.text,
                        "page_numbers": chunk.page_numbers,
                        "chapter": chunk.chapter,
                        "section": chunk.section,
                        "token_count": chunk.token_count,
                        "sha256": chunk.sha256,
                    },
                )
            )

        self._client.upsert(
            collection_name=COLLECTION_NAME,
            points=points,
        )

    def search(
        self,
        query_embedding: Any,
        top_k: int = 10,
        filters: Optional[dict] = None,
    ) -> list[dict]:
        """Search for similar chunks."""
        if self.backend == "qdrant":
            return self._search_qdrant(query_embedding, top_k, filters)
        else:
            return self._search_chroma(query_embedding, top_k, filters)

    def _search_chroma(
        self,
        query_embedding: Any,
        top_k: int,
        filters: Optional[dict],
    ) -> list[dict]:
        query_emb = (
            query_embedding.tolist()
            if hasattr(query_embedding, "tolist")
            else list(query_embedding)
        )

        where = None
        if filters:
            where = {}
            if "document_id" in filters:
                where["document_id"] = filters["document_id"]
            if "chapter" in filters:
                where["chapter"] = filters["chapter"]

        kwargs = {
            "query_embeddings": [query_emb],
            "n_results": top_k,
        }
        if where:
            kwargs["where"] = where

        results = self._collection.query(**kwargs)

        hits = []
        if results and results["ids"][0]:
            for i, doc_id in enumerate(results["ids"][0]):
                hits.append(
                    {
                        "chunk_id": doc_id,
                        "text": results["documents"][0][i],
                        "score": 1.0 - results["distances"][0][i],
                        "metadata": results["metadatas"][0][i],
                    }
                )
        return hits

    def _search_qdrant(
        self,
        query_embedding: Any,
        top_k: int,
        filters: Optional[dict],
    ) -> list[dict]:
        from qdrant_client.models import Filter, FieldCondition, MatchValue

        query_vec = (
            query_embedding.tolist()
            if hasattr(query_embedding, "tolist")
            else list(query_embedding)
        )

        query_filter = None
        if filters:
            conditions = []
            if "document_id" in filters:
                conditions.append(
                    FieldCondition(
                        key="document_id",
                        match=MatchValue(value=filters["document_id"]),
                    )
                )
            if conditions:
                query_filter = Filter(must=conditions)

        results = self._client.query_points(
            collection_name=COLLECTION_NAME,
            query=query_vec,
            limit=top_k,
            query_filter=query_filter,
        )

        hits = []
        for point in results.points:
            hits.append(
                {
                    "chunk_id": point.payload.get("chunk_id", ""),
                    "text": point.payload.get("text", ""),
                    "score": point.score,
                    "metadata": point.payload,
                }
            )
        return hits

    def get_stats(self) -> dict:
        """Get index statistics."""
        if self.backend == "chroma":
            return {
                "total_chunks": self._collection.count(),
                "collection": COLLECTION_NAME,
                "backend": "chroma",
            }
        else:
            info = self._client.get_collection(COLLECTION_NAME)
            return {
                "total_chunks": info.points_count,
                "collection": COLLECTION_NAME,
                "backend": "qdrant",
            }

    def delete_document(self, document_id: str):
        """Remove all chunks for a document."""
        if self.backend == "chroma":
            self._collection.delete(where={"document_id": document_id})
        else:
            from qdrant_client.models import Filter, FieldCondition, MatchValue

            self._client.delete(
                collection_name=COLLECTION_NAME,
                points_selector=Filter(
                    must=[
                        FieldCondition(
                            key="document_id",
                            match=MatchValue(value=document_id),
                        )
                    ]
                ),
            )
