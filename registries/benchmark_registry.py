"""Benchmark Registry — Tracks all benchmarks run by AstroSage."""
from __future__ import annotations

import json
import uuid
from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional


@dataclass
class BenchmarkEntry:
    bench_id: str = ""
    name: str = ""
    category: str = ""  # ocr, embedding, chunking, retrieval, recovery, verification, etc.
    description: str = ""
    results: dict = field(default_factory=dict)
    metadata: dict = field(default_factory=dict)
    pipeline_version: str = ""
    dataset_version: str = ""
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

    def __post_init__(self):
        if not self.bench_id:
            self.bench_id = f"BENCH-{uuid.uuid4().hex[:8]}"


class BenchmarkRegistry:
    """Registry of all benchmarks and their results."""

    def __init__(self, registry_dir: str = "registries"):
        self.registry_dir = Path(registry_dir)
        self.registry_dir.mkdir(parents=True, exist_ok=True)
        self._entries: dict[str, BenchmarkEntry] = {}

    def register(self, entry: BenchmarkEntry) -> str:
        if not entry.bench_id:
            entry.bench_id = f"BENCH-{uuid.uuid4().hex[:8]}"
        self._entries[entry.bench_id] = entry
        return entry.bench_id

    def get(self, bench_id: str) -> Optional[BenchmarkEntry]:
        return self._entries.get(bench_id)

    def find_by_category(self, category: str) -> list[BenchmarkEntry]:
        return [e for e in self._entries.values() if e.category == category]

    def find_by_name(self, name: str) -> list[BenchmarkEntry]:
        return [e for e in self._entries.values() if name.lower() in e.name.lower()]

    def get_latest(self, category: str) -> Optional[BenchmarkEntry]:
        entries = self.find_by_category(category)
        if not entries:
            return None
        return max(entries, key=lambda e: e.created_at)

    def list_all(self) -> list[BenchmarkEntry]:
        return list(self._entries.values())

    def save(self):
        data = {eid: asdict(e) for eid, e in self._entries.items()}
        with open(self.registry_dir / "benchmarks.json", "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

    def load(self):
        path = self.registry_dir / "benchmarks.json"
        if not path.exists():
            return
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        for eid, edata in data.items():
            self._entries[eid] = BenchmarkEntry(**edata)

    def summary(self) -> dict:
        cat_counts = {}
        for e in self._entries.values():
            cat = e.category or "uncategorized"
            cat_counts[cat] = cat_counts.get(cat, 0) + 1
        return {"total": len(self._entries), "by_category": cat_counts}
