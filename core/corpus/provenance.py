"""Corpus Provenance — Every byte traceable in gap recovery."""
from __future__ import annotations
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Optional

@dataclass
class CorpusProvenanceEntry:
    entry_id: str = ""
    knowledge_uuid: str = ""
    operation: str = ""
    agent: str = ""
    tool: str = ""
    inputs: dict[str, Any] = field(default_factory=dict)
    outputs: dict[str, Any] = field(default_factory=dict)
    confidence: float = 0.0
    previous_entry_id: str = ""
    timestamp: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    def __post_init__(self):
        if not self.entry_id: self.entry_id = f"PV-{uuid.uuid4().hex[:12]}"

class CorpusProvenanceLedger:
    def __init__(self):
        self._entries: dict[str, list[CorpusProvenanceEntry]] = {}
        self._all: dict[str, CorpusProvenanceEntry] = {}
    def record(self, knowledge_uuid: str, operation: str, **kwargs) -> str:
        entry = CorpusProvenanceEntry(knowledge_uuid=knowledge_uuid, operation=operation, **kwargs)
        existing = self._entries.get(knowledge_uuid, [])
        if existing: entry.previous_entry_id = existing[-1].entry_id
        self._entries.setdefault(knowledge_uuid, []).append(entry)
        self._all[entry.entry_id] = entry
        return entry.entry_id
    def get_lineage(self, knowledge_uuid: str) -> list[CorpusProvenanceEntry]:
        return self._entries.get(knowledge_uuid, [])
    def verify_integrity(self, knowledge_uuid: str) -> bool:
        entries = self._entries.get(knowledge_uuid, [])
        for i in range(1, len(entries)):
            if entries[i].previous_entry_id != entries[i - 1].entry_id: return False
        return True
    def count(self) -> int:
        return len(self._all)
    def summary(self) -> dict:
        return {"total_entries": self.count(), "total_knowledge_items": len(self._entries)}
