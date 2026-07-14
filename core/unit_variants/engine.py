"""Unit Variants — Preserve every version as a variant."""
from __future__ import annotations
import hashlib
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any

@dataclass
class UnitVariant:
    variant_id: str = ""
    unit_id: str = ""
    text: str = ""
    text_hash: str = ""
    variant_type: str = "original"
    source: str = ""
    edition_id: str = ""
    publisher: str = ""
    language: str = ""
    confidence: float = 0.0
    is_primary: bool = False
    evidence_ids: list[str] = field(default_factory=list)
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    metadata: dict[str, Any] = field(default_factory=dict)
    def __post_init__(self):
        if not self.variant_id:
            self.variant_id = f"UV-{uuid.uuid4().hex[:12]}"
        if not self.text_hash and self.text:
            self.text_hash = hashlib.sha256(self.text.encode("utf-8")).hexdigest()[:16]

class UnitVariantEngine:
    def __init__(self):
        self._variants: dict[str, UnitVariant] = {}
        self._by_unit: dict[str, list[str]] = {}
        self._primary: dict[str, str] = {}

    def add(self, unit_id: str, text: str, variant_type: str = "original",
            source: str = "", is_primary: bool = False, **kwargs) -> UnitVariant:
        v = UnitVariant(unit_id=unit_id, text=text, variant_type=variant_type,
                        source=source, is_primary=is_primary, **kwargs)
        self._variants[v.variant_id] = v
        self._by_unit.setdefault(unit_id, []).append(v.variant_id)
        if is_primary:
            self._primary[unit_id] = v.variant_id
        return v

    def get_variants(self, unit_id: str) -> list[UnitVariant]:
        ids = self._by_unit.get(unit_id, [])
        return [self._variants[vid] for vid in ids if vid in self._variants]

    def get_primary(self, unit_id: str) -> UnitVariant | None:
        vid = self._primary.get(unit_id)
        return self._variants.get(vid) if vid else None

    def count(self) -> int:
        return len(self._variants)

    def summary(self) -> dict:
        vt: dict[str, int] = {}
        for v in self._variants.values():
            vt[v.variant_type] = vt.get(v.variant_type, 0) + 1
        return {"total": self.count(), "by_type": vt, "primary_count": len(self._primary)}
