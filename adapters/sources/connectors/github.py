"""
GitHub Source Connector — Production implementation.

Searches GitHub for public datasets, code, and repositories
related to Sanskrit texts, scriptures, and scholarly data.
"""
from __future__ import annotations

import json
import logging
import time
from typing import Any

import requests

from adapters.sources.base import SourceAdapter, SourceConfig, SourceResult

logger = logging.getLogger(__name__)

_API_BASE = "https://api.github.com"


class GitHubAdapter(SourceAdapter):
    """Real production connector for GitHub API."""

    def __init__(self):
        self._config: SourceConfig | None = None
        self._session: requests.Session | None = None
        self._last_request: float = 0.0
        self._min_interval: float = 2.0  # Conservative for unauthenticated

    def name(self) -> str:
        return "github"

    def configure(self, config: SourceConfig) -> None:
        self._config = config
        self._session = requests.Session()
        self._session.headers.update({
            "Accept": "application/vnd.github.v3+json",
            "User-Agent": "AstroSage-KnowledgeRecovery/1.0",
        })
        if config.api_key:
            self._session.headers["Authorization"] = f"token {config.api_key}"

    def health(self) -> dict[str, Any]:
        try:
            r = self._session.get(f"{_API_BASE}/rate_limit", timeout=10)
            data = r.json() if r.status_code == 200 else {}
            remaining = data.get("resources", {}).get("core", {}).get("remaining", 0)
            return {"status": "healthy" if remaining > 10 else "rate_limited",
                    "source": self.name(), "rate_remaining": remaining}
        except Exception as e:
            return {"status": "unhealthy", "source": self.name(), "error": str(e)}

    def _throttle(self):
        elapsed = time.time() - self._last_request
        if elapsed < self._min_interval:
            time.sleep(self._min_interval - elapsed)
        self._last_request = time.time()

    def search(self, query: str, max_results: int = 10) -> SourceResult:
        """Search GitHub repositories."""
        self._throttle()
        try:
            params = {"q": query, "per_page": str(min(max_results, 30))}
            r = self._session.get(f"{_API_BASE}/search/repositories", params=params, timeout=30)
            r.raise_for_status()
            data = r.json()

            items = []
            for repo in data.get("items", []):
                items.append({
                    "id": repo.get("full_name", ""),
                    "name": repo.get("name", ""),
                    "description": repo.get("description", ""),
                    "url": repo.get("html_url", ""),
                    "language": repo.get("language", ""),
                    "stars": repo.get("stargazers_count", 0),
                    "created_at": repo.get("created_at", ""),
                    "updated_at": repo.get("updated_at", ""),
                    "topics": repo.get("topics", []),
                    "source": "github.com",
                })

            return SourceResult(
                success=True,
                items=items,
                total=data.get("total_count", 0),
                source_name=self.name(),
                query=query,
            )
        except Exception as e:
            logger.warning("GitHub search failed: %s", e)
            return SourceResult(success=False, source_name=self.name(), query=query, error=str(e))

    def search_code(self, query: str, max_results: int = 10) -> SourceResult:
        """Search GitHub code."""
        self._throttle()
        try:
            params = {"q": query, "per_page": str(min(max_results, 30))}
            r = self._session.get(f"{_API_BASE}/search/code", params=params, timeout=30)
            r.raise_for_status()
            data = r.json()

            items = []
            for item in data.get("items", []):
                repo = item.get("repository", {})
                items.append({
                    "path": item.get("path", ""),
                    "name": item.get("name", ""),
                    "url": item.get("html_url", ""),
                    "repo": repo.get("full_name", ""),
                    "repo_url": repo.get("html_url", ""),
                    "source": "github.com",
                })

            return SourceResult(
                success=True, items=items, total=data.get("total_count", 0),
                source_name=self.name(), query=query,
            )
        except Exception as e:
            return SourceResult(success=False, source_name=self.name(), query=query, error=str(e))

    def fetch(self, item_id: str) -> SourceResult:
        """Fetch repository details."""
        self._throttle()
        try:
            r = self._session.get(f"{_API_BASE}/repos/{item_id}", timeout=30)
            r.raise_for_status()
            data = r.json()
            return SourceResult(
                success=True, items=[{
                    "id": data.get("full_name", ""),
                    "description": data.get("description", ""),
                    "url": data.get("html_url", ""),
                    "default_branch": data.get("default_branch", ""),
                    "source": "github.com",
                }], total=1, source_name=self.name(), query=item_id,
            )
        except Exception as e:
            return SourceResult(success=False, source_name=self.name(), query=item_id, error=str(e))

    def is_available(self) -> bool:
        return self._session is not None
