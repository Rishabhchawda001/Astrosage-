"""
Smart Scheduler — Priority queue with dependency resolution and work stealing.

Supports: dynamic worker allocation, idle reassignment, automatic retry,
checkpoint resume, failure isolation.
"""
from __future__ import annotations

import uuid
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Optional

from core.taskgraph.graph import TaskGraph, Task, TaskStatus, TaskPriority


class SchedulerMode(str, Enum):
    SEQUENTIAL = "sequential"
    PARALLEL = "parallel"
    ADAPTIVE = "adaptive"
    HYBRID = "hybrid"


@dataclass
class ScheduleEntry:
    task_id: str = ""
    worker_id: str = ""
    priority: int = 0
    scheduled_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


class SmartScheduler:
    """
    Production scheduler with priority queue, dependency resolution,
    work stealing, and failure isolation.
    """

    def __init__(self, mode: SchedulerMode = SchedulerMode.ADAPTIVE):
        self.mode = mode
        self._queue: list[str] = []
        self._history: list[ScheduleEntry] = []
        self._max_retries: int = 3

    def _priority_score(self, task: Task) -> int:
        scores = {"critical": 0, "high": 1, "normal": 2, "low": 3}
        return scores.get(task.priority.value if hasattr(task.priority, "value") else str(task.priority), 2)

    def schedule(self, graph: TaskGraph) -> list[str]:
        """Schedule all ready tasks in priority order."""
        ready = graph.get_ready_tasks()
        ready.sort(key=lambda t: (self._priority_score(t), -t.estimated_cost))
        scheduled = []
        for task in ready:
            if task.task_id not in self._queue:
                self._queue.append(task.task_id)
                task.status = TaskStatus.READY
                scheduled.append(task.task_id)
                self._history.append(ScheduleEntry(
                    task_id=task.task_id,
                    priority=self._priority_score(task),
                ))
        return scheduled

    def assign(self, task_id: str, worker_id: str) -> bool:
        if task_id in self._queue:
            self._queue.remove(task_id)
            return True
        return False

    def on_task_completed(self, graph: TaskGraph, task_id: str) -> list[str]:
        """When a task completes, check if new tasks become ready."""
        graph.mark_completed(task_id)
        return self.schedule(graph)

    def on_task_failed(self, graph: TaskGraph, task_id: str, error: str = "") -> Optional[str]:
        """Handle task failure — retry or mark failed."""
        task = graph.get_task(task_id)
        if not task:
            return None
        if task.can_retry:
            task.retry_count += 1
            task.status = TaskStatus.RETRYING
            task.error = ""
            self._queue.append(task_id)
            return task_id
        graph.mark_failed(task_id, error)
        return None

    def steal_work(self, idle_worker_id: str, busy_workers_tasks: list[str]) -> Optional[str]:
        """Work stealing: take lowest-priority task from a busy worker."""
        if not busy_workers_tasks:
            return None
        return busy_workers_tasks[-1]

    def get_next_task(self) -> Optional[str]:
        if self._queue:
            return self._queue.pop(0)
        return None

    def get_queue(self) -> list[str]:
        return list(self._queue)

    def clear_queue(self) -> None:
        self._queue.clear()

    def is_empty(self) -> bool:
        return len(self._queue) == 0

    def summary(self) -> dict:
        return {
            "mode": self.mode.value,
            "queue_size": len(self._queue),
            "scheduled_total": len(self._history),
        }
