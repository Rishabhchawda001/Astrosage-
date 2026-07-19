"""
Knowledge Graph routes — entity lookup, relationships, scripture metadata, path finding.
"""
from __future__ import annotations

from fastapi import APIRouter, Query
from pydantic import BaseModel, Field

from api.services import get_graph_service

router = APIRouter(prefix="/api/v1/graph", tags=["knowledge graph"])


class EntitySummary(BaseModel):
    name: str
    type: str
    guid: str
    total_mentions: int = 0


class Relationship(BaseModel):
    type: str
    direction: str  # outgoing or incoming
    target_guid: str
    target_name: str
    target_type: str = ""
    confidence: int = 0


class EntityDetail(BaseModel):
    guid: str
    name: str
    type: str
    total_mentions: int
    sources: list[str] = []
    relationships: list[Relationship] = []


class ScriptureSummary(BaseModel):
    id: str
    name: str
    type: str = "Scripture"
    verses: int = 0
    coverage: float = 0
    source: str = ""
    certification: str = ""


class PathResult(BaseModel):
    path: list[str] = []
    path_names: list[str] = []
    depth: int = 0


class GraphStats(BaseModel):
    entities: int
    scriptures: int
    edges: int
    edge_types: int
    node_types: int


@router.get("/entity/{name}", response_model=EntityDetail)
async def get_entity(name: str):
    """Get details and relationships for a knowledge graph entity."""
    graph = get_graph_service()
    entity = graph.find_entity(name)
    if not entity:
        from api.exceptions import NotFoundError
        raise NotFoundError(message=f"Entity '{name}' not found in knowledge graph")

    guid = entity.get("GUID", "")
    relationships = graph.get_entity_relationships(guid)

    return EntityDetail(
        guid=guid,
        name=entity.get("name", ""),
        type=entity.get("type", ""),
        total_mentions=entity.get("total_mentions", 0),
        sources=entity.get("sources", []),
        relationships=[Relationship(**r) for r in relationships],
    )


@router.get("/search", response_model=list[EntitySummary])
async def search_entities(
    q: str = Query(..., min_length=1, max_length=100),
    limit: int = Query(10, ge=1, le=50),
):
    """Search entities by name."""
    graph = get_graph_service()
    results = graph.search_entities(q, limit=limit)
    return [EntitySummary(**r) for r in results]


@router.get("/scripture/{scripture_id}", response_model=ScriptureSummary)
async def get_scripture(scripture_id: str):
    """Get metadata for a scripture."""
    graph = get_graph_service()
    s = graph.get_scripture(scripture_id)
    if not s:
        from api.exceptions import NotFoundError
        raise NotFoundError(message=f"Scripture '{scripture_id}' not found")
    return ScriptureSummary(**{
        "id": s.get("id", ""),
        "name": s.get("canonical_name", s.get("id", "")),
        "type": "Scripture",
        "verses": s.get("total_verses", 0),
        "coverage": s.get("coverage", 0),
        "source": s.get("primary_source", ""),
        "certification": s.get("certification", ""),
    })


@router.get("/scriptures", response_model=list[ScriptureSummary])
async def list_scriptures():
    """List all indexed scriptures."""
    graph = get_graph_service()
    return graph.list_scriptures()


@router.get("/path", response_model=PathResult)
async def find_path(
    source: str = Query(..., description="Source entity name"),
    target: str = Query(..., description="Target entity name"),
    max_depth: int = Query(3, ge=1, le=6),
):
    """Find a path between two entities in the knowledge graph."""
    graph = get_graph_service()
    src_entity = graph.find_entity(source)
    tgt_entity = graph.find_entity(target)

    if not src_entity or not tgt_entity:
        from api.exceptions import NotFoundError
        raise NotFoundError(
            message=f"Entity not found: '{source if not src_entity else target}'"
        )

    path = graph.find_path(src_entity["GUID"], tgt_entity["GUID"], max_depth=max_depth)
    if not path:
        return PathResult(path=[], path_names=[], depth=0)

    path_names = []
    for guid in path:
        entity = graph.get_entity_detail(guid)
        path_names.append(entity.get("name", guid) if entity else guid)

    return PathResult(path=path, path_names=path_names, depth=len(path) - 1)


@router.get("/stats", response_model=GraphStats)
async def graph_stats():
    """Get knowledge graph statistics."""
    graph = get_graph_service()
    return GraphStats(**graph.stats)
