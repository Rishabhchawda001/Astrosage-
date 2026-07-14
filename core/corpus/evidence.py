"""Corpus Evidence — Evidence collection for corpus gap recovery."""
from __future__ import annotations
import hashlib, uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Optional

class CorpusEvidenceType(str, Enum):
    ORIGINAL_PDF = "original_pdf"
    OCR_OUTPUT = "ocr_output"
    ALTERNATIVE_EDITION = "alternative_edition"
    DIGITAL_LIBRARY = "digital_library"
    ACADEMIC = "academic"
    HUMAN_REVIEW = "human_review"
    ARCHIVE = "archive"
    UNKNOWN = "unknown"

@dataclass
class CorpusEvidenceItem:
    evidence_id: str = ""
    source_id: str = ""
    passport_id: str = ""
    knowledge_uuid: str = ""
    content: str = ""
    content_hash: str = ""
    evidence_type: CorpusEvidenceType = CorpusEvidenceType.UNKNOWN
    confidence: float = 0.0
    trust_score: float = 0.0
    edition: str = ""
    publisher: str = ""
    language: str = ""
    checksum: str = ""
    metadata: dict[str, Any] = field(default_factory=dict)
    collected_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    def __post_init__(self):
        if not self.evidence_id: self.evidence_id = f"EV-{uuid.uuid4().hex[:12]}"
        if not self.content_hash and self.content: self.content_hash = hashlib.sha256(self.content.encode("utf-8")).hexdigest()
        if not self.checksum: self.checksum = self.content_hash

class CorpusEvidenceEngine:
    def __init__(self):
        self._items: dict[str, CorpusEvidenceItem] = {}
        self._by_knowledge: dict[str, list[str]] = {}
    def submit(self, item: CorpusEvidenceItem) -> str:
        self._items[item.evidence_id] = item
        if item.knowledge_uuid: self._by_knowledge.setdefault(item.knowledge_uuid, []).append(item.evidence_id)
        return item.evidence_id
    def get(self, evidence_id: str) -> Optional[CorpusEvidenceItem]:
        return self._items.get(evidence_id)
    def deduplicate(self) -> int:
        seen: dict[str, str] = {}
        to_remove = []
        for eid, item in self._items.items():
            if item.content_hash in seen: to_remove.append(eid)
            else: seen[item.content_hash] = eid
        for eid in to_remove: del self._items[eid]
        return len(to_remove)
    def count(self) -> int:
        return len(self._items)
    def summary(self) -> dict:
        return {"total_items": self.count()}
