"""Tests for the Retrieval Cache."""
import sys
import time
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))


class TestRetrievalCache:
    def test_imports(self):
        from core.cache.lru_cache import RetrievalCache
        assert RetrievalCache is not None

    def test_init(self):
        from core.cache.lru_cache import RetrievalCache
        cache = RetrievalCache(max_size=10)
        assert cache.max_size == 10

    def test_set_get(self):
        from core.cache.lru_cache import RetrievalCache
        cache = RetrievalCache()
        cache.set("key1", {"result": "test"})
        result = cache.get("key1")
        assert result == {"result": "test"}

    def test_miss(self):
        from core.cache.lru_cache import RetrievalCache
        cache = RetrievalCache()
        result = cache.get("nonexistent")
        assert result is None

    def test_lru_eviction(self):
        from core.cache.lru_cache import RetrievalCache
        cache = RetrievalCache(max_size=3)
        cache.set("k1", "v1")
        cache.set("k2", "v2")
        cache.set("k3", "v3")
        cache.set("k4", "v4")  # Should evict k1
        assert cache.get("k1") is None
        assert cache.get("k2") == "v2"

    def test_ttl_expiration(self):
        from core.cache.lru_cache import RetrievalCache
        cache = RetrievalCache(default_ttl=0.01)  # 10ms
        cache.set("key1", "value1")
        time.sleep(0.02)
        assert cache.get("key1") is None

    def test_get_or_set(self):
        from core.cache.lru_cache import RetrievalCache
        cache = RetrievalCache()
        call_count = [0]
        def factory():
            call_count[0] += 1
            return "computed"
        result = cache.get_or_set("key1", factory)
        assert result == "computed"
        assert call_count[0] == 1
        # Second call should use cache
        result2 = cache.get_or_set("key1", factory)
        assert result2 == "computed"
        assert call_count[0] == 1

    def test_invalidate(self):
        from core.cache.lru_cache import RetrievalCache
        cache = RetrievalCache()
        cache.set("key1", "value1")
        assert cache.invalidate("key1") is True
        assert cache.get("key1") is None
        assert cache.invalidate("key1") is False

    def test_clear(self):
        from core.cache.lru_cache import RetrievalCache
        cache = RetrievalCache()
        cache.set("k1", "v1")
        cache.set("k2", "v2")
        cache.clear()
        assert cache.get("k1") is None
        assert cache.get("k2") is None

    def test_stats(self):
        from core.cache.lru_cache import RetrievalCache
        cache = RetrievalCache()
        cache.set("k1", "v1")
        cache.get("k1")
        cache.get("k2")
        stats = cache.stats()
        assert stats["hits"] == 1
        assert stats["misses"] == 1
        assert stats["size"] == 1

    def test_global_cache(self):
        from core.cache.lru_cache import get_cache
        cache1 = get_cache()
        cache2 = get_cache()
        assert cache1 is cache2

    def test_factory_function(self):
        from core.cache.lru_cache import RetrievalCache
        cache = RetrievalCache()
        result = cache.get_or_set("key", lambda: 42)
        assert result == 42
