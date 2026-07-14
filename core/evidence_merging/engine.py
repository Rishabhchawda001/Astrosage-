"""Evidence Merging — Collect ALL supporting evidence for a knowledge passport."""
from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Optional


@dataclass
class MergedEvidence:
    merge_id: str = ""
    knowledge_uuid: str = ""
    primary_evidence: list[str] = field(default_factory=list)
    secondary_evidence: list[str] = field(default_factory=list)
    supporting_editions: list[str] = field(default_factory=list)
    supporting_translations: list[str] = field(default_factory=list)
    supporting_commentaries: list[str] = field(default_factory=list)
    supporting_references: list[str] = field(default_factory=list)
    total_evidence_count: int = 0
    confidence: float = 0.0
    merged_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

    def __post_init__(self):
        if not self.merge_id:
            self.merge_id = f"ME-{uuid.uuid4().hex[:12]}"
        self.total_evidence_count = (len(self.primary_evidence) + len(self.secondary_evidence) +
                                     len(self.supporting_editions) + len(self.supporting_translations) +
                                     len(self.supporting_commentaries) + len(self.supporting_references))


class EvidenceMergingEngine:
    def __init__(self):
        self._merges: dict[str, MergedEvidence] = {}
        self._by_knowledge: dict[str, str] = {}

    def merge(self, knowledge_uuid: str, **kwargs) -> MergedEvidence:
        existing_id = self._by_knowledge.get(knowledge_uuid)
        if existing_id and existing_id in self._merges:
            merge = self._merges[existing_id]
            for key, val in kwargs.items():
                if hasattr(merge, key) and isinstance(val, list):
                    existing = getattr(merge, key)
                    for item in val:
                        if item not in existing:
                            existing.append(item)
            merge.total_evidence_count = (len(merge.primary_evidence) + len(merge.secondary_evidence) +
                                          len(merge.supporting_editions) + len(merge.supporting_translations) +
                                          len(merge.supporting_commentaries) + len(merge.supporting_references))
            merge.merged_at = datetime.now(timezone.utc).isoformat()
            return merge
        merge = MergedEvidence(knowledge_uuid=knowledge_uuid, **kwargs)
        self._merges[merge.merge_id] = merge
        self._by_knowledge[knowledge_uuid] = merge.merge_id
        return merge

    def get(self, knowledge_uuid: str) -> Optional[MergedEvidence]:
        mid = self._by_knowledge.get(knowledge_uuid)
        return self._merges.get(mid) if mid else None

    def count(self) -> int:
        return len(self._merges)

    def summary(self) -> dict:
        total_ev = sum(m.total_evidence_count for m in self._merges.values())
        return {"total_merges": self.count(), "total_evidence_refs": total_ev}
