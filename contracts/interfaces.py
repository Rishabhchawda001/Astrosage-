"""Service contracts — ABC interfaces for all major services."""
from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any


@dataclass
class HealthStatus:
    status: str = "ok"
    details: dict = field(default_factory=dict)


class KnowledgeService(ABC):
    @abstractmethod
    def search(self, query: str, top_k: int = 10) -> list[dict]: ...
    @abstractmethod
    def get_document(self, doc_id: str) -> dict | None: ...
    @abstractmethod
    def list_documents(self, filters: dict = None) -> list[dict]: ...
    @abstractmethod
    def health(self) -> HealthStatus: ...


class RecoveryService(ABC):
    @abstractmethod
    def recover(self, document_id: str) -> dict: ...
    @abstractmethod
    def get_status(self, job_id: str) -> dict: ...
    @abstractmethod
    def health(self) -> HealthStatus: ...


class VerificationService(ABC):
    @abstractmethod
    def verify_answer(self, answer: str, sources: list[str]) -> dict: ...
    @abstractmethod
    def verify_citation(self, citation: str, source: str) -> dict: ...
    @abstractmethod
    def health(self) -> HealthStatus: ...


class CorpusService(ABC):
    @abstractmethod
    def statistics(self) -> dict: ...
    @abstractmethod
    def health(self) -> HealthStatus: ...


class OCRService(ABC):
    @abstractmethod
    def process(self, document_id: str) -> dict: ...
    @abstractmethod
    def health(self) -> HealthStatus: ...


class CitationService(ABC):
    @abstractmethod
    def track(self, citation: dict) -> str: ...
    @abstractmethod
    def verify(self, citation_id: str) -> dict: ...
    @abstractmethod
    def health(self) -> HealthStatus: ...


class KnowledgeGraphService(ABC):
    @abstractmethod
    def query(self, entity: str, depth: int = 2) -> dict: ...
    @abstractmethod
    def health(self) -> HealthStatus: ...


class ResearchService(ABC):
    @abstractmethod
    def search(self, query: str) -> list[dict]: ...
    @abstractmethod
    def health(self) -> HealthStatus: ...


class GitHubService(ABC):
    @abstractmethod
    def search_repos(self, query: str) -> list[dict]: ...
    @abstractmethod
    def health(self) -> HealthStatus: ...


class BrowserService(ABC):
    @abstractmethod
    def fetch(self, url: str) -> dict: ...
    @abstractmethod
    def search(self, query: str) -> list[dict]: ...
    @abstractmethod
    def health(self) -> HealthStatus: ...
