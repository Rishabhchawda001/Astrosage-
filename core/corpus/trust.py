"""Corpus Trust — Trust scoring for external knowledge sources in corpus context."""
from __future__ import annotations
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Optional

class SourceTrustLevel(str, Enum):
    AUTHORITATIVE = "authoritative"
    RELIABLE = "reliable"
    MODERATE = "moderate"
    LOW = "low"
    UNTRUSTED = "untrusted"
    UNKNOWN = "unknown"

@dataclass
class SourceTrustRecord:
    trust_id: str = ""
    source_id: str = ""
    trust_score: float = 0.0
    trust_level: SourceTrustLevel = SourceTrustLevel.UNKNOWN
    publisher: str = ""
    edition: str = ""
    language: str = ""
    year: str = ""
    authority: float = 0.0
    authenticity: float = 0.0
    license: str = ""
    version: str = ""
    evidence_count: int = 0
    metadata: dict[str, Any] = field(default_factory=dict)
    evaluated_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    def __post_init__(self):
        if not self.trust_id:
            self.trust_id = f"TR-{uuid.uuid4().hex[:12]}"

class CorpusSourceTrustEngine:
    def __init__(self):
        self._records: dict[str, SourceTrustRecord] = {}
        self._by_source: dict[str, str] = {}
    def evaluate(self, source_id: str, authority: float = 0.5, authenticity: float = 0.5, evidence_count: int = 0, **kwargs) -> SourceTrustRecord:
        trust_score = (authority * 0.4 + authenticity * 0.4 + min(1.0, evidence_count * 0.2) * 0.2)
        if trust_score >= 0.8: level = SourceTrustLevel.AUTHORITATIVE
        elif trust_score >= 0.6: level = SourceTrustLevel.RELIABLE
        elif trust_score >= 0.4: level = SourceTrustLevel.MODERATE
        elif trust_score >= 0.2: level = SourceTrustLevel.LOW
        else: level = SourceTrustLevel.UNTRUSTED
        record = SourceTrustRecord(source_id=source_id, trust_score=round(trust_score, 4), trust_level=level, authority=authority, authenticity=authenticity, evidence_count=evidence_count, **kwargs)
        self._records[record.trust_id] = record
        self._by_source[source_id] = record.trust_id
        return record
    def get_trust(self, source_id: str) -> Optional[SourceTrustRecord]:
        tid = self._by_source.get(source_id)
        return self._records.get(tid) if tid else None
    def count(self) -> int:
        return len(self._records)
    def summary(self) -> dict:
        scores = [r.trust_score for r in self._records.values()]
        return {"total": self.count(), "avg_trust": sum(scores) / max(len(scores), 1)}
