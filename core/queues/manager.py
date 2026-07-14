"""
Queue Manager — Priority-based task queues with work stealing.

Supports multiple named queues, priority ordering, and queue balancing.
"""
from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Optional


class QueueType(str, Enum):
    DEFAULT = "default"
    PRIORITY = "priority"
    RECOVERY = "recovery"
    VALIDATION = "validation"
    CHECKPOINT = "checkpoint"


@dataclass
class QueueItem:
    item_id: str = ""
    task_id: str = ""
    priority: int = 0
    payload: dict[str, Any] = field(default_factory=dict)
    enqueued_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    retry_count: int = 0

    def __post_init__(self):
        if not self.item_id:
            self.item_id = f"QI-{uuid.uuid4().hex[:8]}"


class TaskQueue:
    """A single priority queue."""

    def __init__(self, name: str = "default", queue_type: QueueType = QueueType.DEFAULT):
        self.name = name
        self.queue_type = queue_type
        self._items: list[QueueItem] = []

    def enqueue(self, item: QueueItem) -> str:
        self._items.append(item)
        self._items.sort(key=lambda i: i.priority)
        return item.item_id

    def dequeue(self) -> Optional[QueueItem]:
        if self._items:
            return self._items.pop(0)
        return None

    def peek(self) -> Optional[QueueItem]:
        return self._items[0] if self._items else None

    def size(self) -> int:
        return len(self._items)

    def is_empty(self) -> bool:
        return len(self._items) == 0

    def remove(self, item_id: str) -> bool:
        for i, item in enumerate(self._items):
            if item.item_id == item_id:
                self._items.pop(i)
                return True
        return False

    def list_items(self) -> list[QueueItem]:
        return list(self._items)


class QueueManager:
    """Manages multiple named priority queues with work stealing."""

    def __init__(self):
        self._queues: dict[str, TaskQueue] = {}
        self._queues["default"] = TaskQueue("default", QueueType.DEFAULT)

    def create_queue(self, name: str, queue_type: QueueType = QueueType.DEFAULT) -> TaskQueue:
        if name not in self._queues:
            self._queues[name] = TaskQueue(name, queue_type)
        return self._queues[name]

    def get_queue(self, name: str) -> TaskQueue | None:
        return self._queues.get(name)

    def enqueue(self, queue_name: str, item: QueueItem) -> str:
        if queue_name not in self._queues:
            self._queues[queue_name] = TaskQueue(queue_name, QueueType.DEFAULT)
        queue = self._queues[queue_name]
        return queue.enqueue(item)

    def dequeue(self, queue_name: str = "default") -> Optional[QueueItem]:
        queue = self._queues.get(queue_name)
        if queue and not queue.is_empty():
            return queue.dequeue()
        return None

    def steal(self, from_queue: str) -> Optional[QueueItem]:
        """Work stealing: take lowest-priority item from another queue."""
        queue = self._queues.get(from_queue)
        if queue and not queue.is_empty():
            items = queue.list_items()
            if items:
                item = items[-1]
                queue.remove(item.item_id)
                return item
        return None

    def total_items(self) -> int:
        return sum(q.size() for q in self._queues.values())

    def queue_names(self) -> list[str]:
        return list(self._queues.keys())

    def summary(self) -> dict:
        return {
            "total_queues": len(self._queues),
            "total_items": self.total_items(),
            "by_queue": {name: q.size() for name, q in self._queues.items()},
        }
