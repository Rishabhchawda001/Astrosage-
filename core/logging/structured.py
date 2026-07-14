"""Structured logging with JSON output support."""
from __future__ import annotations

import json
import logging
import sys
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any


class LogLevel(str, Enum):
    DEBUG = "debug"
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


@dataclass
class LogEntry:
    timestamp: str = ""
    level: str = ""
    logger: str = ""
    message: str = ""
    module: str = ""
    function: str = ""
    line: int = 0
    extra: dict = field(default_factory=dict)
    error: str = ""
    traceback: str = ""


class StructuredLogger:
    """Structured logger with JSON output support."""

    def __init__(self, name: str, json_output: bool = False):
        self.name = name
        self.json_output = json_output
        self._logger = logging.getLogger(name)

    def _emit(self, level: str, message: str, **kwargs):
        entry = LogEntry(
            timestamp=datetime.now(timezone.utc).isoformat(),
            level=level,
            logger=self.name,
            message=message,
            extra=kwargs,
        )
        if self.json_output:
            print(json.dumps(asdict(entry), ensure_ascii=False))
        else:
            getattr(self._logger, level.lower(), self._logger.info)(message)

    def debug(self, message: str, **kwargs):
        self._emit("debug", message, **kwargs)

    def info(self, message: str, **kwargs):
        self._emit("info", message, **kwargs)

    def warning(self, message: str, **kwargs):
        self._emit("warning", message, **kwargs)

    def error(self, message: str, **kwargs):
        self._emit("error", message, **kwargs)

    def critical(self, message: str, **kwargs):
        self._emit("critical", message, **kwargs)

    def component_event(self, component: str, event: str, **data):
        self.info(f"{component}: {event}", component=component, event=event, **data)
