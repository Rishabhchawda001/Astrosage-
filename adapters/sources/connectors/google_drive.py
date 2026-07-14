"""
googleDrive Source Connector — Stub for google_drive integration.
"""
from __future__ import annotations
from typing import Any
from adapters.sources.base import SourceAdapter, SourceConfig, SourceResult


class googleDriveAdapter(SourceAdapter):
    def __init__(self):
        self._config: SourceConfig | None = None

    def name(self) -> str:
        return "google_drive"

    def configure(self, config: SourceConfig) -> None:
        self._config = config

    def health(self) -> dict[str, Any]:
        return {"status": "stub", "source": self.name()}

    def search(self, query: str, max_results: int = 10) -> SourceResult:
        return SourceResult(success=False, source_name=self.name(), query=query, error="Not yet implemented")

    def fetch(self, item_id: str) -> SourceResult:
        return SourceResult(success=False, source_name=self.name(), error="Not yet implemented")

    def is_available(self) -> bool:
        return False
