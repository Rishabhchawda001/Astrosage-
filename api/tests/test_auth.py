"""Test authentication endpoints."""
import pytest
from httpx import ASGITransport, AsyncClient

from api.main import app


@pytest.fixture
async def client():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac


@pytest.mark.asyncio
async def test_register_user(client):
    response = await client.post("/api/v1/auth/register", json={
        "username": "testuser",
        "password": "testpassword123",
    })
    assert response.status_code == 201
    data = response.json()
    assert data["username"] == "testuser"
    assert "api_key" in data


@pytest.mark.asyncio
async def test_register_duplicate_user(client):
    # First registration succeeds
    await client.post("/api/v1/auth/register", json={
        "username": "dupeuser",
        "password": "testpassword123",
    })
    # Second registration fails
    response = await client.post("/api/v1/auth/register", json={
        "username": "dupeuser",
        "password": "testpassword123",
    })
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_login_success(client):
    # Register first
    await client.post("/api/v1/auth/register", json={
        "username": "logintest",
        "password": "testpassword123",
    })
    # Login
    response = await client.post("/api/v1/auth/token", json={
        "username": "logintest",
        "password": "testpassword123",
    })
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert "refresh_token" in data
    assert data["token_type"] == "bearer"


@pytest.mark.asyncio
async def test_login_failure_wrong_password(client):
    response = await client.post("/api/v1/auth/token", json={
        "username": "nonexistent",
        "password": "wrongpassword",
    })
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_get_current_user(client):
    # Register and login
    await client.post("/api/v1/auth/register", json={
        "username": "currentuser",
        "password": "testpassword123",
    })
    login_resp = await client.post("/api/v1/auth/token", json={
        "username": "currentuser",
        "password": "testpassword123",
    })
    token = login_resp.json()["access_token"]

    # Get current user
    response = await client.get(
        "/api/v1/auth/me",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["username"] == "currentuser"


@pytest.mark.asyncio
async def test_auth_required_for_me(client):
    """Test that /me returns 401 without auth."""
    response = await client.get("/api/v1/auth/me")
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_register_invalid_username(client):
    response = await client.post("/api/v1/auth/register", json={
        "username": "ab",  # too short (min 3)
        "password": "testpassword123",
    })
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_register_short_password(client):
    response = await client.post("/api/v1/auth/register", json={
        "username": "validuser",
        "password": "short",  # too short (min 8)
    })
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_create_api_key(client):
    # Register and login
    await client.post("/api/v1/auth/register", json={
        "username": "apikeyuser",
        "password": "testpassword123",
    })
    login_resp = await client.post("/api/v1/auth/token", json={
        "username": "apikeyuser",
        "password": "testpassword123",
    })
    token = login_resp.json()["access_token"]

    # Create API key
    response = await client.post(
        "/api/v1/auth/api-keys",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["api_key"].startswith("ast-")
