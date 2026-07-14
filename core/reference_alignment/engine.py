"""Reference Alignment — Cross-link texts across the Dharmic corpus."""
from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Optional


class ReferenceCategory(str):
    VEDA = "veda"
    UPANISHAD = "upanishad"
    PURANA = "purana"
    RAMAYANA = "ramayana"
    MAHABHARATA = "mahabharata"
    BHAGAVAD_GITA = "bhagavad_gita"
    AYURVEDA = "ayurveda"
    JYOTISHA = "jyotisha"
    YOGA = "yoga"
    VEDANTA = "vedanta"
    NYAYA = "nyaya"
    SAMKHYA = "samkhya"


@dataclass
class ReferenceLink:
    link_id: str = ""
    source_text_id: str = ""
    referenced_text_id: str = ""
    reference_type: str = ""
    description: str = ""
    confidence: float = 0.0
    metadata: dict[str, Any] = field(default_factory=dict)
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

    def __post_init__(self):
        if not self.link_id:
            self.link_id = f"RL-{uuid.uuid4().hex[:12]}"


class ReferenceAlignmentEngine:
    def __init__(self):
        self._links: dict[str, ReferenceLink] = {}
        self._by_source: dict[str, list[str]] = {}
        self._by_category: dict[str, list[str]] = {}

    def link(self, source_text_id: str, referenced_text_id: str, reference_type: str = "", description: str = "") -> ReferenceLink:
        link = ReferenceLink(source_text_id=source_text_id, referenced_text_id=referenced_text_id,
                            reference_type=reference_type, description=description)
        self._links[link.link_id] = link
        self._by_source.setdefault(source_text_id, []).append(link.link_id)
        self._by_category.setdefault(reference_type, []).append(link.link_id)
        return link

    def get_references(self, text_id: str) -> list[ReferenceLink]:
        ids = self._by_source.get(text_id, [])
        return [self._links[lid] for lid in ids if lid in self._links]

    def count(self) -> int:
        return len(self._links)

    def summary(self) -> dict:
        cat_counts: dict[str, int] = {}
        for l in self._links.values():
            cat_counts[l.reference_type] = cat_counts.get(l.reference_type, 0) + 1
        return {"total": self.count(), "by_type": cat_counts}
