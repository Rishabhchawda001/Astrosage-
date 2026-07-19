"""
Cache routes — stats and management for the API cache layer.
"""
from __future__ import annotations

from fastapi import APIRouter, Depends
from pydantic import BaseModel

from api.services.cache import get_cache

router = APIRouter(prefix="/api/v1/cache", tags=["cache"])


class CacheStats(BaseModel):
    search_cache: dict = {}
    answer_cache: dict = {}
    embedding_cache: dict = {}
    total_hits: int = 0
    total_misses: int = 0
    total_requests: int = 0
    overall_hit_rate: float = 0.0


@router.get("/stats", response_model=CacheStats)
async def cache_stats():
    """Get cache hit/miss statistics."""
    return get_cache().stats


@router.post("/clear")
async def clear_cache():
    """Clear all caches."""
    cache = get_cache()
    cache.invalidate_search()
    cache.invalidate_answer()
    return {"status": "cleared", "message": "All caches cleared"}
