"""
Planner Engine — Automatic task decomposition and execution graph generation.

Detects independent work, estimates execution cost, memory, CPU, IO, network.
Generates execution graph from phase description.
"""
from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any

from core.taskgraph.graph import TaskGraph, Task, TaskPriority, WorkerType


@dataclass
class WorkPackage:
    """A discrete work package identified by the planner."""
    package_id: str = ""
    name: str = ""
    description: str = ""
    estimated_tasks: int = 0
    dependencies: list[str] = field(default_factory=list)
    worker_type: WorkerType = WorkerType.ANY
    estimated_time: float = 0.0
    estimated_cpu: float = 0.0
    estimated_memory: float = 0.0
    risk: float = 0.0

    def __post_init__(self):
        if not self.package_id:
            self.package_id = f"WP-{uuid.uuid4().hex[:12]}"


class PlannerEngine:
    """
    Automatic planner that decomposes phases into executable task graphs.

    Analyzes dependencies, estimates costs, and produces optimized execution plans.
    """

    def __init__(self):
        self._packages: dict[str, WorkPackage] = {}
        self._plans: dict[str, TaskGraph] = {}

    def create_package(self, **kwargs) -> WorkPackage:
        pkg = WorkPackage(**kwargs)
        self._packages[pkg.package_id] = pkg
        return pkg

    def plan_phase(self, phase_name: str, packages: list[WorkPackage]) -> TaskGraph:
        """Generate a task graph from work packages."""
        graph = TaskGraph()
        pkg_to_task: dict[str, str] = {}
        for pkg in packages:
            task = Task(
                name=pkg.name,
                description=pkg.description,
                worker_type=pkg.worker_type,
                estimated_time=pkg.estimated_time,
                estimated_cpu=pkg.estimated_cpu,
                estimated_memory=pkg.estimated_memory,
                risk=pkg.risk,
                dependencies=[],
            )
            graph.add_task(task)
            pkg_to_task[pkg.package_id] = task.task_id

        # Wire dependencies
        for pkg in packages:
            task_id = pkg_to_task[pkg.package_id]
            for dep_id in pkg.dependencies:
                if dep_id in pkg_to_task:
                    graph.add_dependency(task_id, pkg_to_task[dep_id])

        self._plans[phase_name] = graph
        return graph

    def analyze_dependencies(self, graph: TaskGraph) -> dict[str, Any]:
        independent_sets = graph.get_independent_sets()
        critical_path = graph.get_critical_path()
        return {
            "total_tasks": graph.count(),
            "independent_levels": len(independent_sets),
            "max_parallelism": max((len(s) for s in independent_sets), default=0),
            "critical_path_length": len(critical_path),
            "has_cycle": graph.has_cycle(),
        }

    def estimate_total_time(self, graph: TaskGraph) -> float:
        levels = graph.get_independent_sets()
        total = 0.0
        for level in levels:
            max_time = 0.0
            for tid in level:
                task = graph.get_task(tid)
                if task:
                    max_time = max(max_time, task.estimated_time)
            total += max_time
        return total

    def estimate_total_cost(self, graph: TaskGraph) -> float:
        return sum(t.estimated_cost for t in graph.tasks())

    def get_plan(self, phase_name: str) -> TaskGraph | None:
        return self._plans.get(phase_name)

    def summary(self) -> dict:
        return {
            "total_packages": len(self._packages),
            "total_plans": len(self._plans),
        }
