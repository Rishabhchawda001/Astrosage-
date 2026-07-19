"""Test search endpoints."""
import pytest
from httpx import ASGITransport, AsyncClient

from api.main import app


@pytest.fixture
async def client():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac


@pytest.mark.asyncio
async def test_search_returns_results(client):
    response = await client.post("/api/v1/search", json={
        "query": "Krishna",
        "top_k": 5,
    })
    assert response.status_code == 200
    data = response.json()
    assert "results" in data
    assert "latency_ms" in data
    assert data["query"] == "Krishna"


@pytest.mark.asyncio
async def test_search_get_variant(client):
    response = await client.get("/api/v1/search?q=Arjuna&top_k=3")
    assert response.status_code == 200
    data = response.json()
    assert len(data["results"]) <= 3


@pytest.mark.asyncio
async def test_search_empty_query(client):
    response = await client.post("/api/v1/search", json={
        "query": "",
        "top_k": 10,
    })
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_search_invalid_top_k(client):
    response = await client.post("/api/v1/search", json={
        "query": "Vishnu",
        "top_k": 0,
    })
    assert response.status_code == 422
