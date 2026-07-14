"""Research Registry — Stores research discoveries, papers, and technology watch."""
from __future__ import annotations

import json
import uuid
from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional


@dataclass
class ResearchEntry:
    entry_id: str = ""
    title: str = ""
    category: str = ""  # github_discovery, arxiv, benchmark, research_note, tech_watch, security_watch, release_watch
    url: str = ""
    summary: str = ""
    tags: list[str] = field(default_factory=list)
    relevance_score: float = 0.0
    action_required: bool = False
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

    def __post_init__(self):
        if not self.entry_id:
            self.entry_id = f"RES-{uuid.uuid4().hex[:8]}"


class ResearchRegistry:
    """Registry of all research discoveries and technology watch items."""

    def __init__(self, registry_dir: str = "registries"):
        self.registry_dir = Path(registry_dir)
        self.registry_dir.mkdir(parents=True, exist_ok=True)
        self._entries: dict[str, ResearchEntry] = {}

    def register(self, entry: ResearchEntry) -> str:
        if not entry.entry_id:
            entry.entry_id = f"RES-{uuid.uuid4().hex[:8]}"
        self._entries[entry.entry_id] = entry
        return entry.entry_id

    def get(self, entry_id: str) -> Optional[ResearchEntry]:
        return self._entries.get(entry_id)

    def find_by_category(self, category: str) -> list[ResearchEntry]:
        return [e for e in self._entries.values() if e.category == category]

    def find_by_tags(self, tags: list[str]) -> list[ResearchEntry]:
        tag_set = set(tags)
        return [e for e in self._entries.values() if tag_set & set(e.tags)]

    def list_all(self) -> list[ResearchEntry]:
        return list(self._entries.values())

    def save(self):
        data = {eid: asdict(e) for eid, e in self._entries.items()}
        with open(self.registry_dir / "research.json", "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

    def load(self):
        path = self.registry_dir / "research.json"
        if not path.exists():
            return
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        for eid, edata in data.items():
            self._entries[eid] = ResearchEntry(**edata)

    def summary(self) -> dict:
        cat_counts = {}
        for e in self._entries.values():
            cat = e.category or "uncategorized"
            cat_counts[cat] = cat_counts.get(cat, 0) + 1
        return {"total": len(self._entries), "by_category": cat_counts}
