"""Unit Identity — Globally unique identity for every knowledge unit."""
from __future__ import annotations
import hashlib
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any

@dataclass
class UnitIdentity:
    identity_id: str = ""
    unit_id: str = ""
    book_uuid: str = ""
    edition_uuid: str = ""
    language: str = "unknown"
    page: int = 0
    paragraph: int = 0
    sentence: int = 0
    verse: str = ""
    chapter: str = ""
    section: str = ""
    checksum: str = ""
    version: int = 1
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    metadata: dict[str, Any] = field(default_factory=dict)
    def __post_init__(self):
        if not self.identity_id:
            self.identity_id = f"UI-{uuid.uuid4().hex[:12]}"

class UnitIdentityEngine:
    def __init__(self):
        self._identities: dict[str, UnitIdentity] = {}
        self._by_unit: dict[str, str] = {}
        self._by_book: dict[str, list[str]] = {}

    def create(self, unit_id: str, book_uuid: str = "", edition_uuid: str = "",
               language: str = "unknown", page: int = 0, paragraph: int = 0,
               sentence: int = 0, verse: str = "", chapter: str = "",
               section: str = "", checksum: str = "", **kwargs) -> UnitIdentity:
        ident = UnitIdentity(unit_id=unit_id, book_uuid=book_uuid, edition_uuid=edition_uuid,
                             language=language, page=page, paragraph=paragraph,
                             sentence=sentence, verse=verse, chapter=chapter,
                             section=section, checksum=checksum, metadata=kwargs)
        self._identities[ident.identity_id] = ident
        self._by_unit[unit_id] = ident.identity_id
        if book_uuid:
            self._by_book.setdefault(book_uuid, []).append(ident.identity_id)
        return ident

    def get_by_unit(self, unit_id: str) -> UnitIdentity | None:
        iid = self._by_unit.get(unit_id)
        return self._identities.get(iid) if iid else None

    def get_by_book(self, book_uuid: str) -> list[UnitIdentity]:
        ids = self._by_book.get(book_uuid, [])
        return [self._identities[iid] for iid in ids if iid in self._identities]

    def count(self) -> int:
        return len(self._identities)
