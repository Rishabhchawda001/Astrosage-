"""Test knowledge graph endpoints."""
import pytest
from httpx import ASGITransport, AsyncClient

from api.main import app


@pytest.fixture
async def client():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac


@pytest.mark.asyncio
async def test_get_entity(client):
    response = await client.get("/api/v1/graph/entity/Vishnu")
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "Vishnu"
    assert data["type"] in ("Deity", "Person", "Concept", "Place")
    assert "relationships" in data


@pytest.mark.asyncio
async def test_get_entity_not_found(client):
    response = await client.get("/api/v1/graph/entity/NonExistentEntity12345")
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_search_entities(client):
    response = await client.get("/api/v1/graph/search?q=Krishna")
    assert response.status_code == 200
    data = response.json()
    assert len(data) > 0
    assert any("Krishna" in e["name"] for e in data)


@pytest.mark.asyncio
async def test_list_scriptures(client):
    response = await client.get("/api/v1/graph/scriptures")
    assert response.status_code == 200
    data = response.json()
    assert len(data) > 0
    assert data[0]["type"] == "Scripture"


@pytest.mark.asyncio
async def test_graph_stats(client):
    response = await client.get("/api/v1/graph/stats")
    assert response.status_code == 200
    data = response.json()
    assert data["entities"] > 0
    assert data["edges"] > 0
    assert data["scriptures"] > 0
