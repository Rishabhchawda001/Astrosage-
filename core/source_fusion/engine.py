"""
Source Fusion Engine — Merges evidence from multiple sources.

Removes duplicates, ranks evidence, and produces fused results.
Never deletes original evidence. Only links.
"""
from __future__ import annotations

import hashlib
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Optional


class FusionStrategy(str, Enum):
    MAJORITY_VOTE = "majority_vote"
    WEIGHTED_AVERAGE = "weighted_average"
    BEST_SOURCE = "best_source"
    CONCATENATE = "concatenate"
    INTERSECTION = "intersection"


@dataclass
class FusedEvidence:
    fusion_id: str = ""
    knowledge_uuid: str = ""
    fused_text: str = ""
    fused_text_hash: str = ""
    source_evidence_ids: list[str] = field(default_factory=list)
    source_editions: list[str] = field(default_factory=list)
    source_count: int = 0
    agreement_score: float = 0.0
    confidence: float = 0.0
    strategy: FusionStrategy = FusionStrategy.MAJORITY_VOTE
    duplicates_removed: int = 0
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    metadata: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self):
        if not self.fusion_id:
            self.fusion_id = f"FE-{uuid.uuid4().hex[:12]}"
        if not self.fused_text_hash and self.fused_text:
            self.fused_text_hash = hashlib.sha256(self.fused_text.encode("utf-8")).hexdigest()[:16]


class SourceFusionEngine:
    """Production source fusion engine."""

    def __init__(self):
        self._fused: dict[str, FusedEvidence] = {}
        self._by_knowledge: dict[str, list[str]] = {}

    def fuse(self, knowledge_uuid: str, texts: list[str], sources: list[str] = None,
             editions: list[str] = None, strategy: FusionStrategy = FusionStrategy.MAJORITY_VOTE,
             **kwargs) -> FusedEvidence:
        sources = sources or []
        editions = editions or []
        seen_hashes: set[str] = set()
        unique_texts: list[str] = []
        duplicates_removed = 0
        for t in texts:
            h = hashlib.sha256(t.encode("utf-8")).hexdigest()[:16]
            if h not in seen_hashes:
                seen_hashes.add(h)
                unique_texts.append(t)
            else:
                duplicates_removed += 1
        if strategy == FusionStrategy.MAJORITY_VOTE and unique_texts:
            fused_text = max(unique_texts, key=lambda t: texts.count(t))
        elif strategy == FusionStrategy.BEST_SOURCE and unique_texts:
            fused_text = unique_texts[0]
        elif strategy == FusionStrategy.CONCATENATE:
            fused_text = "\n".join(unique_texts)
        else:
            fused_text = unique_texts[0] if unique_texts else ""
        text_hashes = [hashlib.sha256(t.encode("utf-8")).hexdigest()[:16] for t in unique_texts]
        agreement = (len(unique_texts) / len(texts)) if texts else 0.0
        fused = FusedEvidence(
            knowledge_uuid=knowledge_uuid, fused_text=fused_text,
            source_evidence_ids=sources, source_editions=editions,
            source_count=len(unique_texts), agreement_score=agreement,
            strategy=strategy, duplicates_removed=duplicates_removed, metadata=kwargs)
        self._fused[fused.fusion_id] = fused
        self._by_knowledge.setdefault(knowledge_uuid, []).append(fused.fusion_id)
        return fused

    def get_fused(self, knowledge_uuid: str) -> list[FusedEvidence]:
        ids = self._by_knowledge.get(knowledge_uuid, [])
        return [self._fused[fid] for fid in ids if fid in self._fused]

    def count(self) -> int:
        return len(self._fused)

    def summary(self) -> dict:
        st: dict[str, int] = {}
        for f in self._fused.values():
            st[f.strategy.value] = st.get(f.strategy.value, 0) + 1
        return {"total": self.count(), "by_strategy": st,
                "total_duplicates_removed": sum(f.duplicates_removed for f in self._fused.values())}
