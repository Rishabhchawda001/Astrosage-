"""
Observability — Dashboard data for system monitoring.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any


@dataclass
class ObservabilitySnapshot:
    timestamp: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    running_workers: int = 0
    parallel_tasks: int = 0
    queue_size: int = 0
    provider_health: dict[str, Any] = field(default_factory=dict)
    workflow_progress: dict[str, Any] = field(default_factory=dict)
    failed_tasks: int = 0
    validation_failures: int = 0
    evidence_confidence_avg: float = 0.0
    memory_usage: dict[str, Any] = field(default_factory=dict)


class ObservabilityEngine:
    def __init__(self):
        self._snapshots: list[ObservabilitySnapshot] = []

    def record(self, **kwargs) -> ObservabilitySnapshot:
        snap = ObservabilitySnapshot(**kwargs)
        self._snapshots.append(snap)
        return snap

    def get_latest(self) -> ObservabilitySnapshot | None:
        return self._snapshots[-1] if self._snapshots else None

    def get_history(self, limit: int = 10) -> list[ObservabilitySnapshot]:
        return self._snapshots[-limit:]

    def count(self) -> int: return len(self._snapshots)

    def summary(self) -> dict:
        return {"snapshots": self.count()}
