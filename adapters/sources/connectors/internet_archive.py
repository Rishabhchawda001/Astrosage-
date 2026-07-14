"""
Internet Archive (archive.org) Source Connector — Production implementation.

Searches archive.org metadata API for public-domain texts, scans, and editions.
Downloads legally accessible public-domain content.
"""
from __future__ import annotations

import hashlib
import json
import logging
import os
import time
from pathlib import Path
from typing import Any, Optional
from urllib.parse import quote_plus

import requests

from adapters.sources.base import SourceAdapter, SourceConfig, SourceResult

logger = logging.getLogger(__name__)

_METADATA_API = "https://archive.org/metadata"
_SEARCH_API = "https://archive.org/advancedsearch.php"
_DOWNLOAD_BASE = "https://archive.org/download"


class InternetArchiveAdapter(SourceAdapter):
    """Real production connector for archive.org."""

    def __init__(self):
        self._config: SourceConfig | None = None
        self._session: requests.Session | None = None
        self._last_request: float = 0.0
        self._min_interval: float = 1.0  # 1 req/sec to be polite

    def name(self) -> str:
        return "internet_archive"

    def configure(self, config: SourceConfig) -> None:
        self._config = config
        self._session = requests.Session()
        self._session.headers.update({
            "User-Agent": "AstroSage-KnowledgeRecovery/1.0 (research; public-domain-texts)"
        })
        if config.timeout:
            self._session.timeout = config.timeout

    def health(self) -> dict[str, Any]:
        try:
            r = self._session.get("https://archive.org/metadata/metadata", timeout=10)
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
        """Search archive.org using Advanced Search API."""
        self._throttle()
        try:
            params = {
                "q": f'({query}) AND mediatype:texts',
                "fl[]": ["identifier", "title", "creator", "date", "language",
                         "subject", "description", "format", "item_count"],
                "sort[]": "downloads desc",
                "rows": str(max_results),
                "page": "1",
                "output": "json",
            }
            # Flatten list params for requests
            flat_params = {}
            for k, v in params.items():
                if isinstance(v, list):
                    flat_params[k] = v
                else:
                    flat_params[k] = v

            r = self._session.get(_SEARCH_API, params=flat_params, timeout=30)
            r.raise_for_status()
            data = r.json()

            items = []
            for doc in data.get("response", {}).get("docs", []):
                items.append({
                    "id": doc.get("identifier", ""),
                    "title": doc.get("title", ""),
                    "creator": doc.get("creator", ""),
                    "date": doc.get("date", ""),
                    "language": doc.get("language", []),
                    "subject": doc.get("subject", []),
                    "description": doc.get("description", ""),
                    "formats": doc.get("format", []),
                    "download_url": f"{_DOWNLOAD_BASE}/{doc.get('identifier', '')}",
                    "metadata_url": f"{_METADATA_API}/{doc.get('identifier', '')}",
                    "source": "archive.org",
                    "public_domain": True,  # archive.org texts are generally public domain
                })

            return SourceResult(
                success=True,
                items=items,
                total=data.get("response", {}).get("numFound", 0),
                source_name=self.name(),
                query=query,
            )
        except requests.RequestException as e:
            logger.warning("Archive.org search failed: %s", e)
            return SourceResult(success=False, source_name=self.name(), query=query, error=str(e))
        except (json.JSONDecodeError, KeyError) as e:
            return SourceResult(success=False, source_name=self.name(), query=query, error=f"Parse error: {e}")

    def fetch(self, item_id: str) -> SourceResult:
        """Fetch metadata for a specific archive.org item."""
        self._throttle()
        try:
            r = self._session.get(f"{_METADATA_API}/{item_id}", timeout=30)
            r.raise_for_status()
            data = r.json()

            metadata = data.get("metadata", {})
            files = data.get("files", [])

            text_files = [f for f in files if any(
                f.get("name", "").lower().endswith(ext)
                for ext in (".txt", ".pdf", ".djvu", ".epub")
            )]

            return SourceResult(
                success=True,
                items=[{
                    "id": item_id,
                    "title": metadata.get("title", ""),
                    "creator": metadata.get("creator", ""),
                    "date": metadata.get("date", ""),
                    "language": metadata.get("language", ""),
                    "publisher": metadata.get("publisher", ""),
                    "description": metadata.get("description", ""),
                    "text_files": [{"name": f["name"], "size": f.get("size", 0),
                                    "format": f.get("format", "")} for f in text_files],
                    "download_url": f"{_DOWNLOAD_BASE}/{item_id}",
                    "source": "archive.org",
                }],
                total=1,
                source_name=self.name(),
                query=item_id,
            )
        except Exception as e:
            return SourceResult(success=False, source_name=self.name(), query=item_id, error=str(e))

    def download_file(self, identifier: str, filename: str, dest_dir: str) -> Optional[dict]:
        """Download a file from archive.org. Returns file info or None on failure."""
        self._throttle()
        os.makedirs(dest_dir, exist_ok=True)
        url = f"{_DOWNLOAD_BASE}/{quote_plus(identifier)}/{quote_plus(filename)}"
        dest_path = os.path.join(dest_dir, filename)

        if os.path.exists(dest_path):
            return {"path": dest_path, "size": os.path.getsize(dest_path), "cached": True}

        try:
            r = self._session.get(url, stream=True, timeout=120)
            r.raise_for_status()
            with open(dest_path, "wb") as f:
                for chunk in r.iter_content(chunk_size=8192):
                    f.write(chunk)
            size = os.path.getsize(dest_path)
            return {"path": dest_path, "size": size, "cached": False}
        except Exception as e:
            logger.warning("Download failed for %s/%s: %s", identifier, filename, e)
            if os.path.exists(dest_path):
                os.remove(dest_path)
            return None

    def is_available(self) -> bool:
        return self._session is not None
