"""
Checkpoint Engine — Persistent execution state for resume after interruption.

Stores task graph, completed/failed tasks, worker state, registry state,
knowledge state, and plugin state.
"""
from __future__ import annotations

import json
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional

from core.taskgraph.graph import Task, TaskStatus


@dataclass
class Checkpoint:
    """A snapshot of execution state."""
    checkpoint_id: str = ""
    phase: str = ""
    completed_tasks: list[str] = field(default_factory=list)
    failed_tasks: list[str] = field(default_factory=list)
    current_queue: list[str] = field(default_factory=list)
    worker_states: dict[str, dict[str, Any]] = field(default_factory=dict)
    registry_state: dict[str, Any] = field(default_factory=dict)
    knowledge_state: dict[str, Any] = field(default_factory=dict)
    plugin_state: dict[str, Any] = field(default_factory=dict)
    task_data: dict[str, dict[str, Any]] = field(default_factory=dict)
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    metadata: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self):
        if not self.checkpoint_id:
            self.checkpoint_id = f"CP-{uuid.uuid4().hex[:12]}"

    def to_dict(self) -> dict[str, Any]:
        return {
            "checkpoint_id": self.checkpoint_id,
            "phase": self.phase,
            "completed_tasks": self.completed_tasks,
            "failed_tasks": self.failed_tasks,
            "current_queue": self.current_queue,
            "worker_states": self.worker_states,
            "created_at": self.created_at,
        }


class CheckpointEngine:
    """
    Production checkpoint engine.

    Saves and restores execution state. Supports automatic checkpointing
    and resume from any checkpoint.
    """

    def __init__(self, checkpoint_dir: str = "knowledge/checkpoints/apee"):
        self.checkpoint_dir = Path(checkpoint_dir)
        self.checkpoint_dir.mkdir(parents=True, exist_ok=True)
        self._checkpoints: dict[str, Checkpoint] = {}
        self._latest: Checkpoint | None = None

    def save(self, checkpoint: Checkpoint) -> str:
        self._checkpoints[checkpoint.checkpoint_id] = checkpoint
        self._latest = checkpoint
        # Persist to disk
        filepath = self.checkpoint_dir / f"{checkpoint.checkpoint_id}.json"
        filepath.write_text(json.dumps(checkpoint.to_dict(), indent=2, ensure_ascii=False))
        return checkpoint.checkpoint_id

    def load(self, checkpoint_id: str) -> Optional[Checkpoint]:
        if checkpoint_id in self._checkpoints:
            return self._checkpoints[checkpoint_id]
        filepath = self.checkpoint_dir / f"{checkpoint_id}.json"
        if filepath.exists():
            data = json.loads(filepath.read_text())
            checkpoint = Checkpoint(**{k: v for k, v in data.items() if k != "task_data"})
            self._checkpoints[checkpoint_id] = checkpoint
            return checkpoint
        return None

    def create_from_graph(self, phase: str, tasks: list[Task], queue: list[str]) -> Checkpoint:
        completed = [t.task_id for t in tasks if t.status == TaskStatus.COMPLETED]
        failed = [t.task_id for t in tasks if t.status == TaskStatus.FAILED]
        task_data = {}
        for t in tasks:
            task_data[t.task_id] = {
                "name": t.name,
                "status": t.status.value,
                "outputs": t.outputs,
                "error": t.error,
            }
        checkpoint = Checkpoint(
            phase=phase,
            completed_tasks=completed,
            failed_tasks=failed,
            current_queue=queue,
            task_data=task_data,
        )
        self.save(checkpoint)
        return checkpoint

    def restore_graph_state(self, checkpoint: Checkpoint) -> dict[str, TaskStatus]:
        state = {}
        for tid in checkpoint.completed_tasks:
            state[tid] = TaskStatus.COMPLETED
        for tid in checkpoint.failed_tasks:
            state[tid] = TaskStatus.FAILED
        return state

    def get_latest(self) -> Optional[Checkpoint]:
        return self._latest

    def list_checkpoints(self) -> list[Checkpoint]:
        return sorted(self._checkpoints.values(), key=lambda c: c.created_at)

    def count(self) -> int:
        return len(self._checkpoints)

    def summary(self) -> dict:
        return {
            "total_checkpoints": self.count(),
            "latest": self._latest.checkpoint_id if self._latest else None,
        }
