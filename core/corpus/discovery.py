"""
Discovery Engine — Searches external sources for recovery evidence.

Orchestrates source connectors to find alternative editions,
parallel texts, and supporting evidence for gap recovery.
"""
from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Optional

from core.corpus.sources import SourceRegistry


class DiscoveryStatus(str, Enum):
    PENDING = "pending"
    SEARCHING = "searching"
    RESULTS_FOUND = "results_found"
    NO_RESULTS = "no_results"
    ERROR = "error"


@dataclass
class DiscoveryRequest:
    """A request to search external sources."""
    request_id: str = ""
    query: str = ""
    book_title: str = ""
    author: str = ""
    language: str = ""
    edition: str = ""
    gap_id: str = ""
    source_ids: list[str] = field(default_factory=list)
    max_results: int = 10
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

    def __post_init__(self):
        if not self.request_id:
            self.request_id = f"DR-{uuid.uuid4().hex[:12]}"


@dataclass
class DiscoveryResult:
    """A result from external source search."""
    result_id: str = ""
    request_id: str = ""
    source_id: str = ""
    title: str = ""
    author: str = ""
    language: str = ""
    year: str = ""
    url: str = ""
    confidence: float = 0.0
    metadata: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self):
        if not self.result_id:
            self.result_id = f"DS-{uuid.uuid4().hex[:12]}"


class DiscoveryEngine:
    """Orchestrates external source searches for gap recovery."""

    def __init__(self, source_registry: SourceRegistry | None = None):
        self.source_registry = source_registry or SourceRegistry()
        self._requests: dict[str, DiscoveryRequest] = {}
        self._results: dict[str, list[DiscoveryResult]] = {}

    def create_request(self, **kwargs) -> DiscoveryRequest:
        request = DiscoveryRequest(**kwargs)
        self._requests[request.request_id] = request
        return request

    def add_result(self, request_id: str, result: DiscoveryResult) -> None:
        result.request_id = request_id
        self._results.setdefault(request_id, []).append(result)

    def get_results(self, request_id: str) -> list[DiscoveryResult]:
        return self._results.get(request_id, [])

    def get_request(self, request_id: str) -> Optional[DiscoveryRequest]:
        return self._requests.get(request_id)

    def count_requests(self) -> int:
        return len(self._requests)

    def count_results(self) -> int:
        return sum(len(r) for r in self._results.values())

    def summary(self) -> dict:
        return {"total_requests": self.count_requests(), "total_results": self.count_results()}
