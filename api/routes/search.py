"""
Search routes — BM25 lexical search over the frozen knowledge corpus.
"""
from __future__ import annotations

import time

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel, Field

from api.services import get_search_service
from api.services.knowledge import BM25SearchService

router = APIRouter(prefix="/api/v1/search", tags=["search"])


class SearchRequest(BaseModel):
    query: str = Field(..., min_length=1, max_length=500, description="Search query")
    top_k: int = Field(default=10, ge=1, le=100, description="Number of results")
    level: str | None = Field(default=None, description="Filter by chunk level")
    scripture: str | None = Field(default=None, description="Filter by scripture ID")


class SearchResult(BaseModel):
    chunk_id: str
    level: str
    scripture_id: str
    text: str
    score: float
    entity_links: list[dict] = []
    provenance: dict = {}


class SearchResponse(BaseModel):
    query: str
    results: list[SearchResult]
    total_results: int
    latency_ms: float


@router.post("", response_model=SearchResponse)
async def search(body: SearchRequest):
    """Search the knowledge base using BM25 lexical search."""
    search_service = get_search_service()
    start = time.time()

    results = search_service.search(body.query, top_k=body.top_k)

    latency = round((time.time() - start) * 1000, 1)

    # Apply filters (post-filter)
    if body.level:
        results = [r for r in results if r["level"] == body.level]
    if body.scripture:
        results = [r for r in results if r["scripture_id"].lower() == body.scripture.lower()]

    return SearchResponse(
        query=body.query,
        results=[SearchResult(**r) for r in results],
        total_results=len(results),
        latency_ms=latency,
    )


@router.get("", response_model=SearchResponse)
async def search_get(
    q: str = Query(..., min_length=1, max_length=500, description="Search query"),
    top_k: int = Query(10, ge=1, le=100),
    level: str | None = Query(None),
    scripture: str | None = Query(None),
):
    """Search the knowledge base (GET variant for simple queries)."""
    return await search(SearchRequest(query=q, top_k=top_k, level=level, scripture=scripture))
