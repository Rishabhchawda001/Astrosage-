"""
Evidence Engine — Collects, verifies, and manages evidence from multiple sources.

Every evidence item retains provenance including source, timestamp, and confidence.
Supports 10+ evidence sources via plugin architecture.
"""
from __future__ import annotations

import hashlib
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from pathlib import Path
from typing import Any, Optional


class EvidenceSource(str, Enum):
    ORIGINAL_PDF = "original_pdf"
    OCR_OUTPUT = "ocr_output"
    ALTERNATIVE_EDITION = "alternative_edition"
    INTERNET_ARCHIVE = "internet_archive"
    OPEN_LIBRARY = "open_library"
    CROSSREF = "crossref"
    OPENALEX = "openalex"
    GITHUB = "github"
    ARXIV = "arxiv"
    GOOGLE_DRIVE = "google_drive"
    BROWSER = "browser"
    FILESYSTEM = "filesystem"
    LOCAL_CORPUS = "local_corpus"
    HUMAN_REVIEW = "human_review"
    ACADEMIC_PUBLICATION = "academic_publication"
    TRUSTED_LIBRARY = "trusted_library"
    UNKNOWN = "unknown"


class EvidenceStatus(str, Enum):
    COLLECTED = "collected"
    VERIFIED = "verified"
    CONFLICTED = "conflicted"
    REJECTED = "rejected"
    EXPIRED = "expired"


@dataclass
class EvidenceItem:
    """A single piece of evidence with full provenance."""
    evidence_id: str = ""
    source: EvidenceSource = EvidenceSource.UNKNOWN
    source_name: str = ""  # human-readable source name
    content: str = ""
    content_hash: str = ""
    language: str = ""
    page: int = 0
    confidence: float = 0.0
    metadata: dict[str, Any] = field(default_factory=dict)
    collected_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    collected_by: str = "evidence_engine"
    status: EvidenceStatus = EvidenceStatus.COLLECTED
    provenance: list[dict[str, Any]] = field(default_factory=list)

    def __post_init__(self):
        if not self.evidence_id:
            self.evidence_id = f"EV-{uuid.uuid4().hex[:12]}"
        if not self.content_hash:
            self.content_hash = hashlib.sha256(self.content.encode("utf-8")).hexdigest()

    def add_provenance_step(self, step: str, agent: str = ""):
        self.provenance.append({
            "step": step,
            "agent": agent or "evidence_engine",
            "timestamp": datetime.now(timezone.utc).isoformat(),
        })


@dataclass
class EvidenceQuery:
    """Query for evidence retrieval."""
    text: str = ""
    document_uuid: str = ""
    book_uuid: str = ""
    edition_uuid: str = ""
    language: str = ""
    sources: list[EvidenceSource] = field(default_factory=list)
    min_confidence: float = 0.0
    max_results: int = 10


class EvidenceCollector:
    """Collects evidence from registered sources."""

    def __init__(self):
        self._adapters: dict[str, Any] = {}

    def register_adapter(self, source: EvidenceSource, adapter: Any) -> None:
        self._adapters[source.value] = adapter

    def collect(self, query: EvidenceQuery) -> list[EvidenceItem]:
        items: list[EvidenceItem] = []
        sources = query.sources or list(EvidenceSource)
        for source in sources:
            adapter = self._adapters.get(source.value)
            if adapter:
                try:
                    results = adapter.collect(query)
                    items.extend(results)
                except Exception:
                    pass
        return items


class EvidenceEngine:
    """
    Production evidence engine.

    Manages evidence collection, deduplication, storage and retrieval.
    Every evidence item retains full provenance.
    """

    def __init__(self, evidence_dir: str = "knowledge/evidence"):
        self.evidence_dir = Path(evidence_dir)
        self.evidence_dir.mkdir(parents=True, exist_ok=True)
        self.collector = EvidenceCollector()
        self._items: dict[str, EvidenceItem] = {}

    def submit(self, item: EvidenceItem) -> str:
        """Submit an evidence item. Returns evidence ID."""
        self._items[item.evidence_id] = item
        item.add_provenance_step("submitted")
        return item.evidence_id

    def get(self, evidence_id: str) -> Optional[EvidenceItem]:
        return self._items.get(evidence_id)

    def search(self, query: EvidenceQuery) -> list[EvidenceItem]:
        results = list(self._items.values())
        if query.document_uuid:
            results = [r for r in results if r.metadata.get("document_uuid") == query.document_uuid]
        if query.sources:
            source_set = set(s.value for s in query.sources)
            results = [r for r in results if r.source.value in source_set]
        if query.min_confidence > 0:
            results = [r for r in results if r.confidence >= query.min_confidence]
        results.sort(key=lambda r: r.confidence, reverse=True)
        return results[:query.max_results]

    def deduplicate(self) -> int:
        """Remove duplicate evidence items by content hash. Returns count removed."""
        seen: dict[str, str] = {}
        to_remove: list[str] = []
        for eid, item in self._items.items():
            if item.content_hash in seen:
                to_remove.append(eid)
            else:
                seen[item.content_hash] = eid
        for eid in to_remove:
            del self._items[eid]
        return len(to_remove)

    def verify(self, evidence_id: str) -> bool:
        """Verify evidence integrity by rehashing content."""
        item = self._items.get(evidence_id)
        if not item:
            return False
        expected = item.content_hash
        actual = hashlib.sha256(item.content.encode("utf-8")).hexdigest()
        if actual != expected:
            item.status = EvidenceStatus.REJECTED
            return False
        item.add_provenance_step("integrity_verified")
        return True

    def summary(self) -> dict:
        source_counts: dict[str, int] = {}
        status_counts: dict[str, int] = {}
        for item in self._items.values():
            source_counts[item.source.value] = source_counts.get(item.source.value, 0) + 1
            status_counts[item.status.value] = status_counts.get(item.status.value, 0) + 1
        return {
            "total_items": len(self._items),
            "by_source": source_counts,
            "by_status": status_counts,
            "avg_confidence": sum(i.confidence for i in self._items.values()) / max(len(self._items), 1),
        }
