"""
Open Library Source Connector — Production implementation.

Searches openlibrary.org for book metadata, editions, and availability.
Provides structured metadata for comparison and evidence building.
"""
from __future__ import annotations

import json
import logging
import time
from typing import Any, Optional

import requests

from adapters.sources.base import SourceAdapter, SourceConfig, SourceResult

logger = logging.getLogger(__name__)

_SEARCH_API = "https://openlibrary.org/search.json"
_EDITION_API = "https://openlibrary.org/books"
_AUTHORS_API = "https://openlibrary.org/authors"
_SUBJECTS_API = "https://openlibrary.org/subjects"


class OpenLibraryAdapter(SourceAdapter):
    """Real production connector for Open Library."""

    def __init__(self):
        self._config: SourceConfig | None = None
        self._session: requests.Session | None = None
        self._last_request: float = 0.0
        self._min_interval: float = 1.0

    def name(self) -> str:
        return "open_library"

    def configure(self, config: SourceConfig) -> None:
        self._config = config
        self._session = requests.Session()
        self._session.headers.update({
            "User-Agent": "AstroSage-KnowledgeRecovery/1.0 (research)"
        })

    def health(self) -> dict[str, Any]:
        try:
            r = self._session.get("https://openlibrary.org/search.json?q=test&limit=1", timeout=10)
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
        """Search Open Library for books matching the query."""
        self._throttle()
        try:
            params = {
                "q": query,
                "limit": str(max_results),
                "fields": "key,title,author_name,first_publish_year,isbn,publisher,"
                          "language,subject,availability,cover_i,edition_key",
            }
            r = self._session.get(_SEARCH_API, params=params, timeout=30)
            r.raise_for_status()
            data = r.json()

            items = []
            for doc in data.get("docs", []):
                editions = doc.get("edition_key", [])
                items.append({
                    "id": doc.get("key", ""),
                    "title": doc.get("title", ""),
                    "author_name": doc.get("author_name", []),
                    "first_publish_year": doc.get("first_publish_year"),
                    "isbn": doc.get("isbn", []),
                    "publisher": doc.get("publisher", []),
                    "language": doc.get("language", []),
                    "subject": doc.get("subject", [])[:10],
                    "edition_keys": editions,
                    "cover_id": doc.get("cover_i"),
                    "availability": doc.get("availability", {}),
                    "openlibrary_url": f"https://openlibrary.org{doc.get('key', '')}",
                    "source": "openlibrary.org",
                })

            return SourceResult(
                success=True,
                items=items,
                total=data.get("numFound", 0),
                source_name=self.name(),
                query=query,
            )
        except Exception as e:
            logger.warning("Open Library search failed: %s", e)
            return SourceResult(success=False, source_name=self.name(), query=query, error=str(e))

    def fetch(self, item_id: str) -> SourceResult:
        """Fetch detailed info for a specific edition or work."""
        self._throttle()
        try:
            url = f"https://openlibrary.org{item_id}.json"
            r = self._session.get(url, timeout=30)
            r.raise_for_status()
            data = r.json()

            return SourceResult(
                success=True,
                items=[{
                    "id": item_id,
                    "title": data.get("title", ""),
                    "subtitle": data.get("subtitle", ""),
                    "authors": [a.get("key", "") for a in data.get("authors", [])],
                    "publish_date": data.get("publish_date", ""),
                    "publishers": data.get("publishers", []),
                    "number_of_pages": data.get("number_of_pages"),
                    "isbn_10": data.get("isbn_10", []),
                    "isbn_13": data.get("isbn_13", []),
                    "oclc": data.get("oclc_numbers", []),
                    "lccn": data.get("lccn", []),
                    "languages": [l.get("key", "") for l in data.get("languages", [])],
                    "subjects": data.get("subjects", []),
                    "source": "openlibrary.org",
                }],
                total=1,
                source_name=self.name(),
                query=item_id,
            )
        except Exception as e:
            return SourceResult(success=False, source_name=self.name(), query=item_id, error=str(e))

    def search_by_isbn(self, isbn: str) -> SourceResult:
        """Search by ISBN."""
        self._throttle()
        try:
            url = f"https://openlibrary.org/isbn/{isbn}.json"
            r = self._session.get(url, timeout=15)
            if r.status_code == 404:
                return SourceResult(success=False, source_name=self.name(), query=isbn, error="Not found")
            r.raise_for_status()
            data = r.json()
            return SourceResult(
                success=True, items=[data], total=1, source_name=self.name(), query=isbn
            )
        except Exception as e:
            return SourceResult(success=False, source_name=self.name(), query=isbn, error=str(e))

    def is_available(self) -> bool:
        return self._session is not None
