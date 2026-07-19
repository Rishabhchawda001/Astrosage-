"""
Cache service — wraps LRU cache for development, designed for Redis in production.

Provides caching for search results, answers, and embeddings.
Exposes hit/miss statistics for monitoring.
"""
from __future__ import annotations

import hashlib
import json
import time
from typing import Any, Optional

from core.cache.lru_cache import RetrievalCache as LRUCache


class CacheService:
    """
    High-level cache service for API operations.

    Uses LRU in-memory cache for development.
    Designed for transparent upgrade to Redis.
    """

    def __init__(self):
        self._search_cache = LRUCache(max_size=500, default_ttl=300)  # 5 min TTL
        self._answer_cache = LRUCache(max_size=200, default_ttl=600)  # 10 min TTL
        self._embedding_cache = LRUCache(max_size=1000, default_ttl=3600)  # 1 hour TTL

    def _make_key(self, prefix: str, *args, **kwargs) -> str:
        """Generate a deterministic cache key."""
        key_parts = [str(a) for a in args]
        key_parts.extend(f"{k}={v}" for k, v in sorted(kwargs.items()))
        key_str = ":".join(key_parts)
        return f"{prefix}:{hashlib.md5(key_str.encode()).hexdigest()[:16]}"

    def get_search(self, query: str, top_k: int) -> Optional[list[dict]]:
        """Get cached search results."""
        key = self._make_key("search", query, top_k=top_k)
        return self._search_cache.get(key)

    def set_search(self, query: str, top_k: int, results: list[dict]) -> None:
        """Cache search results."""
        key = self._make_key("search", query, top_k=top_k)
        self._search_cache.set(key, results)

    def get_or_set_search(self, query: str, top_k: int, fn) -> list[dict]:
        """Get cached search results or compute and cache."""
        key = self._make_key("search", query, top_k=top_k)
        return self._search_cache.get_or_set(key, fn)

    def get_answer(self, question: str) -> Optional[dict]:
        """Get cached answer."""
        key = self._make_key("answer", question)
        return self._answer_cache.get(key)

    def set_answer(self, question: str, answer: dict) -> None:
        """Cache an answer."""
        key = self._make_key("answer", question)
        self._answer_cache.set(key, answer)

    def get_embedding(self, text: str) -> Optional[list[float]]:
        """Get cached embedding."""
        key = self._make_key("embed", text)
        return self._embedding_cache.get(key)

    def set_embedding(self, text: str, embedding: list[float]) -> None:
        """Cache an embedding."""
        key = self._make_key("embed", text)
        self._embedding_cache.set(key, embedding)

    def invalidate_search(self, query: str | None = None) -> None:
        """Invalidate search cache (all or specific query)."""
        if query:
            key = self._make_key("search", query, top_k=10)
            self._search_cache.invalidate(key)
        else:
            self._search_cache.clear()

    def invalidate_answer(self, question: str | None = None) -> None:
        """Invalidate answer cache."""
        if question:
            key = self._make_key("answer", question)
            self._answer_cache.invalidate(key)
        else:
            self._answer_cache.clear()

    @property
    def stats(self) -> dict:
        """Get cache statistics."""
        s = self._search_cache.stats()
        a = self._answer_cache.stats()
        e = self._embedding_cache.stats()
        total_hits = s["hits"] + a["hits"] + e["hits"]
        total_misses = s["misses"] + a["misses"] + e["misses"]
        total_requests = total_hits + total_misses
        return {
            "search_cache": s,
            "answer_cache": a,
            "embedding_cache": e,
            "total_hits": total_hits,
            "total_misses": total_misses,
            "total_requests": total_requests,
            "overall_hit_rate": round(total_hits / max(total_requests, 1), 4),
        }


# Module-level singleton
_cache_service: CacheService | None = None


def get_cache() -> CacheService:
    global _cache_service
    if _cache_service is None:
        _cache_service = CacheService()
    return _cache_service
