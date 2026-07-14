"""
OpenAlex Source Connector — Production implementation.

Searches api.openalex.org for open scholarly works, authors, institutions.
Fully open, no API key required.
"""
from __future__ import annotations

import json
import logging
import time
from typing import Any

import requests

from adapters.sources.base import SourceAdapter, SourceConfig, SourceResult

logger = logging.getLogger(__name__)

_API_BASE = "https://api.openalex.org"


class OpenAlexAdapter(SourceAdapter):
    """Real production connector for OpenAlex API."""

    def __init__(self):
        self._config: SourceConfig | None = None
        self._session: requests.Session | None = None
        self._last_request: float = 0.0
        self._min_interval: float = 0.5

    def name(self) -> str:
        return "openalex"

    def configure(self, config: SourceConfig) -> None:
        self._config = config
        self._session = requests.Session()
        self._session.headers.update({
            "User-Agent": "AstroSage-KnowledgeRecovery/1.0 (research)"
        })

    def health(self) -> dict[str, Any]:
        try:
            r = self._session.get(f"{_API_BASE}/works?per_page=1", timeout=10)
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
                "search": query,
                "per_page": str(max_results),
                "select": "id,title,authorships,publication_year,primary_location,"
                          "type,language,open_access,doi,biblio",
            }
            r = self._session.get(f"{_API_BASE}/works", params=params, timeout=30)
            r.raise_for_status()
            data = r.json()

            items = []
            for work in data.get("results", []):
                authors = []
                for authorship in work.get("authorships", []):
                    author = authorship.get("author", {})
                    authors.append({"name": author.get("display_name", ""),
                                    "id": author.get("id", "")})
                loc = work.get("primary_location", {}) or {}
                source = loc.get("source", {}) or {}
                items.append({
                    "id": work.get("id", ""),
                    "doi": work.get("doi", ""),
                    "title": work.get("title", ""),
                    "authors": authors,
                    "publication_year": work.get("publication_year"),
                    "source_name": source.get("display_name", ""),
                    "type": work.get("type", ""),
                    "language": work.get("language", ""),
                    "is_oa": work.get("open_access", {}).get("is_oa", False),
                    "oa_url": work.get("open_access", {}).get("oa_url", ""),
                    "biblio": work.get("biblio", {}),
                    "source": "openalex.org",
                })

            return SourceResult(
                success=True,
                items=items,
                total=data.get("meta", {}).get("count", 0),
                source_name=self.name(),
                query=query,
            )
        except Exception as e:
            logger.warning("OpenAlex search failed: %s", e)
            return SourceResult(success=False, source_name=self.name(), query=query, error=str(e))

    def fetch(self, item_id: str) -> SourceResult:
        self._throttle()
        try:
            r = self._session.get(f"{_API_BASE}/works/{item_id}", timeout=30)
            r.raise_for_status()
            data = r.json()
            return SourceResult(
                success=True, items=[data], total=1,
                source_name=self.name(), query=item_id,
            )
        except Exception as e:
            return SourceResult(success=False, source_name=self.name(), query=item_id, error=str(e))

    def is_available(self) -> bool:
        return self._session is not None
