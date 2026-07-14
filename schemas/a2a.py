"""A2A Schemas — Agent-to-Agent communication schemas."""
from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Optional


class AgentStatus(str, Enum):
    IDLE = "idle"
    BUSY = "busy"
    ERROR = "error"
    OFFLINE = "offline"


class TaskStatus(str, Enum):
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


@dataclass
class AgentIdentity:
    agent_id: str = ""
    name: str = ""
    version: str = ""
    capabilities: list[str] = field(default_factory=list)
    status: AgentStatus = AgentStatus.IDLE


@dataclass
class AgentRegistry:
    agents: list[AgentIdentity] = field(default_factory=list)


@dataclass
class TaskRequest:
    task_id: str = ""
    from_agent: str = ""
    to_agent: str = ""
    task_type: str = ""
    payload: dict = field(default_factory=dict)
    priority: int = 5
    timeout_seconds: int = 300


@dataclass
class TaskResponse:
    task_id: str = ""
    status: TaskStatus = TaskStatus.PENDING
    result: Any = None
    error: str = ""


@dataclass
class DelegationSchema:
    delegator_agent: str = ""
    delegate_agent: str = ""
    task_type: str = ""
    reason: str = ""


@dataclass
class Heartbeat:
    agent_id: str = ""
    timestamp: str = ""
    status: AgentStatus = AgentStatus.IDLE
    active_tasks: int = 0
