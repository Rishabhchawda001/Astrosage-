"""Unit Relationships — Explicit relationships between knowledge units."""
from __future__ import annotations
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any

@dataclass
class Relationship:
    relationship_id: str = ""
    source_unit_id: str = ""
    target_unit_id: str = ""
    relationship_type: str = "references"
    weight: float = 1.0
    evidence_ids: list[str] = field(default_factory=list)
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    metadata: dict[str, Any] = field(default_factory=dict)
    def __post_init__(self):
        if not self.relationship_id:
            self.relationship_id = f"REL-{uuid.uuid4().hex[:12]}"

class UnitRelationshipEngine:
    def __init__(self):
        self._relationships: dict[str, Relationship] = {}
        self._by_source: dict[str, list[str]] = {}
        self._by_target: dict[str, list[str]] = {}

    def add(self, source_unit_id: str, target_unit_id: str,
            relationship_type: str = "references", weight: float = 1.0,
            evidence_ids: list[str] | None = None, **kwargs) -> Relationship:
        r = Relationship(source_unit_id=source_unit_id, target_unit_id=target_unit_id,
                         relationship_type=relationship_type, weight=weight,
                         evidence_ids=evidence_ids or [], **kwargs)
        self._relationships[r.relationship_id] = r
        self._by_source.setdefault(source_unit_id, []).append(r.relationship_id)
        self._by_target.setdefault(target_unit_id, []).append(r.relationship_id)
        return r

    def get_outgoing(self, unit_id: str) -> list[Relationship]:
        ids = self._by_source.get(unit_id, [])
        return [self._relationships[rid] for rid in ids if rid in self._relationships]

    def get_incoming(self, unit_id: str) -> list[Relationship]:
        ids = self._by_target.get(unit_id, [])
        return [self._relationships[rid] for rid in ids if rid in self._relationships]

    def find_related(self, unit_id: str) -> list[Relationship]:
        s = set(self._by_source.get(unit_id, []))
        t = set(self._by_target.get(unit_id, []))
        all_ids = s | t
        return [self._relationships[rid] for rid in all_ids if rid in self._relationships]

    def count(self) -> int:
        return len(self._relationships)

    def summary(self) -> dict:
        rt: dict[str, int] = {}
        for r in self._relationships.values():
            rt[r.relationship_type] = rt.get(r.relationship_type, 0) + 1
        return {"total": self.count(), "by_type": rt}
