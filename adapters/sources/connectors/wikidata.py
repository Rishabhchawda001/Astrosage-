"""
Wikidata Source Connector — Production implementation.

Searches Wikidata for structured knowledge about texts, authors, publishers.
Uses SPARQL and search APIs.
"""
from __future__ import annotations

import json
import logging
import time
from typing import Any

import requests

from adapters.sources.base import SourceAdapter, SourceConfig, SourceResult

logger = logging.getLogger(__name__)

_API_BASE = "https://www.wikidata.org/w/api.php"
_SPARQL_ENDPOINT = "https://query.wikidata.org/sparql"


class WikidataAdapter(SourceAdapter):
    """Real production connector for Wikidata."""

    def __init__(self):
        self._config: SourceConfig | None = None
        self._session: requests.Session | None = None
        self._last_request: float = 0.0
        self._min_interval: float = 1.0

    def name(self) -> str:
        return "wikidata"

    def configure(self, config: SourceConfig) -> None:
        self._config = config
        self._session = requests.Session()
        self._session.headers.update({
            "User-Agent": "AstroSage-KnowledgeRecovery/1.0 (research)",
            "Accept": "application/json",
        })

    def health(self) -> dict[str, Any]:
        try:
            params = {"action": "wbgetentities", "ids": "Q1", "format": "json"}
            r = self._session.get(_API_BASE, params=params, timeout=10)
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
        """Search Wikidata entities."""
        self._throttle()
        try:
            params = {
                "action": "wbsearchentities",
                "search": query,
                "language": "en",
                "limit": str(max_results),
                "format": "json",
            }
            r = self._session.get(_API_BASE, params=params, timeout=30)
            r.raise_for_status()
            data = r.json()

            items = []
            for result in data.get("search", []):
                items.append({
                    "id": result.get("id", ""),
                    "label": result.get("label", ""),
                    "description": result.get("description", ""),
                    "url": result.get("concepturi", ""),
                    "source": "wikidata.org",
                })

            return SourceResult(
                success=True,
                items=items,
                total=data.get("searchinfo", {}).get("hits", len(items)),
                source_name=self.name(),
                query=query,
            )
        except Exception as e:
            logger.warning("Wikidata search failed: %s", e)
            return SourceResult(success=False, source_name=self.name(), query=query, error=str(e))

    def fetch(self, item_id: str) -> SourceResult:
        """Fetch full entity data from Wikidata."""
        self._throttle()
        try:
            params = {
                "action": "wbgetentities",
                "ids": item_id,
                "format": "json",
                "props": "labels|descriptions|claims|sitelinks",
                "languages": "en|hi|sa|gu|pa|mr",
            }
            r = self._session.get(_API_BASE, params=params, timeout=30)
            r.raise_for_status()
            data = r.json()

            entity = data.get("entities", {}).get(item_id, {})
            labels = {lang: v.get("value", "") for lang, v in entity.get("labels", {}).items()}
            descriptions = {lang: v.get("value", "") for lang, v in entity.get("descriptions", {}).items()}

            return SourceResult(
                success=True,
                items=[{
                    "id": item_id,
                    "labels": labels,
                    "descriptions": descriptions,
                    "sitelinks": entity.get("sitelinks", {}),
                    "source": "wikidata.org",
                }],
                total=1, source_name=self.name(), query=item_id,
            )
        except Exception as e:
            return SourceResult(success=False, source_name=self.name(), query=item_id, error=str(e))

    def sparql_query(self, query: str) -> SourceResult:
        """Execute a SPARQL query against Wikidata."""
        self._throttle()
        try:
            r = self._session.get(_SPARQL_ENDPOINT,
                                  params={"query": query, "format": "json"},
                                  timeout=60)
            r.raise_for_status()
            data = r.json()
            bindings = data.get("results", {}).get("bindings", [])
            return SourceResult(
                success=True,
                items=bindings,
                total=len(bindings),
                source_name=self.name(),
                query="SPARQL",
            )
        except Exception as e:
            return SourceResult(success=False, source_name=self.name(), query="SPARQL", error=str(e))

    def is_available(self) -> bool:
        return self._session is not None
