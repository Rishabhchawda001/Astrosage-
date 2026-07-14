"""
arXiv Source Connector — Production implementation.

Searches arxiv.org for scholarly preprints related to Sanskrit, Indology, etc.
Uses the arxiv API (no key required).
"""
from __future__ import annotations

import json
import logging
import time
import xml.etree.ElementTree as ET
from typing import Any

import requests

from adapters.sources.base import SourceAdapter, SourceConfig, SourceResult

logger = logging.getLogger(__name__)

_API_URL = "http://export.arxiv.org/api/query"
_NS = {"atom": "http://www.w3.org/2005/Atom"}


class ArxivAdapter(SourceAdapter):
    """Real production connector for arXiv API."""

    def __init__(self):
        self._config: SourceConfig | None = None
        self._session: requests.Session | None = None
        self._last_request: float = 0.0
        self._min_interval: float = 3.0  # arxiv recommends 3s between requests

    def name(self) -> str:
        return "arxiv"

    def configure(self, config: SourceConfig) -> None:
        self._config = config
        self._session = requests.Session()

    def health(self) -> dict[str, Any]:
        try:
            r = self._session.get(_API_URL, params={"search_query": "cat:cs.AI", "max_results": "1"}, timeout=15)
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
                "search_query": f"all:{query}",
                "max_results": str(max_results),
                "sortBy": "relevance",
                "sortOrder": "descending",
            }
            r = self._session.get(_API_URL, params=params, timeout=30)
            r.raise_for_status()
            root = ET.fromstring(r.text)

            items = []
            for entry in root.findall("atom:entry", _NS):
                title = entry.findtext("atom:title", "", _NS).strip()
                summary = entry.findtext("atom:summary", "", _NS).strip()
                authors = [a.findtext("atom:name", "", _NS) for a in entry.findall("atom:author", _NS)]
                links = {l.get("title", l.get("type", "")): l.get("href", "")
                         for l in entry.findall("atom:link", _NS)}
                categories = [c.get("term", "") for c in entry.findall("atom:category", _NS)]

                items.append({
                    "id": entry.findtext("atom:id", "", _NS),
                    "title": title,
                    "summary": summary,
                    "authors": authors,
                    "published": entry.findtext("atom:published", "", _NS),
                    "pdf_url": links.get("pdf", ""),
                    "categories": categories,
                    "source": "arxiv.org",
                })

            return SourceResult(
                success=True, items=items,
                total=len(items), source_name=self.name(), query=query,
            )
        except Exception as e:
            logger.warning("arXiv search failed: %s", e)
            return SourceResult(success=False, source_name=self.name(), query=query, error=str(e))

    def fetch(self, item_id: str) -> SourceResult:
        self._throttle()
        try:
            params = {"id_list": item_id}
            r = self._session.get(_API_URL, params=params, timeout=30)
            r.raise_for_status()
            root = ET.fromstring(r.text)
            entry = root.find("atom:entry", _NS)
            if entry is None:
                return SourceResult(success=False, source_name=self.name(), query=item_id, error="Not found")
            title = entry.findtext("atom:title", "", _NS).strip()
            return SourceResult(
                success=True,
                items=[{"id": item_id, "title": title, "source": "arxiv.org"}],
                total=1, source_name=self.name(), query=item_id,
            )
        except Exception as e:
            return SourceResult(success=False, source_name=self.name(), query=item_id, error=str(e))

    def is_available(self) -> bool:
        return self._session is not None
