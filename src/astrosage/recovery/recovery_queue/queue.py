"""
Recovery Queue — Manages documents awaiting recovery processing.

Infrastructure only. No actual recovery execution in this phase.
"""
from __future__ import annotations

import json
import uuid
from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from enum import Enum
from pathlib import Path
from typing import Optional


class QueueStatus(str, Enum):
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    RETRYING = "retrying"


class Priority(str, Enum):
    CRITICAL = "critical"  # Highly damaged, frequently referenced
    HIGH = "high"          # Important text, significant OCR issues
    MEDIUM = "medium"      # Moderate issues, standard text
    LOW = "low"            # Minor issues, low-priority text


class FailureCategory(str, Enum):
    RECOVERABLE = "recoverable"       # Can retry automatically
    RETRYABLE = "retryable"           # Transient failure, retry with backoff
    FATAL = "fatal"                   # Permanent failure, needs human intervention


@dataclass
class RecoveryJob:
    job_id: str
    document_uuid: str
    book_uuid: str = ""
    page: int = 0
    bounding_box: str = ""  # "x1,y1,x2,y2" format for page regions
    reason: str = ""
    priority: Priority = Priority.MEDIUM
    confidence: float = 0.0
    retry_count: int = 0
    max_retries: int = 3
    assigned_worker: str = ""
    status: QueueStatus = QueueStatus.PENDING
    failure_category: Optional[FailureCategory] = None
    checkpoint: dict = field(default_factory=dict)
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    updated_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    completed_at: str = ""
    error_message: str = ""

    def to_dict(self) -> dict:
        d = asdict(self)
        d["priority"] = self.priority.value
        d["status"] = self.status.value
        if self.failure_category:
            d["failure_category"] = self.failure_category.value
        return d


class RecoveryQueue:
    """
    Priority queue for recovery jobs.

    Infrastructure only — no execution logic.
    Jobs are enqueued, prioritized, and dispatched to workers.
    """

    def __init__(self, queue_dir: str = "knowledge/recovery/recovery_queue"):
        self.queue_dir = Path(queue_dir)
        self.queue_dir.mkdir(parents=True, exist_ok=True)
        self._jobs: dict[str, RecoveryJob] = {}

    def enqueue(
        self,
        document_uuid: str,
        book_uuid: str = "",
        page: int = 0,
        reason: str = "",
        priority: Priority = Priority.MEDIUM,
        confidence: float = 0.0,
        bounding_box: str = "",
        max_retries: int = 3,
    ) -> str:
        """Add a job to the recovery queue. Returns job_id."""
        job_id = f"RQ-{uuid.uuid4().hex[:12]}"
        job = RecoveryJob(
            job_id=job_id,
            document_uuid=document_uuid,
            book_uuid=book_uuid,
            page=page,
            bounding_box=bounding_box,
            reason=reason,
            priority=priority,
            confidence=confidence,
            max_retries=max_retries,
        )
        self._jobs[job_id] = job
        return job_id

    def dequeue(self) -> Optional[RecoveryJob]:
        """Get the highest priority pending job."""
        priority_order = {
            Priority.CRITICAL: 0,
            Priority.HIGH: 1,
            Priority.MEDIUM: 2,
            Priority.LOW: 3,
        }
        pending = [j for j in self._jobs.values() if j.status == QueueStatus.PENDING]
        if not pending:
            return None
        pending.sort(key=lambda j: (priority_order.get(j.priority, 9), j.created_at))
        job = pending[0]
        job.status = QueueStatus.IN_PROGRESS
        job.updated_at = datetime.now(timezone.utc).isoformat()
        return job

    def complete_job(self, job_id: str, checkpoint: Optional[dict] = None):
        if job_id in self._jobs:
            self._jobs[job_id].status = QueueStatus.COMPLETED
            self._jobs[job_id].completed_at = datetime.now(timezone.utc).isoformat()
            self._jobs[job_id].updated_at = datetime.now(timezone.utc).isoformat()
            if checkpoint:
                self._jobs[job_id].checkpoint = checkpoint

    def fail_job(self, job_id: str, error: str, category: FailureCategory = FailureCategory.RETRYABLE):
        if job_id in self._jobs:
            job = self._jobs[job_id]
            job.retry_count += 1
            if job.retry_count >= job.max_retries or category == FailureCategory.FATAL:
                job.status = QueueStatus.FAILED
                job.failure_category = category
            else:
                job.status = QueueStatus.RETRYING
            job.error_message = error
            job.updated_at = datetime.now(timezone.utc).isoformat()

    def get_job(self, job_id: str) -> Optional[RecoveryJob]:
        return self._jobs.get(job_id)

    def get_by_status(self, status: QueueStatus) -> list[RecoveryJob]:
        return [j for j in self._jobs.values() if j.status == status]

    def get_by_priority(self, priority: Priority) -> list[RecoveryJob]:
        return [j for j in self._jobs.values() if j.priority == priority]

    @property
    def pending_count(self) -> int:
        return len([j for j in self._jobs.values() if j.status == QueueStatus.PENDING])

    @property
    def in_progress_count(self) -> int:
        return len([j for j in self._jobs.values() if j.status == QueueStatus.IN_PROGRESS])

    @property
    def completed_count(self) -> int:
        return len([j for j in self._jobs.values() if j.status == QueueStatus.COMPLETED])

    @property
    def failed_count(self) -> int:
        return len([j for j in self._jobs.values() if j.status == QueueStatus.FAILED])

    def save(self):
        data = {jid: j.to_dict() for jid, j in self._jobs.items()}
        filepath = self.queue_dir / "queue.json"
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

    def load(self):
        filepath = self.queue_dir / "queue.json"
        if not filepath.exists():
            return
        with open(filepath, "r", encoding="utf-8") as f:
            data = json.load(f)
        for jid, jdata in data.items():
            jdata["priority"] = Priority(jdata["priority"])
            jdata["status"] = QueueStatus(jdata["status"])
            if jdata.get("failure_category"):
                jdata["failure_category"] = FailureCategory(jdata["failure_category"])
            self._jobs[jid] = RecoveryJob(**jdata)

    def summary(self) -> dict:
        return {
            "total_jobs": len(self._jobs),
            "pending": self.pending_count,
            "in_progress": self.in_progress_count,
            "completed": self.completed_count,
            "failed": self.failed_count,
        }
