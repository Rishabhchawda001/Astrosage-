"""
Edition Registry — Tracks different editions of the same work.

AstroSage must understand the relationships between:
  - Original manuscripts
  - Translations
  - Publisher editions
  - Critical editions
  - Commentaries
  - Roman transliterations
  - Regional editions

Every edition receives a UUID. Nothing merged. Everything linked.
"""
from __future__ import annotations

import json
import uuid
from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from enum import Enum
from pathlib import Path
from typing import Optional


class EditionType(str, Enum):
    ORIGINAL = "original"
    TRANSLATION = "translation"
    PUBLISHER_EDITION = "publisher_edition"
    CRITICAL_EDITION = "critical_edition"
    COMMENTARY = "commentary"
    ROMAN_TRANSLITERATION = "roman_transliteration"
    REGIONAL_EDITION = "regional_edition"
    DIGITAL_REPRINT = "digital_reprint"
    UNKNOWN = "unknown"


class EditionRelationship(str, Enum):
    TRANSLATION_OF = "translation_of"
    EDITION_OF = "edition_of"
    COMMENTARY_ON = "commentary_on"
    TRANSLITERATION_OF = "transliteration_of"
    REPRINT_OF = "reprint_of"
    DERIVED_FROM = "derived_from"
    RELATED_TO = "related_to"


@dataclass
class EditionLink:
    """A link between two editions."""
    source_edition_id: str
    target_edition_id: str
    relationship: EditionRelationship
    confidence: float = 1.0
    notes: str = ""


@dataclass
class Edition:
    title: str
    edition_id: str = ""
    author: str = ""
    original_title: str = ""
    edition_type: EditionType = EditionType.UNKNOWN
    publisher: str = ""
    year: str = ""
    language: str = ""
    script: str = ""
    isbn: str = ""
    doi: str = ""
    source_url: str = ""
    source_id: str = ""  # Link to Knowledge Source Registry
    document_uuid: str = ""  # Link to Knowledge Registry
    sha256: str = ""
    trust_level: float = 0.5
    text_agreement_scores: dict = field(default_factory=dict)  # edition_id -> agreement %
    metadata: dict = field(default_factory=dict)
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    updated_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


class EditionRegistry:
    """
    Registry of all editions of all works.

    Every edition is tracked independently.
    Relationships between editions are explicitly recorded.
    """

    def __init__(self, registry_dir: str = "knowledge/recovery/edition_registry"):
        self.registry_dir = Path(registry_dir)
        self.registry_dir.mkdir(parents=True, exist_ok=True)
        self._editions: dict[str, Edition] = {}
        self._links: list[EditionLink] = []

    def register_edition(self, edition: Edition) -> str:
        """Register a new edition. Returns edition_id."""
        if not edition.edition_id:
            edition.edition_id = f"ED-{uuid.uuid4().hex[:12]}"
        edition.updated_at = datetime.now(timezone.utc).isoformat()
        self._editions[edition.edition_id] = edition
        return edition.edition_id

    def link_editions(
        self,
        source_id: str,
        target_id: str,
        relationship: EditionRelationship,
        confidence: float = 1.0,
        notes: str = "",
    ):
        """Create a link between two editions."""
        link = EditionLink(
            source_edition_id=source_id,
            target_edition_id=target_id,
            relationship=relationship,
            confidence=confidence,
            notes=notes,
        )
        self._links.append(link)

    def get_edition(self, edition_id: str) -> Optional[Edition]:
        return self._editions.get(edition_id)

    def get_related_editions(self, edition_id: str) -> list[tuple[Edition, EditionRelationship]]:
        """Get all editions related to the given one."""
        related = []
        for link in self._links:
            if link.source_edition_id == edition_id:
                target = self._editions.get(link.target_edition_id)
                if target:
                    related.append((target, link.relationship))
            elif link.target_edition_id == edition_id:
                source = self._editions.get(link.source_edition_id)
                if source:
                    related.append((source, link.relationship))
        return related

    def find_editions_by_title(self, title: str) -> list[Edition]:
        """Find all editions matching a title (case-insensitive)."""
        title_lower = title.lower()
        return [e for e in self._editions.values() if title_lower in e.title.lower()]

    def find_editions_by_author(self, author: str) -> list[Edition]:
        author_lower = author.lower()
        return [e for e in self._editions.values() if author_lower in e.author.lower()]

    def find_editions_by_type(self, edition_type: EditionType) -> list[Edition]:
        return [e for e in self._editions.values() if e.edition_type == edition_type]

    def find_editions_by_language(self, language: str) -> list[Edition]:
        return [e for e in self._editions.values() if e.language == language]

    def update_agreement_score(self, edition_id: str, other_id: str, score: float):
        if edition_id in self._editions:
            self._editions[edition_id].text_agreement_scores[other_id] = score
            self._editions[edition_id].updated_at = datetime.now(timezone.utc).isoformat()

    def save(self):
        editions_data = {
            eid: {
                "edition_id": e.edition_id,
                "title": e.title,
                "author": e.author,
                "original_title": e.original_title,
                "edition_type": e.edition_type.value,
                "publisher": e.publisher,
                "year": e.year,
                "language": e.language,
                "script": e.script,
                "isbn": e.isbn,
                "doi": e.doi,
                "source_url": e.source_url,
                "source_id": e.source_id,
                "document_uuid": e.document_uuid,
                "sha256": e.sha256,
                "trust_level": e.trust_level,
                "text_agreement_scores": e.text_agreement_scores,
                "metadata": e.metadata,
                "created_at": e.created_at,
                "updated_at": e.updated_at,
            }
            for eid, e in self._editions.items()
        }
        links_data = [
            {
                "source_edition_id": l.source_edition_id,
                "target_edition_id": l.target_edition_id,
                "relationship": l.relationship.value,
                "confidence": l.confidence,
                "notes": l.notes,
            }
            for l in self._links
        ]
        filepath = self.registry_dir / "editions.json"
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump({"editions": editions_data, "links": links_data}, f, indent=2, ensure_ascii=False)

    def load(self):
        filepath = self.registry_dir / "editions.json"
        if not filepath.exists():
            return
        with open(filepath, "r", encoding="utf-8") as f:
            data = json.load(f)
        for eid, edata in data.get("editions", {}).items():
            edata["edition_type"] = EditionType(edata["edition_type"])
            self._editions[eid] = Edition(**edata)
        for ldata in data.get("links", []):
            ldata["relationship"] = EditionRelationship(ldata["relationship"])
            self._links.append(EditionLink(**ldata))

    def summary(self) -> dict:
        type_counts = {}
        lang_counts = {}
        for e in self._editions.values():
            type_counts[e.edition_type.value] = type_counts.get(e.edition_type.value, 0) + 1
            lang_counts[e.language] = lang_counts.get(e.language, 0) + 1
        return {
            "total_editions": len(self._editions),
            "total_links": len(self._links),
            "by_type": type_counts,
            "by_language": lang_counts,
        }
