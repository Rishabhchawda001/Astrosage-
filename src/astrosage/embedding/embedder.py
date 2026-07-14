"""
Embedding pipeline using BGE-M3.

Supports dense, sparse (BM25-like), and ColBERT embeddings.
All models run locally — no paid APIs.
"""
from __future__ import annotations

import logging
from typing import Optional

import numpy as np

logger = logging.getLogger(__name__)


class Embedder:
    """
    Multilingual embedding engine using BGE-M3.

    Generates:
    - Dense embeddings (768-dim) for vector search
    - Sparse embeddings (BM25-like) for hybrid search
    - ColBERT late-interaction embeddings for reranking
    """

    def __init__(
        self,
        model_name: str = "BAAI/bge-m3",
        device: str = "cpu",
        use_dense: bool = True,
        use_sparse: bool = True,
        use_colbert: bool = False,
    ):
        self.model_name = model_name
        self.device = device
        self.use_dense = use_dense
        self.use_sparse = use_sparse
        self.use_colbert = use_colbert
        self._model = None

    def _load_model(self):
        if self._model is not None:
            return

        logger.info(f"Loading embedding model: {self.model_name} on {self.device}")
        try:
            from FlagEmbedding import BGEM3FlagModel

            self._model = BGEM3FlagModel(
                self.model_name,
                use_fp16=False if self.device == "cpu" else True,
            )
            logger.info(f"Model loaded: {self.model_name}")
        except ImportError:
            logger.error("FlagEmbedding not installed. Using sentence-transformers fallback.")
            self._load_fallback()

    def _load_fallback(self):
        """Fallback to sentence-transformers with BGE model."""
        from sentence_transformers import SentenceTransformer

        logger.info(f"Loading fallback model: {self.model_name}")
        self._model = SentenceTransformer(self.model_name, device=self.device)
        logger.info("Fallback model loaded")

    def embed_texts(self, texts: list[str], batch_size: int = 32) -> dict:
        """
        Generate embeddings for a list of texts.

        Returns:
            {
                "dense": np.ndarray (N x 768),
                "sparse": list of dicts (token_id -> weight),
                "colbert": list of np.ndarray (N x seq_len x dim),
            }
        """
        self._load_model()

        results = {"dense": None, "sparse": None, "colbert": None}

        if isinstance(self._model, type) and hasattr(self._model, "encode"):
            # Fallback mode — sentence-transformers
            dense = self._model.encode(
                texts, batch_size=batch_size, show_progress_bar=True
            )
            results["dense"] = dense
            return results

        # BGEM3FlagModel mode
        output = self._model.encode(
            texts,
            batch_size=batch_size,
            max_length=8192,
            return_dense=self.use_dense,
            return_sparse=self.use_sparse,
            return_colbert_vecs=self.use_colbert,
        )

        if self.use_dense:
            results["dense"] = output.get("dense_vecs")
        if self.use_sparse:
            results["sparse"] = output.get("lexical_weights")
        if self.use_colbert:
            results["colbert"] = output.get("colbert_vecs")

        return results

    def embed_query(self, query: str) -> dict:
        """Embed a single query (returns same format as embed_texts)."""
        return self.embed_texts([query], batch_size=1)

    def embed_documents(
        self,
        texts: list[str],
        batch_size: int = 32,
    ) -> dict:
        """Embed document chunks."""
        return self.embed_texts(texts, batch_size=batch_size)

    @property
    def embedding_dim(self) -> int:
        return 1024  # BGE-M3 dense dimension
