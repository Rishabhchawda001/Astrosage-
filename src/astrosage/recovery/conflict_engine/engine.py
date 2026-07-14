"""
Conflict Engine — Manages disagreements between editions and sources.

When different editions disagree:
  - Never discard
  - Store all variants
  - Track preferred version
  - Record evidence and reasoning
"""
from __future__ import annotations

import json
import uuid
from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from enum import Enum
from pathlib import Path
from typing import Optional


class ConflictSeverity(str, Enum):
    MINOR = "minor"           # Whitespace, punctuation differences
    MODERATE = "moderate"     # Word-level differences
    MAJOR = "major"           # Phrase or verse-level differences
    CRITICAL = "critical"     # Meaning-changing differences


@dataclass
class Variant:
    variant_id: str
    text: str
    source_edition_id: str = ""
    source_name: str = ""
    confidence: float = 0.0
    is_preferred: bool = False
    notes: str = ""


@dataclass
class Conflict:
    conflict_id: str
    document_uuid: str
    book_uuid: str = ""
    page: int = 0
    original_ocr_region: str = ""
    severity: ConflictSeverity = ConflictSeverity.MODERATE
    variants: list[Variant] = field(default_factory=list)
    preferred_variant_id: str = ""
    reason: str = ""
    evidence: list[dict] = field(default_factory=list)
    resolved: bool = False
    resolution_notes: str = ""
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    updated_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


class ConflictEngine:
    """
    Manages conflicts between different editions and sources.

    Every conflict is stored with all variants.
    Nothing is discarded. Everything is linked.
    """

    def __init__(self, engine_dir: str = "knowledge/recovery"):
        self.engine_dir = Path(engine_dir)
        self.engine_dir.mkdir(parents=True, exist_ok=True)
        self._conflicts: dict[str, Conflict] = {}

    def record_conflict(
        self,
        document_uuid: str,
        original_ocr: str,
        variants: list[Variant],
        severity: ConflictSeverity = ConflictSeverity.MODERATE,
        book_uuid: str = "",
        page: int = 0,
        reason: str = "",
    ) -> str:
        """Record a new conflict. Returns conflict_id."""
        conflict_id = f"CF-{uuid.uuid4().hex[:12]}"
        conflict = Conflict(
            conflict_id=conflict_id,
            document_uuid=document_uuid,
            book_uuid=book_uuid,
            page=page,
            original_ocr_region=original_ocr,
            severity=severity,
            variants=variants,
            reason=reason,
        )
        self._conflicts[conflict_id] = conflict
        return conflict_id

    def resolve_conflict(
        self,
        conflict_id: str,
        preferred_variant_id: str,
        notes: str = "",
    ):
        """Resolve a conflict by selecting a preferred variant."""
        if conflict_id in self._conflicts:
            conflict = self._conflicts[conflict_id]
            conflict.preferred_variant_id = preferred_variant_id
            conflict.resolved = True
            conflict.resolution_notes = notes
            conflict.updated_at = datetime.now(timezone.utc).isoformat()
            for v in conflict.variants:
                v.is_preferred = v.variant_id == preferred_variant_id

    def get_conflict(self, conflict_id: str) -> Optional[Conflict]:
        return self._conflicts.get(conflict_id)

    def get_unresolved(self) -> list[Conflict]:
        return [c for c in self._conflicts.values() if not c.resolved]

    def get_by_severity(self, severity: ConflictSeverity) -> list[Conflict]:
        return [c for c in self._conflicts.values() if c.severity == severity]

    def get_by_document(self, document_uuid: str) -> list[Conflict]:
        return [c for c in self._conflicts.values() if c.document_uuid == document_uuid]

    def get_preferred_text(self, conflict_id: str) -> str:
        """Get the preferred variant text for a conflict."""
        conflict = self._conflicts.get(conflict_id)
        if not conflict:
            return ""
        for v in conflict.variants:
            if v.variant_id == conflict.preferred_variant_id:
                return v.text
        return ""

    def save(self):
        data = {}
        for cid, c in self._conflicts.items():
            data[cid] = {
                "conflict_id": c.conflict_id,
                "document_uuid": c.document_uuid,
                "book_uuid": c.book_uuid,
                "page": c.page,
                "original_ocr_region": c.original_ocr_region,
                "severity": c.severity.value,
                "variants": [
                    {
                        "variant_id": v.variant_id,
                        "text": v.text,
                        "source_edition_id": v.source_edition_id,
                        "source_name": v.source_name,
                        "confidence": v.confidence,
                        "is_preferred": v.is_preferred,
                        "notes": v.notes,
                    }
                    for v in c.variants
                ],
                "preferred_variant_id": c.preferred_variant_id,
                "reason": c.reason,
                "evidence": c.evidence,
                "resolved": c.resolved,
                "resolution_notes": c.resolution_notes,
                "created_at": c.created_at,
                "updated_at": c.updated_at,
            }
        filepath = self.engine_dir / "conflicts.json"
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

    def load(self):
        filepath = self.engine_dir / "conflicts.json"
        if not filepath.exists():
            return
        with open(filepath, "r", encoding="utf-8") as f:
            data = json.load(f)
        for cid, cdata in data.items():
            cdata["severity"] = ConflictSeverity(cdata["severity"])
            cdata["variants"] = [Variant(**v) for v in cdata.get("variants", [])]
            self._conflicts[cid] = Conflict(**cdata)

    def summary(self) -> dict:
        severity_counts = {}
        for c in self._conflicts.values():
            severity_counts[c.severity.value] = severity_counts.get(c.severity.value, 0) + 1
        return {
            "total_conflicts": len(self._conflicts),
            "resolved": sum(1 for c in self._conflicts.values() if c.resolved),
            "unresolved": sum(1 for c in self._conflicts.values() if not c.resolved),
            "by_severity": severity_counts,
        }
