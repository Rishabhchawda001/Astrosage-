"""
Worker Manager — Dynamic worker lifecycle and capability management.

Workers advertise capabilities, speed, resources, supported tasks,
health, and current load. Workers are generic — no fixed numbering.
"""
from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Callable, Optional

from core.taskgraph.graph import WorkerType, Task, TaskStatus


class WorkerStatus(str, Enum):
    IDLE = "idle"
    BUSY = "busy"
    FAILED = "failed"
    SHUTDOWN = "shutdown"
    DRAINING = "draining"


@dataclass
class WorkerCapabilities:
    supported_types: list[WorkerType] = field(default_factory=lambda: [WorkerType.ANY])
    max_concurrent: int = 1
    preferred_batch_size: int = 1
    gpu: bool = False
    network: bool = False


@dataclass
class WorkerMetrics:
    tasks_completed: int = 0
    tasks_failed: int = 0
    total_time: float = 0.0
    idle_time: float = 0.0
    avg_task_time: float = 0.0

    @property
    def utilization(self) -> float:
        total = self.total_time + self.idle_time
        return self.total_time / total if total > 0 else 0.0

    @property
    def success_rate(self) -> float:
        total = self.tasks_completed + self.tasks_failed
        return self.tasks_completed / total if total > 0 else 1.0


@dataclass
class Worker:
    worker_id: str = ""
    name: str = ""
    status: WorkerStatus = WorkerStatus.IDLE
    capabilities: WorkerCapabilities = field(default_factory=WorkerCapabilities)
    metrics: WorkerMetrics = field(default_factory=WorkerMetrics)
    current_task: str = ""
    health: dict[str, Any] = field(default_factory=lambda: {"status": "ok"})
    registered_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    last_heartbeat: str = ""
    current_load: float = 0.0
    metadata: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self):
        if not self.worker_id:
            self.worker_id = f"WR-{uuid.uuid4().hex[:12]}"

    @property
    def is_available(self) -> bool:
        return self.status == WorkerStatus.IDLE and self.current_load < 1.0

    def assign_task(self, task_id: str) -> None:
        self.current_task = task_id
        self.status = WorkerStatus.BUSY

    def complete_task(self, success: bool = True) -> None:
        self.current_task = ""
        self.status = WorkerStatus.IDLE
        if success:
            self.metrics.tasks_completed += 1
        else:
            self.metrics.tasks_failed += 1

    def matches_task(self, task: Task) -> bool:
        return (
            WorkerType.ANY in self.capabilities.supported_types
            or task.worker_type in self.capabilities.supported_types
        )


class WorkerManager:
    """Dynamic worker pool with automatic assignment and load balancing."""

    def __init__(self):
        self._workers: dict[str, Worker] = {}
        self._task_to_worker: dict[str, str] = {}

    def register(self, worker: Worker | None = None) -> Worker:
        if worker is None:
            worker = Worker()
        self._workers[worker.worker_id] = worker
        return worker

    def unregister(self, worker_id: str) -> bool:
        if worker_id in self._workers:
            del self._workers[worker_id]
            return True
        return False

    def get_worker(self, worker_id: str) -> Optional[Worker]:
        return self._workers.get(worker_id)

    def find_worker(self, task: Task) -> Optional[Worker]:
        candidates = [
            w for w in self._workers.values()
            if w.is_available and w.matches_task(task)
        ]
        if not candidates:
            return None
        candidates.sort(key=lambda w: w.current_load)
        return candidates[0]

    def assign_task(self, task: Task) -> Optional[Worker]:
        worker = self.find_worker(task)
        if worker:
            worker.assign_task(task.task_id)
            self._task_to_worker[task.task_id] = worker.worker_id
        return worker

    def complete_task(self, task_id: str, success: bool = True) -> None:
        worker_id = self._task_to_worker.pop(task_id, None)
        if worker_id and worker_id in self._workers:
            self._workers[worker_id].complete_task(success)

    def get_idle_workers(self) -> list[Worker]:
        return [w for w in self._workers.values() if w.is_available]

    def get_busy_workers(self) -> list[Worker]:
        return [w for w in self._workers.values() if w.status == WorkerStatus.BUSY]

    def get_worker_for_task(self, task_id: str) -> Optional[Worker]:
        wid = self._task_to_worker.get(task_id)
        return self._workers.get(wid) if wid else None

    def count(self) -> int:
        return len(self._workers)

    def summary(self) -> dict:
        status_counts: dict[str, int] = {}
        for w in self._workers.values():
            status_counts[w.status.value] = status_counts.get(w.status.value, 0) + 1
        return {
            "total_workers": self.count(),
            "idle": status_counts.get("idle", 0),
            "busy": status_counts.get("busy", 0),
            "by_status": status_counts,
        }
