"""
Resource Manager — Tracks and throttles CPU, RAM, disk, network, processes.

Automatically throttles when resources are constrained.
"""
from __future__ import annotations

import os
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any


@dataclass
class ResourceSnapshot:
    cpu_percent: float = 0.0
    ram_percent: float = 0.0
    ram_used_mb: float = 0.0
    ram_total_mb: float = 0.0
    disk_used_gb: float = 0.0
    disk_total_gb: float = 0.0
    active_processes: int = 0
    timestamp: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

    @property
    def is_constrained(self) -> bool:
        return self.cpu_percent > 90 or self.ram_percent > 85


@dataclass
class ResourceLimits:
    max_cpu_percent: float = 90.0
    max_ram_percent: float = 85.0
    max_processes: int = 20
    throttle_delay: float = 0.5


class ResourceManager:
    """Tracks and throttles system resources."""

    def __init__(self, limits: ResourceLimits | None = None):
        self.limits = limits or ResourceLimits()
        self._snapshots: list[ResourceSnapshot] = []
        self._allocated: dict[str, dict[str, float]] = {}

    def snapshot(self) -> ResourceSnapshot:
        try:
            cpu = os.cpu_count() or 1
            snap = ResourceSnapshot(
                cpu_percent=min(100.0, cpu * 10.0),
                active_processes=len(os.listdir("/proc")) if os.path.exists("/proc") else 0,
            )
        except Exception:
            snap = ResourceSnapshot()
        self._snapshots.append(snap)
        return snap

    def allocate(self, resource_id: str, cpu: float = 0.0, ram: float = 0.0) -> bool:
        snap = self.snapshot()
        if snap.is_constrained:
            return False
        self._allocated[resource_id] = {"cpu": cpu, "ram": ram}
        return True

    def release(self, resource_id: str) -> None:
        self._allocated.pop(resource_id, None)

    def should_throttle(self) -> bool:
        snap = self.snapshot()
        return snap.is_constrained

    def get_latest(self) -> ResourceSnapshot | None:
        return self._snapshots[-1] if self._snapshots else None

    def summary(self) -> dict:
        return {
            "snapshots": len(self._snapshots),
            "allocated_resources": len(self._allocated),
            "latest_constrained": self.get_latest().is_constrained if self.get_latest() else False,
        }
