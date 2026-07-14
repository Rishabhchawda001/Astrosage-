"""
Variant Management Engine — Generates knowledge variants instead of replacements.

Nothing is overwritten. Every variant remains traceable.
Stores every version from every source.
"""
from __future__ import annotations

import hashlib
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Optional


class VariantType(str, Enum):
    ORIGINAL = "original"
    EDITION_VARIANT = "edition_variant"
    TRANSLATION = "translation"
    COMMENTARY = "commentary"
    RECOVERED = "recovered"
    CORRECTED = "corrected"
    CONFLICTING = "conflicting"
    UNKNOWN = "unknown"


@dataclass
class KnowledgeVariant:
    variant_id: str = ""
    knowledge_uuid: str = ""
    variant_type: VariantType = VariantType.ORIGINAL
    text: str = ""
    text_hash: str = ""
    source: str = ""
    edition_uuid: str = ""
    publisher: str = ""
    language: str = ""
    confidence: float = 0.0
    is_primary: bool = False
    evidence_ids: list[str] = field(default_factory=list)
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    metadata: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self):
        if not self.variant_id:
            self.variant_id = f"KV-{uuid.uuid4().hex[:12]}"
        if not self.text_hash and self.text:
            self.text_hash = hashlib.sha256(self.text.encode("utf-8")).hexdigest()[:16]


class VariantManager:
    """Production variant management engine."""

    def __init__(self):
        self._variants: dict[str, KnowledgeVariant] = {}
        self._by_knowledge: dict[str, list[str]] = {}
        self._primary: dict[str, str] = {}

    def add_variant(self, knowledge_uuid: str, text: str,
                    variant_type: VariantType = VariantType.ORIGINAL,
                    source: str = "", edition_uuid: str = "",
                    publisher: str = "", language: str = "",
                    confidence: float = 0.0, is_primary: bool = False,
                    evidence_ids: list[str] | None = None,
                    **kwargs) -> KnowledgeVariant:
        variant = KnowledgeVariant(
            knowledge_uuid=knowledge_uuid, variant_type=variant_type,
            text=text, source=source, edition_uuid=edition_uuid,
            publisher=publisher, language=language, confidence=confidence,
            is_primary=is_primary, evidence_ids=evidence_ids or [],
            metadata=kwargs)
        self._variants[variant.variant_id] = variant
        self._by_knowledge.setdefault(knowledge_uuid, []).append(variant.variant_id)
        if is_primary:
            self._primary[knowledge_uuid] = variant.variant_id
        return variant

    def get_primary(self, knowledge_uuid: str) -> KnowledgeVariant | None:
        vid = self._primary.get(knowledge_uuid)
        return self._variants.get(vid) if vid else None

    def get_variants(self, knowledge_uuid: str) -> list[KnowledgeVariant]:
        ids = self._by_knowledge.get(knowledge_uuid, [])
        return [self._variants[vid] for vid in ids if vid in self._variants]

    def find_similar(self, text: str, threshold: float = 0.8) -> list[KnowledgeVariant]:
        results = []
        text_words = set(text.lower().split())
        for v in self._variants.values():
            v_words = set(v.text.lower().split())
            if not text_words or not v_words:
                continue
            overlap = len(text_words & v_words) / max(len(text_words | v_words), 1)
            if overlap >= threshold:
                results.append(v)
        return results

    def count(self) -> int:
        return len(self._variants)

    def knowledge_count(self) -> int:
        return len(self._by_knowledge)

    def summary(self) -> dict:
        tt: dict[str, int] = {}
        for v in self._variants.values():
            tt[v.variant_type.value] = tt.get(v.variant_type.value, 0) + 1
        return {"total_variants": self.count(), "knowledge_units": self.knowledge_count(),
                "by_type": tt, "primary_assigned": len(self._primary)}
