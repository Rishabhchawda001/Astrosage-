"""
Knowledge Version Engine — Tracks every version of a knowledge unit.

Nothing is overwritten. Every change creates a new version.
All versions remain accessible and traceable.
"""
from __future__ import annotations

import hashlib
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Optional


class VersionType(str, Enum):
    ORIGINAL = "original"
    RECOVERED = "recovered"
    VERIFIED = "verified"
    REVISED = "revised"
    CONFLICTED = "conflicted"
    UNKNOWN = "unknown"


@dataclass
class KnowledgeVersion:
    version_id: str = ""
    knowledge_uuid: str = ""
    version_number: int = 0
    version_type: VersionType = VersionType.ORIGINAL
    text: str = ""
    text_hash: str = ""
    source: str = ""
    edition_uuid: str = ""
    confidence: float = 0.0
    evidence_ids: list[str] = field(default_factory=list)
    change_reason: str = ""
    is_current: bool = False
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    metadata: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self):
        if not self.version_id:
            self.version_id = f"KV-{uuid.uuid4().hex[:12]}"
        if not self.text_hash and self.text:
            self.text_hash = hashlib.sha256(self.text.encode("utf-8")).hexdigest()[:16]


class KnowledgeVersionEngine:
    """Production knowledge versioning engine."""

    def __init__(self):
        self._versions: dict[str, KnowledgeVersion] = {}
        self._by_knowledge: dict[str, list[str]] = {}
        self._current: dict[str, str] = {}

    def create_version(self, knowledge_uuid: str, text: str, version_type: VersionType,
                       source: str = "", edition_uuid: str = "",
                       confidence: float = 0.0, evidence_ids: list[str] | None = None,
                       change_reason: str = "", **kwargs) -> KnowledgeVersion:
        existing = self._by_knowledge.get(knowledge_uuid, [])
        version_number = len(existing) + 1
        version = KnowledgeVersion(
            knowledge_uuid=knowledge_uuid, version_number=version_number,
            version_type=version_type, text=text, source=source,
            edition_uuid=edition_uuid, confidence=confidence,
            evidence_ids=evidence_ids or [], change_reason=change_reason,
            is_current=True, metadata=kwargs)
        self._versions[version.version_id] = version
        self._by_knowledge.setdefault(knowledge_uuid, []).append(version.version_id)
        if knowledge_uuid in self._current:
            old_vid = self._current[knowledge_uuid]
            if old_vid in self._versions:
                self._versions[old_vid].is_current = False
        self._current[knowledge_uuid] = version.version_id
        return version

    def get_current(self, knowledge_uuid: str) -> KnowledgeVersion | None:
        vid = self._current.get(knowledge_uuid)
        return self._versions.get(vid) if vid else None

    def get_all_versions(self, knowledge_uuid: str) -> list[KnowledgeVersion]:
        ids = self._by_knowledge.get(knowledge_uuid, [])
        return sorted(
            [self._versions[vid] for vid in ids if vid in self._versions],
            key=lambda v: v.version_number)

    def get_version(self, version_id: str) -> KnowledgeVersion | None:
        return self._versions.get(version_id)

    def count(self) -> int:
        return len(self._versions)

    def knowledge_count(self) -> int:
        return len(self._by_knowledge)

    def summary(self) -> dict:
        tt: dict[str, int] = {}
        for v in self._versions.values():
            tt[v.version_type.value] = tt.get(v.version_type.value, 0) + 1
        return {"total_versions": self.count(), "knowledge_units": self.knowledge_count(),
                "by_type": tt, "current_versions": len(self._current)}
