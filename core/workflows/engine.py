"""
N8N Workflow Engine — Resumable workflow definitions for AstroSage.
"""
from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Callable, Optional


class WorkflowStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    PAUSED = "paused"
    COMPLETED = "completed"
    FAILED = "failed"


class StepStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"


@dataclass
class WorkflowStep:
    step_id: str = ""
    name: str = ""
    status: StepStatus = StepStatus.PENDING
    inputs: dict[str, Any] = field(default_factory=dict)
    outputs: dict[str, Any] = field(default_factory=dict)
    error: str = ""
    started_at: str = ""
    completed_at: str = ""
    def __post_init__(self):
        if not self.step_id: self.step_id = f"WS-{uuid.uuid4().hex[:8]}"


@dataclass
class Workflow:
    workflow_id: str = ""
    name: str = ""
    steps: list[WorkflowStep] = field(default_factory=list)
    status: WorkflowStatus = WorkflowStatus.PENDING
    context: dict[str, Any] = field(default_factory=dict)
    current_step: int = 0
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    completed_at: str = ""
    def __post_init__(self):
        if not self.workflow_id: self.workflow_id = f"WF-{uuid.uuid4().hex[:8]}"


class WorkflowEngine:
    def __init__(self, enabled: bool = False):
        self.enabled = enabled
        self._workflows: dict[str, Workflow] = {}
        self._step_handlers: dict[str, Callable] = {}

    def register_step_handler(self, name: str, handler: Callable) -> None:
        self._step_handlers[name] = handler

    def create_book_workflow(self, book_name: str, book_path: str = "") -> Workflow:
        steps = [WorkflowStep(name=n, inputs={"book": book_name, "path": book_path})
                 for n in ["ocr", "language_detection", "metadata_extraction", "evidence_search",
                           "cross_source_verification", "translation_alignment", "truth_reconstruction",
                           "quality_validation", "knowledge_graph_update", "checkpoint"]]
        wf = Workflow(name=f"book:{book_name}", steps=steps, context={"book_name": book_name})
        self._workflows[wf.workflow_id] = wf
        return wf

    def execute_step(self, workflow_id: str) -> bool:
        if not self.enabled: return False
        wf = self._workflows.get(workflow_id)
        if not wf or wf.current_step >= len(wf.steps): return False
        step = wf.steps[wf.current_step]
        step.status = StepStatus.RUNNING
        step.started_at = datetime.now(timezone.utc).isoformat()
        wf.status = WorkflowStatus.RUNNING
        handler = self._step_handlers.get(step.name)
        if handler:
            try:
                step.outputs = handler(step.inputs, wf.context)
                step.status = StepStatus.COMPLETED
                step.completed_at = datetime.now(timezone.utc).isoformat()
            except Exception as e:
                step.status = StepStatus.FAILED
                step.error = str(e)
                wf.status = WorkflowStatus.FAILED
                return False
        else:
            step.status = StepStatus.SKIPPED
        wf.current_step += 1
        if wf.current_step >= len(wf.steps):
            wf.status = WorkflowStatus.COMPLETED
            wf.completed_at = datetime.now(timezone.utc).isoformat()
        return True

    def resume(self, workflow_id: str) -> bool:
        wf = self._workflows.get(workflow_id)
        if wf and wf.status in (WorkflowStatus.PAUSED, WorkflowStatus.FAILED):
            wf.status = WorkflowStatus.PENDING
            return True
        return False

    def get_workflow(self, workflow_id: str) -> Optional[Workflow]:
        return self._workflows.get(workflow_id)

    def count(self) -> int: return len(self._workflows)

    def summary(self) -> dict:
        sc: dict[str, int] = {}
        for wf in self._workflows.values(): sc[wf.status.value] = sc.get(wf.status.value, 0) + 1
        return {"enabled": self.enabled, "total": self.count(), "by_status": sc}
