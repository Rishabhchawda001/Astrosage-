"""
Task Graph — DAG representation of phase work packages.

Every phase is a directed acyclic graph of tasks with dependencies,
priorities, cost estimates, and validation requirements.
"""
from __future__ import annotations

import uuid
from collections import defaultdict, deque
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Optional


class TaskStatus(str, Enum):
    PENDING = "pending"
    READY = "ready"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    BLOCKED = "blocked"
    RETRYING = "retrying"


class TaskPriority(str, Enum):
    CRITICAL = "critical"
    HIGH = "high"
    NORMAL = "normal"
    LOW = "low"


class WorkerType(str, Enum):
    ARCHITECTURE = "architecture"
    CORE_ENGINE = "core_engine"
    PLUGIN = "plugin"
    SKILLS = "skills"
    REGISTRIES = "registries"
    INTERFACES = "interfaces"
    ADAPTERS = "adapters"
    TESTING = "testing"
    PERFORMANCE = "performance"
    GIT = "git"
    VALIDATION = "validation"
    ANY = "any"


@dataclass
class Task:
    """A single unit of work in the task graph."""
    task_id: str = ""
    name: str = ""
    description: str = ""
    priority: TaskPriority = TaskPriority.NORMAL
    status: TaskStatus = TaskStatus.PENDING
    dependencies: list[str] = field(default_factory=list)
    dependents: list[str] = field(default_factory=list)
    worker_type: WorkerType = WorkerType.ANY
    validation_requirements: list[str] = field(default_factory=list)
    retry_policy: dict[str, Any] = field(default_factory=lambda: {"max_retries": 3, "backoff": 1.0})
    checkpoint_id: str = ""
    inputs: dict[str, Any] = field(default_factory=dict)
    outputs: dict[str, Any] = field(default_factory=dict)
    estimated_cost: float = 0.0
    estimated_time: float = 0.0
    estimated_cpu: float = 0.0
    estimated_memory: float = 0.0
    estimated_io: float = 0.0
    risk: float = 0.0
    retry_count: int = 0
    actual_time: float = 0.0
    assigned_worker: str = ""
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    started_at: str = ""
    completed_at: str = ""
    error: str = ""
    metadata: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self):
        if not self.task_id:
            self.task_id = f"TK-{uuid.uuid4().hex[:12]}"

    @property
    def can_retry(self) -> bool:
        return self.retry_count < self.retry_policy.get("max_retries", 3)

    @property
    def is_terminal(self) -> bool:
        return self.status in (TaskStatus.COMPLETED, TaskStatus.CANCELLED)

    @property
    def is_active(self) -> bool:
        return self.status == TaskStatus.RUNNING


class TaskGraph:
    """
    Directed acyclic graph for phase execution planning.

    Supports topological ordering, dependency analysis, critical path,
    cycle detection, and dynamic task management.
    """

    def __init__(self):
        self._tasks: dict[str, Task] = {}
        self._adjacency: dict[str, set[str]] = defaultdict(set)
        self._reverse: dict[str, set[str]] = defaultdict(set)

    def add_task(self, task: Task) -> str:
        self._tasks[task.task_id] = task
        for dep_id in task.dependencies:
            self._adjacency[dep_id].add(task.task_id)
            self._reverse[task.task_id].add(dep_id)
            if dep_id in self._tasks:
                self._tasks[dep_id].dependents.append(task.task_id)
        return task.task_id

    def get_task(self, task_id: str) -> Optional[Task]:
        return self._tasks.get(task_id)

    def add_dependency(self, task_id: str, depends_on: str) -> None:
        if task_id in self._tasks:
            self._tasks[task_id].dependencies.append(depends_on)
            self._adjacency[depends_on].add(task_id)
            self._reverse[task_id].add(depends_on)
            if depends_on in self._tasks:
                self._tasks[depends_on].dependents.append(task_id)

    def has_cycle(self) -> bool:
        WHITE, GRAY, BLACK = 0, 1, 2
        color: dict[str, int] = {tid: WHITE for tid in self._tasks}

        def dfs(node: str) -> bool:
            color[node] = GRAY
            for neighbor in self._adjacency.get(node, set()):
                if neighbor in color:
                    if color[neighbor] == GRAY:
                        return True
                    if color[neighbor] == WHITE and dfs(neighbor):
                        return True
            color[node] = BLACK
            return False

        for tid in self._tasks:
            if color.get(tid, WHITE) == WHITE:
                if dfs(tid):
                    return True
        return False

    def topological_sort(self) -> list[str]:
        in_degree: dict[str, int] = {tid: 0 for tid in self._tasks}
        for tid, deps in self._reverse.items():
            in_degree[tid] = len(deps)

        queue = deque([tid for tid, deg in in_degree.items() if deg == 0])
        result = []
        while queue:
            node = queue.popleft()
            result.append(node)
            for neighbor in self._adjacency.get(node, set()):
                in_degree[neighbor] -= 1
                if in_degree[neighbor] == 0:
                    queue.append(neighbor)
        return result

    def get_ready_tasks(self) -> list[Task]:
        ready = []
        for task in self._tasks.values():
            if task.status != TaskStatus.PENDING:
                continue
            deps_met = all(
                self._tasks[d].status == TaskStatus.COMPLETED
                for d in task.dependencies if d in self._tasks
            )
            if deps_met:
                ready.append(task)
        ready.sort(key=lambda t: (
            {"critical": 0, "high": 1, "normal": 2, "low": 3}.get(
                t.priority.value if hasattr(t.priority, 'value') else str(t.priority), 2
            ),
            -t.estimated_cost,
        ))
        return ready

    def get_critical_path(self) -> list[str]:
        order = self.topological_sort()
        dist: dict[str, float] = {tid: 0.0 for tid in order}
        prev: dict[str, str] = {}
        for tid in order:
            for dep in self._reverse.get(tid, set()):
                new_dist = dist.get(dep, 0) + self._tasks.get(dep, Task()).estimated_time
                if new_dist > dist.get(tid, 0):
                    dist[tid] = new_dist
                    prev[tid] = dep
        if not dist:
            return []
        end = max(dist, key=dist.get)
        path = [end]
        while end in prev:
            end = prev[end]
            path.append(end)
        path.reverse()
        return path

    def get_independent_sets(self) -> list[list[str]]:
        order = self.topological_sort()
        levels: list[list[str]] = []
        level_map: dict[str, int] = {}
        for tid in order:
            max_dep_level = -1
            for dep in self._reverse.get(tid, set()):
                if dep in level_map:
                    max_dep_level = max(max_dep_level, level_map[dep])
            level = max_dep_level + 1
            level_map[tid] = level
            while len(levels) <= level:
                levels.append([])
            levels[level].append(tid)
        return levels

    def mark_completed(self, task_id: str) -> None:
        if task_id in self._tasks:
            self._tasks[task_id].status = TaskStatus.COMPLETED

    def mark_failed(self, task_id: str, error: str = "") -> None:
        if task_id in self._tasks:
            self._tasks[task_id].status = TaskStatus.FAILED
            self._tasks[task_id].error = error

    def tasks(self) -> list[Task]:
        return list(self._tasks.values())

    def count(self) -> int:
        return len(self._tasks)

    def summary(self) -> dict:
        status_counts: dict[str, int] = {}
        for t in self._tasks.values():
            status_counts[t.status.value] = status_counts.get(t.status.value, 0) + 1
        return {
            "total_tasks": self.count(),
            "by_status": status_counts,
            "has_cycle": self.has_cycle(),
            "critical_path_length": len(self.get_critical_path()),
        }
