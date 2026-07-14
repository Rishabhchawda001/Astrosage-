"""Browser and web research adapter interfaces."""
from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field


@dataclass
class WebResult:
    url: str = ""
    title: str = ""
    content: str = ""
    snippet: str = ""
    metadata: dict = field(default_factory=dict)


class BrowserAdapter(ABC):
    @abstractmethod
    def name(self) -> str: ...
    @abstractmethod
    def fetch(self, url: str) -> WebResult: ...
    @abstractmethod
    def search(self, query: str, max_results: int = 10) -> list[WebResult]: ...
    @abstractmethod
    def health(self) -> dict: ...


class PlaywrightAdapter(BrowserAdapter):
    def name(self): return "playwright"
    def fetch(self, url): return WebResult()
    def search(self, query, max_results=10): return []
    def health(self): return {"status": "scaffold"}


class GitHubAdapter(BrowserAdapter):
    def name(self): return "github"
    def fetch(self, url): return WebResult()
    def search(self, query, max_results=10): return []
    def health(self): return {"status": "scaffold"}


class BraveAdapter(BrowserAdapter):
    def name(self): return "brave"
    def fetch(self, url): return WebResult()
    def search(self, query, max_results=10): return []
    def health(self): return {"status": "scaffold"}


class ExaAdapter(BrowserAdapter):
    def name(self): return "exa"
    def fetch(self, url): return WebResult()
    def search(self, query, max_results=10): return []
    def health(self): return {"status": "scaffold"}


class ArxivAdapter(BrowserAdapter):
    def name(self): return "arxiv"
    def fetch(self, url): return WebResult()
    def search(self, query, max_results=10): return []
    def health(self): return {"status": "scaffold"}


class GoogleDriveAdapter(BrowserAdapter):
    def name(self): return "google_drive"
    def fetch(self, url): return WebResult()
    def search(self, query, max_results=10): return []
    def health(self): return {"status": "scaffold"}


class InternetArchiveAdapter(BrowserAdapter):
    def name(self): return "internet_archive"
    def fetch(self, url): return WebResult()
    def search(self, query, max_results=10): return []
    def health(self): return {"status": "scaffold"}


class OpenLibraryAdapter(BrowserAdapter):
    def name(self): return "open_library"
    def fetch(self, url): return WebResult()
    def search(self, query, max_results=10): return []
    def health(self): return {"status": "scaffold"}


class CrossrefAdapter(BrowserAdapter):
    def name(self): return "crossref"
    def fetch(self, url): return WebResult()
    def search(self, query, max_results=10): return []
    def health(self): return {"status": "scaffold"}


class OpenAlexAdapter(BrowserAdapter):
    def name(self): return "openalex"
    def fetch(self, url): return WebResult()
    def search(self, query, max_results=10): return []
    def health(self): return {"status": "scaffold"}
