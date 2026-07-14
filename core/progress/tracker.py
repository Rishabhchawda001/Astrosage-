"""
Progress Tracker — Real-time execution progress monitoring.

Tracks task completion, worker utilization, parallel efficiency,
retry counts, and checkpoint frequency.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any


@dataclass
class ProgressSnapshot:
    """A point-in-time snapshot of execution progress."""
    total_tasks: int = 0
    completed_tasks: int = 0
    failed_tasks: int = 0
    running_tasks: int = 0
    pending_tasks: int = 0
    worker_count: int = 0
    idle_workers: int = 0
    utilization: float = 0.0
    parallel_efficiency: float = 0.0
    retry_count: int = 0
    checkpoint_count: int = 0
    elapsed_time: float = 0.0
    estimated_remaining: float = 0.0
    timestamp: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

    @property
    def completion_pct(self) -> float:
        return (self.completed_tasks / self.total_tasks * 100) if self.total_tasks > 0 else 0.0

    @property
    def failure_rate(self) -> float:
        return (self.failed_tasks / max(self.total_tasks, 1))


class ProgressTracker:
    """Tracks and reports execution progress."""

    def __init__(self):
        self._snapshots: list[ProgressSnapshot] = []
        self._start_time: str = ""
        self._retry_count: int = 0
        self._checkpoint_count: int = 0

    def start(self) -> None:
        self._start_time = datetime.now(timezone.utc).isoformat()

    def record_retry(self) -> None:
        self._retry_count += 1

    def record_checkpoint(self) -> None:
        self._checkpoint_count += 1

    def snapshot(self, total: int, completed: int, failed: int, running: int,
                 pending: int, worker_count: int, idle_workers: int) -> ProgressSnapshot:
        snap = ProgressSnapshot(
            total_tasks=total,
            completed_tasks=completed,
            failed_tasks=failed,
            running_tasks=running,
            pending_tasks=pending,
            worker_count=worker_count,
            idle_workers=idle_workers,
            utilization=(worker_count - idle_workers) / max(worker_count, 1),
            retry_count=self._retry_count,
            checkpoint_count=self._checkpoint_count,
        )
        self._snapshots.append(snap)
        return snap

    def get_latest(self) -> ProgressSnapshot | None:
        return self._snapshots[-1] if self._snapshots else None

    def get_history(self) -> list[ProgressSnapshot]:
        return list(self._snapshots)

    def summary(self) -> dict:
        latest = self.get_latest()
        return {
            "snapshots": len(self._snapshots),
            "retry_count": self._retry_count,
            "checkpoint_count": self._checkpoint_count,
            "latest_pct": latest.completion_pct if latest else 0.0,
            "latest_utilization": latest.utilization if latest else 0.0,
        }
