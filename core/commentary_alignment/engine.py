"""Commentary Alignment — Align commentaries with their source texts."""
from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Optional


@dataclass
class CommentaryLink:
    link_id: str = ""
    source_edition_id: str = ""
    commentary_edition_id: str = ""
    commentator: str = ""
    coverage: float = 0.0
    confidence: float = 0.0
    metadata: dict[str, Any] = field(default_factory=dict)
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

    def __post_init__(self):
        if not self.link_id:
            self.link_id = f"CL-{uuid.uuid4().hex[:12]}"


class CommentaryAlignmentEngine:
    def __init__(self):
        self._links: dict[str, CommentaryLink] = {}
        self._by_source: dict[str, list[str]] = {}

    def link(self, source_edition_id: str, commentary_edition_id: str, commentator: str = "", coverage: float = 0.0) -> CommentaryLink:
        link = CommentaryLink(source_edition_id=source_edition_id, commentary_edition_id=commentary_edition_id,
                             commentator=commentator, coverage=coverage, confidence=min(1.0, coverage))
        self._links[link.link_id] = link
        self._by_source.setdefault(source_edition_id, []).append(link.link_id)
        return link

    def get_commentaries(self, source_edition_id: str) -> list[CommentaryLink]:
        ids = self._by_source.get(source_edition_id, [])
        return [self._links[lid] for lid in ids if lid in self._links]

    def count(self) -> int:
        return len(self._links)

    def summary(self) -> dict:
        return {"total": self.count()}
