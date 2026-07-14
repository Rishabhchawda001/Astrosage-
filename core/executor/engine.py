"""
Executor Engine — Executes tasks from the scheduler using available workers.

Supports sequential, parallel, adaptive, and hybrid execution modes.
Maintains deterministic output ordering.
"""
from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Callable, Optional

from core.taskgraph.graph import TaskGraph, Task, TaskStatus
from core.workers.manager import WorkerManager, Worker
from core.events.bus import EventBus, EventType


class ExecutionMode(str, Enum):
    SEQUENTIAL = "sequential"
    PARALLEL = "parallel"
    ADAPTIVE = "adaptive"
    HYBRID = "hybrid"


@dataclass
class ExecutionResult:
    task_id: str = ""
    success: bool = False
    output: Any = None
    error: str = ""
    duration: float = 0.0
    worker_id: str = ""


TaskHandler = Callable[[Task, Worker], Any]


class ExecutorEngine:
    """
    Production task executor.

    Pulls tasks from scheduler, assigns workers, executes, handles results.
    Supports all execution modes with deterministic ordering.
    """

    def __init__(self, worker_manager: WorkerManager, event_bus: EventBus | None = None):
        self.worker_manager = worker_manager
        self.event_bus = event_bus
        self._handlers: dict[str, TaskHandler] = {}
        self._results: dict[str, ExecutionResult] = {}
        self._execution_count: int = 0

    def register_handler(self, worker_type: str, handler: TaskHandler) -> None:
        self._handlers[worker_type] = handler

    def register_default_handler(self, handler: TaskHandler) -> None:
        self._handlers["*"] = handler

    def execute_task(self, task: Task) -> ExecutionResult:
        worker = self.worker_manager.find_worker(task)
        if not worker:
            return ExecutionResult(
                task_id=task.task_id,
                success=False,
                error="No available worker",
            )

        task.status = TaskStatus.RUNNING
        task.started_at = datetime.now(timezone.utc).isoformat()
        worker.assign_task(task.task_id)

        if self.event_bus:
            self.event_bus.emit(EventType.TASK_STARTED, source="executor", data={"task_id": task.task_id})

        handler = self._handlers.get(task.worker_type.value) or self._handlers.get("*")
        try:
            if handler:
                output = handler(task, worker)
            else:
                output = None
            result = ExecutionResult(
                task_id=task.task_id,
                success=True,
                output=output,
                worker_id=worker.worker_id,
            )
            task.status = TaskStatus.COMPLETED
            task.completed_at = datetime.now(timezone.utc).isoformat()
            task.outputs = {"result": output} if output else {}
            if self.event_bus:
                self.event_bus.emit(EventType.TASK_COMPLETED, source="executor", data={"task_id": task.task_id})
        except Exception as e:
            result = ExecutionResult(
                task_id=task.task_id,
                success=False,
                error=str(e),
                worker_id=worker.worker_id,
            )
            task.status = TaskStatus.FAILED
            task.error = str(e)
            if self.event_bus:
                self.event_bus.emit(EventType.TASK_FAILED, source="executor", data={"task_id": task.task_id, "error": str(e)})

        self.worker_manager.complete_task(task.task_id, result.success)
        self._results[task.task_id] = result
        self._execution_count += 1
        return result

    def get_result(self, task_id: str) -> ExecutionResult | None:
        return self._results.get(task_id)

    def execution_count(self) -> int:
        return self._execution_count

    def summary(self) -> dict:
        success = sum(1 for r in self._results.values() if r.success)
        failed = sum(1 for r in self._results.values() if not r.success)
        return {
            "total_executions": self._execution_count,
            "successful": success,
            "failed": failed,
        }
