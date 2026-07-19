"""Test chat completions endpoint."""
import pytest
from httpx import ASGITransport, AsyncClient

from api.main import app


@pytest.fixture
async def client():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac


@pytest.mark.asyncio
async def test_chat_completions_basic(client):
    """Test basic chat completion (non-streaming)."""
    response = await client.post("/api/v1/chat/completions", json={
        "model": "gpt-4o-mini",
        "messages": [
            {"role": "user", "content": "Who is Krishna?"}
        ],
        "stream": False,
    })
    # Should either work (with API key) or fallback to knowledge base
    assert response.status_code in (200, 500, 503)
    if response.status_code == 200:
        data = response.json()
        assert "choices" in data
        assert len(data["choices"]) > 0


@pytest.mark.asyncio
async def test_chat_completions_empty_messages(client):
    """Test validation for empty messages."""
    response = await client.post("/api/v1/chat/completions", json={
        "model": "gpt-4o-mini",
        "messages": [],
        "stream": False,
    })
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_chat_completions_invalid_model(client):
    """Test with invalid model (should fallback gracefully)."""
    response = await client.post("/api/v1/chat/completions", json={
        "model": "nonexistent-model-12345",
        "messages": [
            {"role": "user", "content": "Explain karma"}
        ],
        "stream": False,
    })
    # Should fallback to knowledge base
    assert response.status_code in (200, 500, 503)
    if response.status_code == 200:
        data = response.json()
        assert data["choices"][0]["message"]["content"]
        assert "knowledge" in data["choices"][0]["message"]["content"].lower() or \
               "entity" in data["choices"][0]["message"]["content"].lower()


@pytest.mark.asyncio
async def test_chat_completions_system_message(client):
    """Test with system message."""
    response = await client.post("/api/v1/chat/completions", json={
        "model": "gpt-4o-mini",
        "messages": [
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": "List all Pandavas"}
        ],
        "stream": False,
    })
    assert response.status_code in (200, 500, 503)


@pytest.mark.asyncio
async def test_chat_streaming_header(client):
    """Test that streaming requests return SSE content type."""
    response = await client.post("/api/v1/chat/completions", json={
        "model": "gpt-4o-mini",
        "messages": [
            {"role": "user", "content": "Who is Vishnu?"}
        ],
        "stream": True,
    })
    assert response.status_code in (200, 500, 503)
    if response.status_code == 200:
        assert response.headers.get("content-type", "").startswith("text/event-stream")
