"""Test health endpoint."""
import pytest
from httpx import ASGITransport, AsyncClient

from api.main import app


@pytest.fixture
async def client():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac


@pytest.mark.asyncio
async def test_health_returns_200(client):
    response = await client.get("/api/v1/health")
    assert response.status_code == 200


@pytest.mark.asyncio
async def test_health_returns_expected_fields(client):
    response = await client.get("/api/v1/health")
    data = response.json()
    assert data["status"] in ("ok", "degraded")
    assert "version" in data
    assert "environment" in data
    assert "timestamp" in data
    assert "components" in data


@pytest.mark.asyncio
async def test_health_components(client):
    response = await client.get("/api/v1/health")
    data = response.json()
    components = data["components"]
    assert "knowledge_base" in components
    assert "knowledge_graph" in components
    assert "bm25_index" in components


@pytest.mark.asyncio
async def test_root_redirects_to_docs(client):
    response = await client.get("/", follow_redirects=False)
    assert response.status_code in (200, 307, 308)


@pytest.mark.asyncio
async def test_openapi_schema(client):
    response = await client.get("/openapi.json")
    assert response.status_code == 200
    schema = response.json()
    assert schema["info"]["title"] == "AstroSage AI"
    assert "paths" in schema
    assert "/api/v1/health" in schema["paths"]
