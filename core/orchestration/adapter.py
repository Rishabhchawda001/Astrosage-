"""
Orca Orchestration Adapter — Maps APEE workers onto Orca.
Never replaces APEE. Only adds compatibility.
"""
from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Optional


class OrcaWorkerType(str, Enum):
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
    VALIDATION = "validation"


class OrcaWorkerStatus(str, Enum):
    IDLE = "idle"
    BUSY = "busy"
    STOPPED = "stopped"


@dataclass
class OrcaWorker:
    worker_id: str = ""
    worker_type: OrcaWorkerType = OrcaWorkerType.RESEARCH
    status: OrcaWorkerStatus = OrcaWorkerStatus.IDLE
    capabilities: list[str] = field(default_factory=list)
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    def __post_init__(self):
        if not self.worker_id: self.worker_id = f"OW-{uuid.uuid4().hex[:8]}"


class OrcaAdapter:
    """
    Optional Orca compatibility adapter. Disabled by default.
    Maps APEE concepts to Orca concepts without replacing APEE.
    """
    def __init__(self, enabled: bool = False):
        self.enabled = enabled
        self._workers: dict[str, OrcaWorker] = {}
        self._task_queue: list[dict[str, Any]] = []

    def create_worker(self, worker_type: OrcaWorkerType, capabilities: list[str] | None = None) -> OrcaWorker:
        w = OrcaWorker(worker_type=worker_type, capabilities=capabilities or [])
        self._workers[w.worker_id] = w
        return w

    def shutdown_worker(self, worker_id: str) -> bool:
        w = self._workers.get(worker_id)
        if w:
            w.status = OrcaWorkerStatus.STOPPED
            return True
        return False

    def submit_task(self, task: dict[str, Any]) -> str:
        task_id = f"OT-{uuid.uuid4().hex[:8]}"
        self._task_queue.append({"task_id": task_id, **task})
        return task_id

    def get_idle_workers(self) -> list[OrcaWorker]:
        return [w for w in self._workers.values() if w.status == OrcaWorkerStatus.IDLE]

    def count(self) -> int: return len(self._workers)

    def summary(self) -> dict:
        tc: dict[str, int] = {}
        for w in self._workers.values(): tc[w.worker_type.value] = tc.get(w.worker_type.value, 0) + 1
        return {"enabled": self.enabled, "workers": self.count(), "queue": len(self._task_queue), "by_type": tc}
