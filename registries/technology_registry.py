"""Technology Registry — Tracks every technology used or evaluated."""
from __future__ import annotations

import json
import uuid
from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional


class TechStatus(str):
    CANDIDATE = "candidate"
    EVALUATING = "evaluating"
    APPROVED = "approved"
    REJECTED = "rejected"
    DEPRECATED = "deprecated"
    REPLACED = "replaced"


@dataclass
class TechnologyEntry:
    tech_id: str = ""
    name: str = ""
    repository: str = ""
    purpose: str = ""
    license: str = ""
    maintainer: str = ""
    stars: int = 0
    last_commit: str = ""
    risk_level: str = ""  # low, medium, high
    status: str = "candidate"
    benchmarked: bool = False
    replacement: str = ""
    dependencies: list[str] = field(default_factory=list)
    subsystem: str = ""
    version: str = ""
    score: float = 0.0
    notes: str = ""
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

    def __post_init__(self):
        if not self.tech_id:
            self.tech_id = f"TECH-{uuid.uuid4().hex[:8]}"


class TechnologyRegistry:
    """Registry of all technologies used or evaluated by AstroSage."""

    def __init__(self, registry_dir: str = "registries"):
        self.registry_dir = Path(registry_dir)
        self.registry_dir.mkdir(parents=True, exist_ok=True)
        self._entries: dict[str, TechnologyEntry] = {}

    def register(self, entry: TechnologyEntry) -> str:
        if not entry.tech_id:
            entry.tech_id = f"TECH-{uuid.uuid4().hex[:8]}"
        self._entries[entry.tech_id] = entry
        return entry.tech_id

    def get(self, tech_id: str) -> Optional[TechnologyEntry]:
        return self._entries.get(tech_id)

    def find_by_name(self, name: str) -> list[TechnologyEntry]:
        return [e for e in self._entries.values() if name.lower() in e.name.lower()]

    def find_by_status(self, status: str) -> list[TechnologyEntry]:
        return [e for e in self._entries.values() if e.status == status]

    def find_by_subsystem(self, subsystem: str) -> list[TechnologyEntry]:
        return [e for e in self._entries.values() if e.subsystem == subsystem]

    def list_all(self) -> list[TechnologyEntry]:
        return list(self._entries.values())

    def save(self):
        data = {eid: asdict(e) for eid, e in self._entries.items()}
        with open(self.registry_dir / "technology.json", "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

    def load(self):
        path = self.registry_dir / "technology.json"
        if not path.exists():
            return
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        for eid, edata in data.items():
            self._entries[eid] = TechnologyEntry(**edata)

    def summary(self) -> dict:
        status_counts = {}
        for e in self._entries.values():
            status_counts[e.status] = status_counts.get(e.status, 0) + 1
        return {"total": len(self._entries), "by_status": status_counts}
