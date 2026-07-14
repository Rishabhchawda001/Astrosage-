"""
Event Bus — Internal event system for APEE v2.

Supports pub/sub with typed events. Every lifecycle event is recorded.
"""
from __future__ import annotations

import uuid
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Callable


class EventType(str, Enum):
    TASK_CREATED = "task_created"
    TASK_STARTED = "task_started"
    TASK_COMPLETED = "task_completed"
    TASK_FAILED = "task_failed"
    TASK_RETRYING = "task_retrying"
    TASK_CANCELLED = "task_cancelled"
    CHECKPOINT_CREATED = "checkpoint_created"
    CHECKPOINT_RESUMED = "checkpoint_resumed"
    VALIDATION_PASSED = "validation_passed"
    VALIDATION_FAILED = "validation_failed"
    WORKER_REGISTERED = "worker_registered"
    WORKER_IDLE = "worker_idle"
    WORKER_ASSIGNED = "worker_assigned"
    WORKER_UNASSIGNED = "worker_unassigned"
    WORKER_FAILED = "worker_failed"
    PLUGIN_LOADED = "plugin_loaded"
    PLUGIN_UNLOADED = "plugin_unloaded"
    PHASE_STARTED = "phase_started"
    PHASE_COMPLETED = "phase_completed"
    RESOURCE_ALLOCATED = "resource_allocated"
    RESOURCE_RELEASED = "resource_released"
    CUSTOM = "custom"


@dataclass
class Event:
    event_id: str = ""
    event_type: EventType = EventType.CUSTOM
    source: str = ""
    data: dict[str, Any] = field(default_factory=dict)
    timestamp: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

    def __post_init__(self):
        if not self.event_id:
            self.event_id = f"EV-{uuid.uuid4().hex[:12]}"


EventHandler = Callable[[Event], None]


class EventBus:
    """
    Production event bus with typed events and subscriber management.
    Supports wildcard subscriptions and event history.
    """

    def __init__(self):
        self._handlers: dict[str, list[EventHandler]] = defaultdict(list)
        self._history: list[Event] = []
        self._max_history: int = 10000

    def subscribe(self, event_type: EventType | str, handler: EventHandler) -> str:
        key = event_type.value if isinstance(event_type, EventType) else event_type
        self._handlers[key].append(handler)
        return f"SUB-{uuid.uuid4().hex[:8]}"

    def subscribe_all(self, handler: EventHandler) -> str:
        return self.subscribe("*", handler)

    def unsubscribe(self, event_type: EventType | str, handler: EventHandler) -> bool:
        key = event_type.value if isinstance(event_type, EventType) else event_type
        if handler in self._handlers.get(key, []):
            self._handlers[key].remove(handler)
            return True
        return False

    def publish(self, event: Event) -> None:
        self._history.append(event)
        if len(self._history) > self._max_history:
            self._history = self._history[-self._max_history:]

        key = event.event_type.value if isinstance(event.event_type, EventType) else event.event_type
        for handler in self._handlers.get(key, []):
            try:
                handler(event)
            except Exception:
                pass
        for handler in self._handlers.get("*", []):
            try:
                handler(event)
            except Exception:
                pass

    def emit(self, event_type: EventType, source: str = "", data: dict | None = None) -> Event:
        event = Event(event_type=event_type, source=source, data=data or {})
        self.publish(event)
        return event

    def get_history(self, event_type: EventType | None = None, limit: int = 100) -> list[Event]:
        if event_type:
            events = [e for e in self._history if e.event_type == event_type]
        else:
            events = list(self._history)
        return events[-limit:]

    def clear_history(self) -> None:
        self._history.clear()

    def summary(self) -> dict:
        type_counts: dict[str, int] = {}
        for e in self._history:
            type_counts[e.event_type.value] = type_counts.get(e.event_type.value, 0) + 1
        return {
            "total_events": len(self._history),
            "subscriber_count": sum(len(h) for h in self._handlers.values()),
            "by_type": type_counts,
        }
