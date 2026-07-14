"""
Provenance Ledger — Records every operation in the knowledge pipeline.

Every transformation is logged: source, timestamp, agent, tool, inputs, outputs,
confidence, version chain. Nothing may disappear.
"""
from __future__ import annotations

import hashlib
import json
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional


@dataclass
class ProvenanceEntry:
    """A single provenance record for a transformation."""
    entry_id: str = ""
    knowledge_uuid: str = ""
    operation: str = ""
    source_hash: str = ""
    output_hash: str = ""
    agent: str = ""
    tool: str = ""
    pipeline_version: str = ""
    inputs: dict[str, Any] = field(default_factory=dict)
    outputs: dict[str, Any] = field(default_factory=dict)
    confidence: float = 0.0
    timestamp: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    previous_entry_id: str = ""
    metadata: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self):
        if not self.entry_id:
            self.entry_id = f"PV-{uuid.uuid4().hex[:12]}"


class ProvenanceLedger:
    """
    Immutable provenance ledger.

    Records every transformation with full traceability.
    Entries are append-only — never modified or deleted.
    Supports lineage queries and verification.
    """

    def __init__(self, ledger_dir: str = "knowledge/provenance"):
        self.ledger_dir = Path(ledger_dir)
        self.ledger_dir.mkdir(parents=True, exist_ok=True)
        self._entries: dict[str, list[ProvenanceEntry]] = {}
        self._all_entries: dict[str, ProvenanceEntry] = {}

    def record(self, entry: ProvenanceEntry) -> str:
        """Record a provenance entry. Returns entry ID."""
        # Link to previous entry for same knowledge_uuid
        if entry.knowledge_uuid in self._entries:
            existing = self._entries[entry.knowledge_uuid]
            if existing and not entry.previous_entry_id:
                entry.previous_entry_id = existing[-1].entry_id
        self._entries.setdefault(entry.knowledge_uuid, []).append(entry)
        self._all_entries[entry.entry_id] = entry
        return entry.entry_id

    def record_operation(
        self,
        knowledge_uuid: str,
        operation: str,
        source_hash: str = "",
        output_hash: str = "",
        agent: str = "",
        tool: str = "",
        pipeline_version: str = "",
        inputs: dict | None = None,
        outputs: dict | None = None,
        confidence: float = 0.0,
    ) -> str:
        """Convenience method to record an operation."""
        entry = ProvenanceEntry(
            knowledge_uuid=knowledge_uuid,
            operation=operation,
            source_hash=source_hash,
            output_hash=output_hash,
            agent=agent,
            tool=tool,
            pipeline_version=pipeline_version,
            inputs=inputs or {},
            outputs=outputs or {},
            confidence=confidence,
        )
        return self.record(entry)

    def get_entry(self, entry_id: str) -> Optional[ProvenanceEntry]:
        return self._all_entries.get(entry_id)

    def get_lineage(self, knowledge_uuid: str) -> list[ProvenanceEntry]:
        """Get the full lineage of a knowledge item."""
        return self._entries.get(knowledge_uuid, [])

    def get_lineage_length(self, knowledge_uuid: str) -> int:
        return len(self._entries.get(knowledge_uuid, []))

    def verify_integrity(self, knowledge_uuid: str) -> bool:
        """Verify that the lineage chain is unbroken."""
        entries = self._entries.get(knowledge_uuid, [])
        if not entries:
            return True
        for i in range(1, len(entries)):
            if entries[i].previous_entry_id != entries[i - 1].entry_id:
                return False
        return True

    def search(
        self,
        operation: str = "",
        tool: str = "",
        pipeline_version: str = "",
    ) -> list[ProvenanceEntry]:
        results = list(self._all_entries.values())
        if operation:
            results = [e for e in results if e.operation == operation]
        if tool:
            results = [e for e in results if e.tool == tool]
        if pipeline_version:
            results = [e for e in results if e.pipeline_version == pipeline_version]
        return results

    def summary(self) -> dict:
        operation_counts: dict[str, int] = {}
        tool_counts: dict[str, int] = {}
        for entry in self._all_entries.values():
            operation_counts[entry.operation] = operation_counts.get(entry.operation, 0) + 1
            tool_counts[entry.tool] = tool_counts.get(entry.tool, 0) + 1
        return {
            "total_entries": len(self._all_entries),
            "total_knowledge_items": len(self._entries),
            "by_operation": operation_counts,
            "by_tool": tool_counts,
        }

    def flush(self, knowledge_uuid: str) -> str:
        """Persist lineage to disk as JSON."""
        entries = self._entries.get(knowledge_uuid, [])
        if not entries:
            return ""
        filepath = self.ledger_dir / f"{knowledge_uuid}.json"
        data = [
            {
                "entry_id": e.entry_id,
                "operation": e.operation,
                "source_hash": e.source_hash,
                "output_hash": e.output_hash,
                "agent": e.agent,
                "tool": e.tool,
                "pipeline_version": e.pipeline_version,
                "timestamp": e.timestamp,
                "previous_entry_id": e.previous_entry_id,
            }
            for e in entries
        ]
        filepath.write_text(json.dumps(data, indent=2, ensure_ascii=False))
        return str(filepath)
