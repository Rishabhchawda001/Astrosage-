"""
Knowledge Provenance Ledger — Core subsystem for tracking every transformation.

Every transformation in the recovery pipeline is recorded:

  Character → OCR → Recovery → Verification → Edition Alignment → Knowledge Object → Chunk → Embedding → Retrieval → Answer

Every step is logged. Nothing may disappear.
Every modification becomes auditable.
"""
from __future__ import annotations

import json
import time
import uuid
from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from enum import Enum
from pathlib import Path
from typing import Optional, Any


class LedgerEntryType(str, Enum):
    CHARACTER = "character"
    OCR = "ocr"
    RECOVERY = "recovery"
    VERIFICATION = "verification"
    EDITION_ALIGNMENT = "edition_alignment"
    KNOWLEDGE_OBJECT = "knowledge_object"
    CHUNK = "chunk"
    EMBEDDING = "embedding"
    RETRIEVAL = "retrieval"
    ANSWER = "answer"
    CONFLICT = "conflict"
    HUMAN_REVIEW = "human_review"


class LedgerEntryStatus(str, Enum):
    CREATED = "created"
    CONFIRMED = "confirmed"
    SUPERSEDED = "superseded"
    REVOKED = "revoked"


@dataclass
class LedgerEntry:
    """A single entry in the provenance ledger."""
    entry_id: str
    entry_type: LedgerEntryType
    object_id: str  # The artifact this entry tracks
    parent_entry_id: Optional[str] = None
    input_data: dict = field(default_factory=dict)
    output_data: dict = field(default_factory=dict)
    transformation: str = ""  # What transformation was applied
    pipeline_name: str = ""
    pipeline_version: str = ""
    source_checksum: str = ""
    output_checksum: str = ""
    confidence: float = 0.0
    status: LedgerEntryStatus = LedgerEntryStatus.CREATED
    timestamp: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    duration_ms: float = 0.0
    metadata: dict = field(default_factory=dict)


class KnowledgeProvenanceLedger:
    """
    Append-only ledger tracking every transformation in the knowledge pipeline.

    Every step is logged. Nothing may disappear.
    Every modification becomes auditable.
    """

    def __init__(self, ledger_dir: str = "knowledge/recovery"):
        self.ledger_dir = Path(ledger_dir)
        self.ledger_dir.mkdir(parents=True, exist_ok=True)
        self._entries: dict[str, LedgerEntry] = {}
        self._object_entries: dict[str, list[str]] = {}  # object_id -> [entry_ids]

    def _next_id(self) -> str:
        return f"PL-{uuid.uuid4().hex[:12]}"

    def record(
        self,
        entry_type: LedgerEntryType,
        object_id: str,
        transformation: str = "",
        pipeline_name: str = "",
        pipeline_version: str = "",
        input_data: Optional[dict] = None,
        output_data: Optional[dict] = None,
        source_checksum: str = "",
        output_checksum: str = "",
        confidence: float = 0.0,
        parent_entry_id: Optional[str] = None,
        duration_ms: float = 0.0,
        metadata: Optional[dict] = None,
    ) -> str:
        """Record a transformation. Returns entry_id."""
        entry_id = self._next_id()
        entry = LedgerEntry(
            entry_id=entry_id,
            entry_type=entry_type,
            object_id=object_id,
            parent_entry_id=parent_entry_id,
            input_data=input_data or {},
            output_data=output_data or {},
            transformation=transformation,
            pipeline_name=pipeline_name,
            pipeline_version=pipeline_version,
            source_checksum=source_checksum,
            output_checksum=output_checksum,
            confidence=confidence,
            duration_ms=duration_ms,
            metadata=metadata or {},
        )
        self._entries[entry_id] = entry
        if object_id not in self._object_entries:
            self._object_entries[object_id] = []
        self._object_entries[object_id].append(entry_id)
        return entry_id

    def confirm(self, entry_id: str):
        if entry_id in self._entries:
            self._entries[entry_id].status = LedgerEntryStatus.CONFIRMED

    def supersede(self, entry_id: str):
        if entry_id in self._entries:
            self._entries[entry_id].status = LedgerEntryStatus.SUPERSEDED

    def revoke(self, entry_id: str):
        if entry_id in self._entries:
            self._entries[entry_id].status = LedgerEntryStatus.REVOKED

    def get_entry(self, entry_id: str) -> Optional[LedgerEntry]:
        return self._entries.get(entry_id)

    def get_object_history(self, object_id: str) -> list[LedgerEntry]:
        """Get the complete history of a knowledge object."""
        entry_ids = self._object_entries.get(object_id, [])
        entries = [self._entries[eid] for eid in entry_ids if eid in self._entries]
        return sorted(entries, key=lambda e: e.timestamp)

    def get_chain(self, entry_id: str) -> list[LedgerEntry]:
        """Trace the complete chain from an entry back to its origin."""
        chain = []
        current_id = entry_id
        visited = set()
        while current_id and current_id not in visited:
            entry = self._entries.get(current_id)
            if not entry:
                break
            chain.append(entry)
            visited.add(current_id)
            current_id = entry.parent_entry_id
        return list(reversed(chain))

    def get_entries_by_type(self, entry_type: LedgerEntryType) -> list[LedgerEntry]:
        return [e for e in self._entries.values() if e.entry_type == entry_type]

    def get_entries_by_status(self, status: LedgerEntryStatus) -> list[LedgerEntry]:
        return [e for e in self._entries.values() if e.status == status]

    def get_entries_by_pipeline(self, pipeline_name: str) -> list[LedgerEntry]:
        return [e for e in self._entries.values() if e.pipeline_name == pipeline_name]

    def audit_trail(self, object_id: str) -> list[dict]:
        """Generate a human-readable audit trail for an object."""
        history = self.get_object_history(object_id)
        return [
            {
                "entry_id": e.entry_id,
                "type": e.entry_type.value,
                "transformation": e.transformation,
                "pipeline": f"{e.pipeline_name}@{e.pipeline_version}",
                "confidence": e.confidence,
                "status": e.status.value,
                "timestamp": e.timestamp,
            }
            for e in history
        ]

    def save(self):
        """Save the entire ledger to disk."""
        data = {
            "entries": {eid: asdict(e) for eid, e in self._entries.items()},
            "object_index": self._object_entries,
            "summary": self.summary(),
        }
        filepath = self.ledger_dir / "provenance_ledger.json"
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

    def load(self):
        """Load the ledger from disk."""
        filepath = self.ledger_dir / "provenance_ledger.json"
        if not filepath.exists():
            return
        with open(filepath, "r", encoding="utf-8") as f:
            data = json.load(f)
        for eid, edata in data.get("entries", {}).items():
            edata["entry_type"] = LedgerEntryType(edata["entry_type"])
            edata["status"] = LedgerEntryStatus(edata["status"])
            self._entries[eid] = LedgerEntry(**edata)
        self._object_entries = data.get("object_index", {})

    def summary(self) -> dict:
        type_counts = {}
        status_counts = {}
        for e in self._entries.values():
            type_counts[e.entry_type.value] = type_counts.get(e.entry_type.value, 0) + 1
            status_counts[e.status.value] = status_counts.get(e.status.value, 0) + 1
        return {
            "total_entries": len(self._entries),
            "unique_objects": len(self._object_entries),
            "by_type": type_counts,
            "by_status": status_counts,
        }
