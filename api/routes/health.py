"""
Health check endpoint.

Returns system status, component health, and version information.
Used by Docker healthchecks, load balancers, and monitoring.
"""
from __future__ import annotations

import time
import json
import os
from datetime import datetime, timezone

from fastapi import APIRouter
from pydantic import BaseModel

from api.config import settings

router = APIRouter(tags=["health"])


class ComponentHealth(BaseModel):
    status: str
    latency_ms: float
    details: dict = {}


class HealthResponse(BaseModel):
    status: str
    version: str
    environment: str
    timestamp: str
    uptime_seconds: float
    components: dict


# Server start time for uptime calculation
_start_time = time.time()


@router.get("/api/v1/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint. Returns 200 if the API server is operational."""
    components: dict[str, ComponentHealth] = {}

    # Check knowledge base availability
    t0 = time.time()
    kb_path = settings.knowledge_base_path
    kb_available = os.path.isdir(kb_path)
    components["knowledge_base"] = ComponentHealth(
        status="ok" if kb_available else "unavailable",
        latency_ms=round((time.time() - t0) * 1000, 1),
        details={"path": kb_path} if kb_available else {},
    )

    # Check embeddings directory
    t0 = time.time()
    embed_path = os.path.join(kb_path, "embeddings")
    embed_available = os.path.isdir(embed_path)
    components["embeddings"] = ComponentHealth(
        status="ok" if embed_available else "missing",
        latency_ms=round((time.time() - t0) * 1000, 1),
    )

    # Check graph availability
    t0 = time.time()
    graph_path = os.path.join(kb_path, "graph", "graph.json")
    graph_available = os.path.isfile(graph_path)
    components["knowledge_graph"] = ComponentHealth(
        status="ok" if graph_available else "missing",
        latency_ms=round((time.time() - t0) * 1000, 1),
    )

    # Check BM25 index
    t0 = time.time()
    bm25_path = os.path.join(kb_path, "retrieval", "bm25_index.json")
    bm25_available = os.path.isfile(bm25_path)
    components["bm25_index"] = ComponentHealth(
        status="ok" if bm25_available else "missing",
        latency_ms=round((time.time() - t0) * 1000, 1),
    )

    overall_status = "ok" if all(
        c.status == "ok" for c in components.values()
    ) else "degraded"

    return HealthResponse(
        status=overall_status,
        version=settings.app_version,
        environment=settings.environment,
        timestamp=datetime.now(timezone.utc).isoformat(),
        uptime_seconds=round(time.time() - _start_time, 1),
        components={
            name: {
                "status": comp.status,
                "latency_ms": comp.latency_ms,
                "details": comp.details,
            }
            for name, comp in components.items()
        },
    )
