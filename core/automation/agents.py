"""
Agency Agents — Specialist agent plugins for AstroSage.

Each agent is a plugin. Independently replaceable.
"""
from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Optional


class AgentType(str, Enum):
    RESEARCH = "research"
    OCR = "ocr"
    VERIFICATION = "verification"
    TRANSLATION = "translation"
    METADATA = "metadata"
    CITATION = "citation"
    EVIDENCE = "evidence"
    KNOWLEDGE_GRAPH = "knowledge_graph"
    TESTING = "testing"
    DOCUMENTATION = "documentation"
    SECURITY = "security"
    PERFORMANCE = "performance"


@dataclass
class AgentConfig:
    agent_id: str = ""
    agent_type: AgentType = AgentType.RESEARCH
    name: str = ""
    description: str = ""
    enabled: bool = True
    capabilities: list[str] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    def __post_init__(self):
        if not self.agent_id: self.agent_id = f"AG-{uuid.uuid4().hex[:8]}"


class AgencyRegistry:
    """Registry of specialist agents. Each is a plugin."""

    def __init__(self):
        self._agents: dict[str, AgentConfig] = {}
        self._by_type: dict[str, list[str]] = {}

    def register(self, config: AgentConfig) -> str:
        self._agents[config.agent_id] = config
        self._by_type.setdefault(config.agent_type.value, []).append(config.agent_id)
        return config.agent_id

    def get(self, agent_id: str) -> Optional[AgentConfig]:
        return self._agents.get(agent_id)

    def get_by_type(self, agent_type: AgentType) -> list[AgentConfig]:
        ids = self._by_type.get(agent_type.value, [])
        return [self._agents[aid] for aid in ids if aid in self._agents]

    def count(self) -> int: return len(self._agents)

    def summary(self) -> dict:
        tc: dict[str, int] = {}
        for a in self._agents.values(): tc[a.agent_type.value] = tc.get(a.agent_type.value, 0) + 1
        return {"total": self.count(), "by_type": tc}
