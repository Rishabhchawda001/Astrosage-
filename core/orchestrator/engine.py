"""
Orchestrator Engine — Self-orchestrating execution engine for AstroSage.

Ties together all APEE v2 subsystems: task graph, scheduler, planner,
executor, workers, validators, checkpoints, progress, resources, events, queues.
"""
from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Callable, Optional

from core.taskgraph.graph import TaskGraph, Task, TaskStatus, TaskPriority
from core.scheduler.engine import SmartScheduler, SchedulerMode
from core.planner.engine import PlannerEngine, WorkPackage
from core.executor.engine import ExecutorEngine, ExecutionMode, ExecutionResult
from core.workers.manager import WorkerManager, Worker
from core.validators.registry import ValidatorRegistry, Validator, ValidationCategory, ValidationResult
from core.checkpoints.engine import CheckpointEngine, Checkpoint
from core.progress.tracker import ProgressTracker
from core.resources.manager import ResourceManager
from core.events.bus import EventBus, EventType, Event
from core.queues.manager import QueueManager


class OrchestratorStatus(str, Enum):
    IDLE = "idle"
    PLANNING = "planning"
    EXECUTING = "executing"
    VALIDATING = "validating"
    CHECKPOINTING = "checkpointing"
    COMPLETED = "completed"
    FAILED = "failed"
    PAUSED = "paused"


@dataclass
class PhaseExecution:
    """Complete execution record for a phase."""
    phase_id: str = ""
    phase_name: str = ""
    status: OrchestratorStatus = OrchestratorStatus.IDLE
    task_count: int = 0
    completed: int = 0
    failed: int = 0
    started_at: str = ""
    completed_at: str = ""
    duration: float = 0.0
    results: dict[str, ExecutionResult] = field(default_factory=dict)

    def __post_init__(self):
        if not self.phase_id:
            self.phase_id = f"PE-{uuid.uuid4().hex[:12]}"


class OrchestratorEngine:
    """
    Production orchestrator that automatically plans, schedules,
    executes, validates, and checkpoints phase work.
    """

    def __init__(self, mode: SchedulerMode = SchedulerMode.ADAPTIVE):
        self.event_bus = EventBus()
        self.worker_manager = WorkerManager()
        self.validator_registry = ValidatorRegistry()
        self.scheduler = SmartScheduler(mode)
        self.planner = PlannerEngine()
        self.executor = ExecutorEngine(self.worker_manager, self.event_bus)
        self.checkpoint_engine = CheckpointEngine()
        self.progress = ProgressTracker()
        self.resource_manager = ResourceManager()
        self.queue_manager = QueueManager()
        self._executions: dict[str, PhaseExecution] = {}
        self._current_graph: TaskGraph | None = None

    def plan_phase(self, phase_name: str, packages: list[WorkPackage]) -> TaskGraph:
        graph = self.planner.plan_phase(phase_name, packages)
        self._current_graph = graph
        self.event_bus.emit(EventType.PHASE_STARTED, source="orchestrator", data={"phase": phase_name})
        return graph

    def execute_phase(self, phase_name: str, graph: TaskGraph | None = None) -> PhaseExecution:
        graph = graph or self._current_graph
        if not graph:
            raise ValueError("No task graph available")

        execution = PhaseExecution(
            phase_name=phase_name,
            task_count=graph.count(),
            started_at=datetime.now(timezone.utc).isoformat(),
        )
        self._executions[execution.phase_id] = execution
        self.progress.start()

        # Schedule initial tasks
        self.scheduler.schedule(graph)

        # Execute until all tasks are done
        max_iterations = graph.count() * 10
        iteration = 0
        while iteration < max_iterations:
            iteration += 1
            task_id = self.scheduler.get_next_task()
            if not task_id:
                if self._all_tasks_done(graph):
                    break
                continue

            task = graph.get_task(task_id)
            if not task:
                continue

            result = self.executor.execute_task(task)
            execution.results[task_id] = result

            if result.success:
                execution.completed += 1
                newly_ready = self.scheduler.on_task_completed(graph, task_id)
            else:
                execution.failed += 1
                self.progress.record_retry()
                self.scheduler.on_task_failed(graph, task_id, result.error)

            # Record progress
            self.progress.snapshot(
                total=graph.count(),
                completed=execution.completed,
                failed=execution.failed,
                running=0,
                pending=graph.count() - execution.completed - execution.failed,
                worker_count=self.worker_manager.count(),
                idle_workers=len(self.worker_manager.get_idle_workers()),
            )

        execution.completed_at = datetime.now(timezone.utc).isoformat()
        execution.status = OrchestratorStatus.COMPLETED
        self.event_bus.emit(EventType.PHASE_COMPLETED, source="orchestrator", data={"phase": phase_name})
        return execution

    def _all_tasks_done(self, graph: TaskGraph) -> bool:
        for task in graph.tasks():
            if task.status not in (TaskStatus.COMPLETED, TaskStatus.CANCELLED, TaskStatus.FAILED):
                return False
        return True

    def save_checkpoint(self) -> str:
        if not self._current_graph:
            return ""
        cp = self.checkpoint_engine.create_from_graph(
            phase="current",
            tasks=self._current_graph.tasks(),
            queue=self.scheduler.get_queue(),
        )
        self.progress.record_checkpoint()
        self.event_bus.emit(EventType.CHECKPOINT_CREATED, source="orchestrator", data={"checkpoint": cp.checkpoint_id})
        return cp.checkpoint_id

    def register_validator(self, category: ValidationCategory, name: str = "") -> str:
        v = Validator(name=name or category.value, category=category)
        return self.validator_registry.register(v)

    def run_validators(self) -> dict[str, bool]:
        results = self.validator_registry.run_all()
        return {vid: r.result == ValidationResult.PASSED for vid, r in results.items()}

    def get_execution(self, phase_id: str) -> PhaseExecution | None:
        return self._executions.get(phase_id)

    def summary(self) -> dict:
        return {
            "orchestrator_status": OrchestratorStatus.EXECUTING.value,
            "executions": len(self._executions),
            "workers": self.worker_manager.summary(),
            "validators": self.validator_registry.summary(),
            "scheduler": self.scheduler.summary(),
            "checkpoints": self.checkpoint_engine.summary(),
            "events": self.event_bus.summary(),
            "progress": self.progress.summary(),
        }
