"""
Crossref Source Connector — Production implementation.

Searches api.crossref.org for academic metadata, DOIs, and scholarly works.
No API key required for basic queries (polite pool with email).
"""
from __future__ import annotations

import json
import logging
import time
from typing import Any

import requests

from adapters.sources.base import SourceAdapter, SourceConfig, SourceResult

logger = logging.getLogger(__name__)

_API_BASE = "https://api.crossref.org"


class CrossrefAdapter(SourceAdapter):
    """Real production connector for Crossref API."""

    def __init__(self):
        self._config: SourceConfig | None = None
        self._session: requests.Session | None = None
        self._last_request: float = 0.0
        self._min_interval: float = 1.0

    def name(self) -> str:
        return "crossref"

    def configure(self, config: SourceConfig) -> None:
        self._config = config
        self._session = requests.Session()
        self._session.headers.update({
            "User-Agent": "AstroSage-KnowledgeRecovery/1.0 (mailto:astrosage@research.org)"
        })

    def health(self) -> dict[str, Any]:
        try:
            r = self._session.get(f"{_API_BASE}/works?rows=1", timeout=10)
            return {"status": "healthy" if r.status_code == 200 else "degraded",
                    "source": self.name(), "status_code": r.status_code}
        except Exception as e:
            return {"status": "unhealthy", "source": self.name(), "error": str(e)}

    def _throttle(self):
        elapsed = time.time() - self._last_request
        if elapsed < self._min_interval:
            time.sleep(self._min_interval - elapsed)
        self._last_request = time.time()

    def search(self, query: str, max_results: int = 10) -> SourceResult:
        self._throttle()
        try:
            params = {
                "query": query,
                "rows": str(max_results),
            }
            r = self._session.get(f"{_API_BASE}/works", params=params, timeout=30)
            r.raise_for_status()
            data = r.json()

            items = []
            for msg in data.get("message", {}).get("items", []):
                title = msg.get("title", [""])[0] if msg.get("title") else ""
                authors = [{"given": a.get("given", ""), "family": a.get("family", "")}
                           for a in msg.get("author", [])]
                container = msg.get("container-title", [""])[0] if msg.get("container-title") else ""
                items.append({
                    "doi": msg.get("DOI", ""),
                    "title": title,
                    "authors": authors,
                    "publisher": msg.get("publisher", ""),
                    "container_title": container,
                    "type": msg.get("type", ""),
                    "subject": msg.get("subject", []),
                    "isbn": msg.get("ISBN", []),
                    "issn": msg.get("ISSN", []),
                    "language": msg.get("language", ""),
                    "abstract": msg.get("abstract", ""),
                    "source": "crossref.org",
                })

            return SourceResult(
                success=True,
                items=items,
                total=data.get("message", {}).get("total-results", 0),
                source_name=self.name(),
                query=query,
            )
        except Exception as e:
            logger.warning("Crossref search failed: %s", e)
            return SourceResult(success=False, source_name=self.name(), query=query, error=str(e))

    def fetch(self, item_id: str) -> SourceResult:
        """Fetch by DOI."""
        self._throttle()
        try:
            r = self._session.get(f"{_API_BASE}/works/{item_id}", timeout=30)
            r.raise_for_status()
            data = r.json()
            msg = data.get("message", {})
            return SourceResult(
                success=True,
                items=[{"doi": msg.get("DOI", ""), "title": msg.get("title", [""])[0],
                        "source": "crossref.org"}],
                total=1, source_name=self.name(), query=item_id,
            )
        except Exception as e:
            return SourceResult(success=False, source_name=self.name(), query=item_id, error=str(e))

    def is_available(self) -> bool:
        return self._session is not None
