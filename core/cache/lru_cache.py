"""
LRU Cache for AstroSage retrieval results.

Provides intelligent caching for:
1. Embedding computations
2. FAISS search results
3. Entity lookups
4. Answer generation results
"""
from __future__ import annotations
import hashlib
import json
import time
from collections import OrderedDict
from dataclasses import dataclass, field
from typing import Any, Optional
from pathlib import Path


@dataclass
class CacheEntry:
    """Single cache entry with metadata."""
    key: str
    value: Any
    created_at: float
    access_count: int = 0
    last_accessed: float = 0
    ttl_seconds: float = 3600  # 1 hour default


class RetrievalCache:
    """
    LRU cache for retrieval results with TTL support.
    
    Features:
    - Automatic eviction of least recently used entries
    - TTL-based expiration
    - Hit/miss statistics
    - Persistent storage option
    """
    
    def __init__(
        self,
        max_size: int = 1000,
        default_ttl: float = 3600,
        persist_path: Optional[str] = None,
    ):
        self.max_size = max_size
        self.default_ttl = default_ttl
        self.persist_path = Path(persist_path) if persist_path else None
        self._cache: OrderedDict[str, CacheEntry] = OrderedDict()
        self._hits = 0
        self._misses = 0
        
        if self.persist_path and self.persist_path.exists():
            self._load()
    
    def _make_key(self, *args, **kwargs) -> str:
        """Generate cache key from arguments."""
        key_parts = [str(a) for a in args]
        key_parts.extend(f"{k}={v}" for k, v in sorted(kwargs.items()))
        key_str = "|".join(key_parts)
        return hashlib.md5(key_str.encode()).hexdigest()
    
    def get(self, key: str) -> Optional[Any]:
        """Get value from cache."""
        if key in self._cache:
            entry = self._cache[key]
            
            # Check TTL
            if time.time() - entry.created_at > entry.ttl_seconds:
                del self._cache[key]
                self._misses += 1
                return None
            
            # Move to end (most recently used)
            self._cache.move_to_end(key)
            entry.access_count += 1
            entry.last_accessed = time.time()
            self._hits += 1
            return entry.value
        
        self._misses += 1
        return None
    
    def set(self, key: str, value: Any, ttl: Optional[float] = None) -> None:
        """Set value in cache."""
        if key in self._cache:
            # Update existing entry
            self._cache.move_to_end(key)
            self._cache[key].value = value
            self._cache[key].created_at = time.time()
            self._cache[key].access_count += 1
        else:
            # Add new entry
            if len(self._cache) >= self.max_size:
                # Remove oldest entry
                self._cache.popitem(last=False)
            
            self._cache[key] = CacheEntry(
                key=key,
                value=value,
                created_at=time.time(),
                ttl_seconds=ttl or self.default_ttl,
            )
    
    def get_or_set(
        self,
        key: str,
        factory,
        ttl: Optional[float] = None,
    ) -> Any:
        """Get from cache or compute and cache."""
        value = self.get(key)
        if value is not None:
            return value
        
        value = factory()
        self.set(key, value, ttl)
        return value
    
    def invalidate(self, key: str) -> bool:
        """Remove entry from cache."""
        if key in self._cache:
            del self._cache[key]
            return True
        return False
    
    def clear(self) -> None:
        """Clear all cache entries."""
        self._cache.clear()
        self._hits = 0
        self._misses = 0
    
    def stats(self) -> dict:
        """Get cache statistics."""
        total = self._hits + self._misses
        return {
            "size": len(self._cache),
            "max_size": self.max_size,
            "hits": self._hits,
            "misses": self._misses,
            "hit_rate": self._hits / max(total, 1),
            "total_requests": total,
        }
    
    def _save(self) -> None:
        """Persist cache to disk."""
        if not self.persist_path:
            return
        
        self.persist_path.parent.mkdir(parents=True, exist_ok=True)
        data = {
            "max_size": self.max_size,
            "default_ttl": self.default_ttl,
            "entries": {
                k: {
                    "key": v.key,
                    "value": v.value,
                    "created_at": v.created_at,
                    "access_count": v.access_count,
                    "last_accessed": v.last_accessed,
                    "ttl_seconds": v.ttl_seconds,
                }
                for k, v in self._cache.items()
            },
        }
        with open(self.persist_path, "w") as f:
            json.dump(data, f)
    
    def _load(self) -> None:
        """Load cache from disk."""
        if not self.persist_path or not self.persist_path.exists():
            return
        
        try:
            with open(self.persist_path) as f:
                data = json.load(f)
            
            self.max_size = data.get("max_size", self.max_size)
            self.default_ttl = data.get("default_ttl", self.default_ttl)
            
            for k, v in data.get("entries", {}).items():
                self._cache[k] = CacheEntry(
                    key=v["key"],
                    value=v["value"],
                    created_at=v["created_at"],
                    access_count=v.get("access_count", 0),
                    last_accessed=v.get("last_accessed", 0),
                    ttl_seconds=v.get("ttl_seconds", self.default_ttl),
                )
        except Exception:
            pass


# Global cache instance
_global_cache: Optional[RetrievalCache] = None


def get_cache(max_size: int = 1000, default_ttl: float = 3600) -> RetrievalCache:
    """Get or create global cache instance."""
    global _global_cache
    if _global_cache is None:
        _global_cache = RetrievalCache(max_size=max_size, default_ttl=default_ttl)
    return _global_cache
