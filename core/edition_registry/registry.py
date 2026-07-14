"""Edition Registry — Every discovered edition gets a permanent record."""
from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Optional


@dataclass
class EditionEntry:
    edition_id: str = ""
    book_title: str = ""
    alternate_titles: list[str] = field(default_factory=list)
    author: str = ""
    translator: str = ""
    commentator: str = ""
    publisher: str = ""
    year: str = ""
    language: str = ""
    script: str = ""
    volume: str = ""
    isbn: str = ""
    chapter_count: int = 0
    verse_count: int = 0
    source_id: str = ""
    url: str = ""
    checksum: str = ""
    trust_score: float = 0.0
    license_id: str = ""
    availability: str = "unknown"
    metadata: dict[str, Any] = field(default_factory=dict)
    registered_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

    def __post_init__(self):
        if not self.edition_id:
            self.edition_id = f"ED-{uuid.uuid4().hex[:12]}"


class EditionRegistry:
    def __init__(self):
        self._entries: dict[str, EditionEntry] = {}
        self._by_title: dict[str, list[str]] = {}
        self._by_author: dict[str, list[str]] = {}
        self._by_language: dict[str, list[str]] = {}

    def register(self, entry: EditionEntry) -> str:
        self._entries[entry.edition_id] = entry
        title_key = entry.book_title.lower().strip()
        self._by_title.setdefault(title_key, []).append(entry.edition_id)
        if entry.author:
            self._by_author.setdefault(entry.author.lower(), []).append(entry.edition_id)
        if entry.language:
            self._by_language.setdefault(entry.language.lower(), []).append(entry.edition_id)
        return entry.edition_id

    def get(self, edition_id: str) -> Optional[EditionEntry]:
        return self._entries.get(edition_id)

    def find_by_title(self, title: str) -> list[EditionEntry]:
        ids = self._by_title.get(title.lower().strip(), [])
        return [self._entries[eid] for eid in ids if eid in self._entries]

    def find_by_author(self, author: str) -> list[EditionEntry]:
        ids = self._by_author.get(author.lower(), [])
        return [self._entries[eid] for eid in ids if eid in self._entries]

    def find_by_language(self, language: str) -> list[EditionEntry]:
        ids = self._by_language.get(language.lower(), [])
        return [self._entries[eid] for eid in ids if eid in self._entries]

    def count(self) -> int:
        return len(self._entries)

    def summary(self) -> dict:
        lang_counts: dict[str, int] = {}
        for e in self._entries.values():
            lang_counts[e.language] = lang_counts.get(e.language, 0) + 1
        return {"total": self.count(), "by_language": lang_counts}
