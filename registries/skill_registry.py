"""Skill Registry — Tracks all AstroSage skills."""
from __future__ import annotations

import json
import uuid
from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional


@dataclass
class SkillEntry:
    skill_id: str = ""
    name: str = ""
    version: str = "1.0.0"
    purpose: str = ""
    category: str = ""  # core, engineering, research, recovery, verification, qa, benchmark, doc
    dependencies: list[str] = field(default_factory=list)
    inputs: list[str] = field(default_factory=list)
    outputs: list[str] = field(default_factory=list)
    examples: list[str] = field(default_factory=list)
    tests: list[str] = field(default_factory=list)
    benchmarks: list[str] = field(default_factory=list)
    compatible_agents: list[str] = field(default_factory=list)
    skill_path: str = ""
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

    def __post_init__(self):
        if not self.skill_id:
            self.skill_id = f"SKILL-{uuid.uuid4().hex[:8]}"


class SkillRegistry:
    """Registry of all AstroSage skills."""

    def __init__(self, registry_dir: str = "registries"):
        self.registry_dir = Path(registry_dir)
        self.registry_dir.mkdir(parents=True, exist_ok=True)
        self._entries: dict[str, SkillEntry] = {}

    def register(self, entry: SkillEntry) -> str:
        if not entry.skill_id:
            entry.skill_id = f"SKILL-{uuid.uuid4().hex[:8]}"
        self._entries[entry.skill_id] = entry
        return entry.skill_id

    def get(self, skill_id: str) -> Optional[SkillEntry]:
        return self._entries.get(skill_id)

    def find_by_name(self, name: str) -> list[SkillEntry]:
        return [e for e in self._entries.values() if name.lower() in e.name.lower()]

    def find_by_category(self, category: str) -> list[SkillEntry]:
        return [e for e in self._entries.values() if e.category == category]

    def list_all(self) -> list[SkillEntry]:
        return list(self._entries.values())

    def save(self):
        data = {eid: asdict(e) for eid, e in self._entries.items()}
        with open(self.registry_dir / "skills.json", "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

    def load(self):
        path = self.registry_dir / "skills.json"
        if not path.exists():
            return
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        for eid, edata in data.items():
            self._entries[eid] = SkillEntry(**edata)

    def summary(self) -> dict:
        cat_counts = {}
        for e in self._entries.values():
            cat = e.category or "uncategorized"
            cat_counts[cat] = cat_counts.get(cat, 0) + 1
        return {"total": len(self._entries), "by_category": cat_counts}
