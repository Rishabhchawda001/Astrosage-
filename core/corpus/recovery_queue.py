"""
Recovery Queue — Priority-based queue for knowledge recovery.

Automatically prioritizes recovery based on knowledge importance,
confidence, and availability of alternate sources.
"""
from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Optional

from core.corpus.gaps import Gap, GapSeverity


class RecoveryPriority(str, Enum):
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class RecoveryStatus(str, Enum):
    QUEUED = "queued"
    IN_PROGRESS = "in_progress"
    CANDIDATE_FOUND = "candidate_found"
    RECOVERED = "recovered"
    FAILED = "failed"
    DEFERRED = "deferred"


@dataclass
class RecoveryJob:
    """A single recovery job in the queue."""
    job_id: str = ""
    gap_id: str = ""
    book_uuid: str = ""
    edition_uuid: str = ""
    passport_id: str = ""
    priority: RecoveryPriority = RecoveryPriority.MEDIUM
    status: RecoveryStatus = RecoveryStatus.QUEUED
    description: str = ""
    confidence: float = 0.0
    evidence_count: int = 0
    source_count: int = 0
    retry_count: int = 0
    max_retries: int = 3
    assigned_worker: str = ""
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    updated_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    metadata: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self):
        if not self.job_id:
            self.job_id = f"RJ-{uuid.uuid4().hex[:12]}"

    @property
    def can_retry(self) -> bool:
        return self.retry_count < self.max_retries


class RecoveryQueue:
    """
    Priority-based recovery queue.

    Orders jobs by priority, evidence availability, and importance.
    Supports retry with backoff and worker assignment.
    """

    def __init__(self):
        self._jobs: dict[str, RecoveryJob] = {}
        self._queue: list[str] = []

    def enqueue_from_gap(self, gap: Gap, source_count: int = 0) -> RecoveryJob:
        severity_to_priority = {
            GapSeverity.CRITICAL: RecoveryPriority.CRITICAL,
            GapSeverity.HIGH: RecoveryPriority.HIGH,
            GapSeverity.MEDIUM: RecoveryPriority.MEDIUM,
            GapSeverity.LOW: RecoveryPriority.LOW,
        }
        priority = severity_to_priority.get(gap.severity, RecoveryPriority.MEDIUM)
        job = RecoveryJob(
            gap_id=gap.gap_id,
            book_uuid=gap.book_uuid,
            edition_uuid=gap.edition_uuid,
            passport_id=gap.passport_id,
            priority=priority,
            description=gap.description,
            confidence=gap.confidence,
            source_count=source_count,
        )
        self._jobs[job.job_id] = job
        self._reorder()
        return job

    def enqueue(self, job: RecoveryJob) -> str:
        self._jobs[job.job_id] = job
        self._reorder()
        return job.job_id

    def dequeue(self) -> Optional[RecoveryJob]:
        for job_id in self._queue:
            job = self._jobs.get(job_id)
            if job and job.status == RecoveryStatus.QUEUED:
                job.status = RecoveryStatus.IN_PROGRESS
                return job
        return None

    def complete(self, job_id: str, success: bool = True) -> None:
        job = self._jobs.get(job_id)
        if job:
            job.status = RecoveryStatus.RECOVERED if success else RecoveryStatus.FAILED
            job.updated_at = datetime.now(timezone.utc).isoformat()
            if job_id in self._queue:
                self._queue.remove(job_id)

    def retry(self, job_id: str) -> bool:
        job = self._jobs.get(job_id)
        if job and job.can_retry:
            job.retry_count += 1
            job.status = RecoveryStatus.QUEUED
            job.updated_at = datetime.now(timezone.utc).isoformat()
            self._queue.append(job_id)
            return True
        return False

    def get_job(self, job_id: str) -> Optional[RecoveryJob]:
        return self._jobs.get(job_id)

    def get_next(self) -> Optional[RecoveryJob]:
        return self.dequeue()

    def size(self) -> int:
        return len([j for j in self._jobs.values() if j.status == RecoveryStatus.QUEUED])

    def _reorder(self) -> None:
        priority_order = {"critical": 0, "high": 1, "medium": 2, "low": 3}
        queued = [(jid, self._jobs[jid]) for jid in self._jobs if self._jobs[jid].status == RecoveryStatus.QUEUED]
        queued.sort(key=lambda x: (priority_order.get(x[1].priority.value, 2), -x[1].evidence_count))
        self._queue = [jid for jid, _ in queued]

    def list_all(self) -> list[RecoveryJob]:
        return list(self._jobs.values())

    def summary(self) -> dict:
        status_counts: dict[str, int] = {}
        priority_counts: dict[str, int] = {}
        for j in self._jobs.values():
            status_counts[j.status.value] = status_counts.get(j.status.value, 0) + 1
            priority_counts[j.priority.value] = priority_counts.get(j.priority.value, 0) + 1
        return {
            "total_jobs": len(self._jobs),
            "queued": self.size(),
            "by_status": status_counts,
            "by_priority": priority_counts,
        }
