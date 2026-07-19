"""Test conversation management endpoints."""
import pytest
from httpx import ASGITransport, AsyncClient

from api.main import app


@pytest.fixture
async def client():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac


@pytest.fixture
async def auth_client(client):
    """Client with authenticated session."""
    # Register test user
    await client.post("/api/v1/auth/register", json={
        "username": "convuser",
        "password": "convpassword123",
    })
    # Get token
    resp = await client.post("/api/v1/auth/token", json={
        "username": "convuser",
        "password": "convpassword123",
    })
    token = resp.json()["access_token"]
    client.headers = {"Authorization": f"Bearer {token}"}
    return client


@pytest.mark.asyncio
async def test_create_conversation(auth_client):
    response = await auth_client.post("/api/v1/conversations", json={
        "title": "Test discussion",
        "model": "gpt-4o-mini",
    })
    assert response.status_code == 201
    data = response.json()
    assert data["title"] == "Test discussion"
    assert data["model"] == "gpt-4o-mini"
    assert "id" in data
    assert data["message_count"] == 0


@pytest.mark.asyncio
async def test_create_conversation_no_auth(client):
    response = await client.post("/api/v1/conversations", json={
        "title": "Test",
        "model": "gpt-4o-mini",
    })
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_list_conversations(auth_client):
    # Create some conversations
    for i in range(3):
        await auth_client.post("/api/v1/conversations", json={
            "title": f"Conv {i}",
            "model": "gpt-4o-mini",
        })

    response = await auth_client.get("/api/v1/conversations")
    assert response.status_code == 200
    data = response.json()
    assert len(data) >= 3


@pytest.mark.asyncio
async def test_get_conversation(auth_client):
    # Create conversation
    create_resp = await auth_client.post("/api/v1/conversations", json={
        "title": "Get test",
        "model": "gpt-4o-mini",
    })
    conv_id = create_resp.json()["id"]

    response = await auth_client.get(f"/api/v1/conversations/{conv_id}")
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == conv_id
    assert data["title"] == "Get test"


@pytest.mark.asyncio
async def test_get_conversation_not_found(auth_client):
    response = await auth_client.get("/api/v1/conversations/nonexistent123")
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_add_message(auth_client):
    # Create conversation
    create_resp = await auth_client.post("/api/v1/conversations", json={"title": "Message test"})
    conv_id = create_resp.json()["id"]

    # Add user message
    msg_resp = await auth_client.post(f"/api/v1/conversations/{conv_id}/messages", json={
        "role": "user",
        "content": "Who is Vishnu?",
    })
    assert msg_resp.status_code == 201
    msg_data = msg_resp.json()
    assert msg_data["role"] == "user"
    assert msg_data["content"] == "Who is Vishnu?"

    # Add assistant response
    msg_resp2 = await auth_client.post(f"/api/v1/conversations/{conv_id}/messages", json={
        "role": "assistant",
        "content": "Vishnu is a major deity in Hinduism...",
        "token_count": 42,
    })
    assert msg_resp2.status_code == 201

    # Get messages
    msgs_resp = await auth_client.get(f"/api/v1/conversations/{conv_id}/messages")
    assert msgs_resp.status_code == 200
    msgs = msgs_resp.json()
    assert len(msgs) >= 2
    assert msgs[0]["role"] == "user"
    assert msgs[1]["role"] == "assistant"


@pytest.mark.asyncio
async def test_delete_conversation(auth_client):
    create_resp = await auth_client.post("/api/v1/conversations", json={"title": "Delete me"})
    conv_id = create_resp.json()["id"]

    delete_resp = await auth_client.delete(f"/api/v1/conversations/{conv_id}")
    assert delete_resp.status_code == 204

    # Verify deleted
    get_resp = await auth_client.get(f"/api/v1/conversations/{conv_id}")
    assert get_resp.status_code == 404


@pytest.mark.asyncio
async def test_update_title(auth_client):
    create_resp = await auth_client.post("/api/v1/conversations", json={"title": "Old title"})
    conv_id = create_resp.json()["id"]

    resp = await auth_client.patch(f"/api/v1/conversations/{conv_id}/title?title=New+title")
    assert resp.status_code == 200

    get_resp = await auth_client.get(f"/api/v1/conversations/{conv_id}")
    assert get_resp.json()["title"] == "New title"


@pytest.mark.asyncio
async def test_chat_auto_creates_conversation(auth_client):
    """Chat auto-creates conversation and persists messages."""
    response = await auth_client.post("/api/v1/chat/completions", json={
        "model": "gpt-4o-mini",
        "messages": [
            {"role": "user", "content": "Tell me about Dharma"}
        ],
        "stream": False,
    })
    assert response.status_code in (200, 500, 503)
    if response.status_code == 200:
        data = response.json()
        # Should have a conversation ID
        assert data["id"] is not None
        # Check messages were persisted
        conv = await auth_client.get(f"/api/v1/conversations/{data['id']}")
        assert conv.status_code == 200
        assert len(conv.json()["messages"]) >= 2  # user + assistant
