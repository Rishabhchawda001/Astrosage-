"""Test answer generation endpoints."""
import pytest
from httpx import ASGITransport, AsyncClient

from api.main import app


@pytest.fixture
async def client():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac


@pytest.mark.asyncio
async def test_answer_question(client):
    response = await client.post("/api/v1/answer", json={
        "question": "Who is Vishnu?",
        "top_k": 5,
    })
    assert response.status_code == 200
    data = response.json()
    assert data["question"] == "Who is Vishnu?"
    assert "answer" in data
    assert "sources" in data
    assert "latency_ms" in data


@pytest.mark.asyncio
async def test_answer_empty_question(client):
    response = await client.post("/api/v1/answer", json={
        "question": "",
        "top_k": 5,
    })
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_answer_includes_provenance(client):
    response = await client.post("/api/v1/answer", json={
        "question": "Explain karma",
        "top_k": 3,
    })
    data = response.json()
    assert "provenance" in data
    assert data["provenance"]["knowledge_version"] == "v1.0.0"
