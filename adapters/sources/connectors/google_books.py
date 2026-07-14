"""
Google Books Source Connector — Production implementation.

Searches Google Books API for book metadata, editions, and availability.
Free tier: 1000 requests/day without API key.
"""
from __future__ import annotations

import json
import logging
import time
from typing import Any

import requests

from adapters.sources.base import SourceAdapter, SourceConfig, SourceResult

logger = logging.getLogger(__name__)

_API_URL = "https://www.googleapis.com/books/v1/volumes"


class GoogleBooksAdapter(SourceAdapter):
    """Real production connector for Google Books API."""

    def __init__(self):
        self._config: SourceConfig | None = None
        self._session: requests.Session | None = None
        self._last_request: float = 0.0
        self._min_interval: float = 1.0

    def name(self) -> str:
        return "google_books"

    def configure(self, config: SourceConfig) -> None:
        self._config = config
        self._session = requests.Session()
        self._api_key = config.api_key if config else ""

    def health(self) -> dict[str, Any]:
        try:
            params = {"q": "test", "maxResults": "1"}
            if self._api_key:
                params["key"] = self._api_key
            r = self._session.get(_API_URL, params=params, timeout=10)
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
                "q": query,
                "maxResults": str(min(max_results, 40)),
                "printType": "books",
                "langRestrict": "sa,hi,en,gu,pa,mr",
            }
            if self._api_key:
                params["key"] = self._api_key
            r = self._session.get(_API_URL, params=params, timeout=30)
            if r.status_code == 429:
                return SourceResult(success=False, source_name=self.name(), query=query,
                                    error="Rate limited (429)")
            r.raise_for_status()
            data = r.json()

            items = []
            for vol in data.get("items", []):
                info = vol.get("volumeInfo", {})
                items.append({
                    "id": vol.get("id", ""),
                    "title": info.get("title", ""),
                    "subtitle": info.get("subtitle", ""),
                    "authors": info.get("authors", []),
                    "publisher": info.get("publisher", ""),
                    "published_date": info.get("publishedDate", ""),
                    "language": info.get("language", ""),
                    "page_count": info.get("pageCount", 0),
                    "categories": info.get("categories", []),
                    "description": info.get("description", ""),
                    "isbn": [ident.get("identifier") for ident in info.get("industryIdentifiers", [])
                             if ident.get("type") in ("ISBN_10", "ISBN_13")],
                    "preview_link": info.get("previewLink", ""),
                    "info_link": info.get("infoLink", ""),
                    "source": "googleapis.com/books",
                })

            return SourceResult(
                success=True, items=items,
                total=data.get("totalItems", 0),
                source_name=self.name(), query=query,
            )
        except Exception as e:
            logger.warning("Google Books search failed: %s", e)
            return SourceResult(success=False, source_name=self.name(), query=query, error=str(e))

    def fetch(self, item_id: str) -> SourceResult:
        self._throttle()
        try:
            params = {}
            if self._api_key:
                params["key"] = self._api_key
            r = self._session.get(f"{_API_URL}/{item_id}", params=params, timeout=30)
            r.raise_for_status()
            data = r.json()
            info = data.get("volumeInfo", {})
            return SourceResult(
                success=True,
                items=[{
                    "id": item_id,
                    "title": info.get("title", ""),
                    "authors": info.get("authors", []),
                    "publisher": info.get("publisher", ""),
                    "source": "googleapis.com/books",
                }],
                total=1, source_name=self.name(), query=item_id,
            )
        except Exception as e:
            return SourceResult(success=False, source_name=self.name(), query=item_id, error=str(e))

    def is_available(self) -> bool:
        return self._session is not None
