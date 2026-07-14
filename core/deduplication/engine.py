"""
Deduplication Engine — Detect and link duplicate/equivalent chunks.

Never deletes. Only links. Uses checksums, semantic similarity, 
passport references, and evidence to detect duplicates.
"""
from __future__ import annotations

import hashlib
import uuid
from dataclasses import dataclass, field
from typing import Any, Optional

from core.chunking.engine import Chunk


from enum import Enum

class DuplicateType(str, Enum):
    EXACT = "exact"
    NEAR = "near"
    PARALLEL_TRANSLATION = "parallel_translation"
    REPEATED_COMMENTARY = "repeated_commentary"
    MULTIPLE_EDITION = "multiple_edition"
    EQUIVALENT = "equivalent"


@dataclass
class DuplicateGroup:
    """A group of chunks that are duplicates or near-duplicates."""
    group_id: str = ""
    primary_chunk_id: str = ""
    duplicate_chunk_ids: list[str] = field(default_factory=list)
    duplicate_type: DuplicateType = DuplicateType.EXACT
    similarity_score: float = 0.0
    evidence: list[str] = field(default_factory=list)
    linked_passports: list[str] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self):
        if not self.group_id:
            self.group_id = f"DG-{uuid.uuid4().hex[:12]}"


@dataclass
class DeduplicationResult:
    """Result of deduplication analysis."""
    chunk_id: str = ""
    is_duplicate: bool = False
    group_id: str = ""
    similarity_score: float = 0.0
    linked_chunks: list[str] = field(default_factory=list)


class DeduplicationEngine:
    """
    Production deduplication engine.
    
    Detects exact, near, and semantic duplicates.
    Never deletes — only creates links between chunks.
    """

    def __init__(self, similarity_threshold: float = 0.85):
        self.similarity_threshold = similarity_threshold
        self._groups: dict[str, DuplicateGroup] = {}
        self._chunk_to_group: dict[str, str] = {}
        self._hash_index: dict[str, list[str]] = {}

    def _compute_hash(self, text: str) -> str:
        normalized = " ".join(text.lower().strip().split())
        return hashlib.sha256(normalized.encode("utf-8")).hexdigest()

    def _compute_similarity(self, text_a: str, text_b: str) -> float:
        words_a = set(text_a.lower().split())
        words_b = set(text_b.lower().split())
        if not words_a or not words_b:
            return 0.0
        intersection = words_a & words_b
        union = words_a | words_b
        return len(intersection) / len(union) if union else 0.0

    def detect_exact_duplicates(self, chunks: list[Chunk]) -> list[DuplicateGroup]:
        """Detect chunks with identical text (normalized)."""
        hash_map: dict[str, list[str]] = {}
        for chunk in chunks:
            h = self._compute_hash(chunk.text)
            hash_map.setdefault(h, []).append(chunk.chunk_id)

        groups = []
        for h, chunk_ids in hash_map.items():
            if len(chunk_ids) > 1:
                group = DuplicateGroup(
                    primary_chunk_id=chunk_ids[0],
                    duplicate_chunk_ids=chunk_ids[1:],
                    duplicate_type=DuplicateType.EXACT,
                    similarity_score=1.0,
                )
                groups.append(group)
                for cid in chunk_ids:
                    self._chunk_to_group[cid] = group.group_id
                self._groups[group.group_id] = group
        return groups

    def detect_near_duplicates(self, chunks: list[Chunk]) -> list[DuplicateGroup]:
        """Detect chunks with similar text content."""
        groups = []
        compared: set[tuple[str, str]] = set()
        for i, chunk_a in enumerate(chunks):
            for j, chunk_b in enumerate(chunks):
                if i >= j:
                    continue
                pair = (chunk_a.chunk_id, chunk_b.chunk_id)
                if pair in compared:
                    continue
                compared.add(pair)
                score = self._compute_similarity(chunk_a.text, chunk_b.text)
                if score >= self.similarity_threshold:
                    group = DuplicateGroup(
                        primary_chunk_id=chunk_a.chunk_id,
                        duplicate_chunk_ids=[chunk_b.chunk_id],
                        duplicate_type=DuplicateType.NEAR,
                        similarity_score=score,
                    )
                    groups.append(group)
                    self._groups[group.group_id] = group
                    self._chunk_to_group[chunk_a.chunk_id] = group.group_id
                    self._chunk_to_group[chunk_b.chunk_id] = group.group_id
        return groups

    def detect_parallel_translations(self, chunks_a: list[Chunk], chunks_b: list[Chunk]) -> list[DuplicateGroup]:
        """Detect chunks that are translations of each other."""
        groups = []
        for ca in chunks_a:
            for cb in chunks_b:
                score = self._compute_similarity(ca.text, cb.text)
                if score >= self.similarity_threshold * 0.8:
                    group = DuplicateGroup(
                        primary_chunk_id=ca.chunk_id,
                        duplicate_chunk_ids=[cb.chunk_id],
                        duplicate_type=DuplicateType.PARALLEL_TRANSLATION,
                        similarity_score=score,
                    )
                    groups.append(group)
                    self._groups[group.group_id] = group
        return groups

    def link_chunks(self, chunk_id_a: str, chunk_id_b: str, duplicate_type: DuplicateType = DuplicateType.EQUIVALENT) -> DuplicateGroup:
        group = DuplicateGroup(
            primary_chunk_id=chunk_id_a,
            duplicate_chunk_ids=[chunk_id_b],
            duplicate_type=duplicate_type,
        )
        self._groups[group.group_id] = group
        self._chunk_to_group[chunk_id_a] = group.group_id
        self._chunk_to_group[chunk_id_b] = group.group_id
        return group

    def get_group(self, group_id: str) -> Optional[DuplicateGroup]:
        return self._groups.get(group_id)

    def get_group_for_chunk(self, chunk_id: str) -> Optional[DuplicateGroup]:
        gid = self._chunk_to_group.get(chunk_id)
        if gid:
            return self._groups.get(gid)
        return None

    def get_all_duplicates(self, chunk_id: str) -> list[str]:
        group = self.get_group_for_chunk(chunk_id)
        if not group:
            return []
        ids = [group.primary_chunk_id] + group.duplicate_chunk_ids
        return [cid for cid in ids if cid != chunk_id]

    def summary(self) -> dict:
        type_counts: dict[str, int] = {}
        for g in self._groups.values():
            type_counts[g.duplicate_type] = type_counts.get(g.duplicate_type, 0) + 1
        return {
            "total_groups": len(self._groups),
            "total_linked_chunks": len(self._chunk_to_group),
            "by_type": type_counts,
        }
