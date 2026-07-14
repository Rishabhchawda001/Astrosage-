"""Source Cache — Cache discovery results to avoid redundant API calls."""
from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional


@dataclass
class CacheEntry:
    cache_key: str = ""
    query: str = ""
    connector: str = ""
    results: list[dict[str, Any]] = field(default_factory=list)
    cached_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    hit_count: int = 0


class SourceCache:
    def __init__(self, cache_dir: str = "knowledge/cache/sources"):
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self._cache: dict[str, CacheEntry] = {}
        self._ttl_hours: int = 24

    def _make_key(self, query: str, connector: str) -> str:
        raw = f"{query}:{connector}"
        return hashlib.sha256(raw.encode()).hexdigest()[:16]

    def get(self, query: str, connector: str = "") -> Optional[CacheEntry]:
        key = self._make_key(query, connector)
        entry = self._cache.get(key)
        if entry:
            entry.hit_count += 1
            return entry
        return None

    def put(self, query: str, connector: str, results: list[dict]) -> CacheEntry:
        key = self._make_key(query, connector)
        entry = CacheEntry(cache_key=key, query=query, connector=connector, results=results)
        self._cache[key] = entry
        return entry

    def invalidate(self, query: str, connector: str = "") -> bool:
        key = self._make_key(query, connector)
        return self._cache.pop(key, None) is not None

    def count(self) -> int:
        return len(self._cache)

    def total_hits(self) -> int:
        return sum(e.hit_count for e in self._cache.values())

    def summary(self) -> dict:
        return {"total_entries": self.count(), "total_hits": self.total_hits()}
