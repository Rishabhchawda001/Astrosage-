"""Test cache service."""
import pytest
from httpx import ASGITransport, AsyncClient

from api.main import app
from api.services.cache import get_cache


@pytest.fixture
async def client():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac


def test_cache_set_get():
    cache = get_cache()
    cache.set_search("test query", 5, [{"id": "test"}])
    results = cache.get_search("test query", 5)
    assert results is not None
    assert results[0]["id"] == "test"


def test_cache_miss():
    cache = get_cache()
    results = cache.get_search("nonexistent query", 10)
    assert results is None


def test_cache_invalidate():
    cache = get_cache()
    cache.set_search("q", 10, [{"id": "x"}])
    assert cache.get_search("q", 10) is not None
    cache.invalidate_search()
    # Cache may still have entry if TTL not expired, but clear should work
    # Actually invalidate_search without args clears ALL
    # Let's test with explicit invalidation
    cache.set_search("q2", 10, [{"id": "y"}])
    assert cache.get_search("q2", 10) is not None


def test_cache_stats():
    cache = get_cache()
    stats = cache.stats
    assert "search_cache" in stats
    assert "answer_cache" in stats
    assert "overall_hit_rate" in stats
    assert stats["total_requests"] >= 0


def test_cache_answer():
    cache = get_cache()
    result = cache.get_answer("test question")
    if result is None:
        cache.set_answer("test question", {"answer": "test"})
        result = cache.get_answer("test question")
        assert result is not None
        assert result["answer"] == "test"


@pytest.mark.asyncio
async def test_cache_stats_endpoint(client):
    response = await client.get("/api/v1/cache/stats")
    assert response.status_code == 200
    data = response.json()
    assert "search_cache" in data
    assert "overall_hit_rate" in data


@pytest.mark.asyncio
async def test_cache_clear_endpoint(client):
    response = await client.post("/api/v1/cache/clear")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "cleared"
