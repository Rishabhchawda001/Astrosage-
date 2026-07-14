"""Research adapter interfaces."""
from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field


@dataclass
class ResearchResult:
    source: str = ""
    title: str = ""
    content: str = ""
    url: str = ""
    metadata: dict = field(default_factory=dict)


class ResearchAdapter(ABC):
    @abstractmethod
    def name(self) -> str: ...
    @abstractmethod
    def search(self, query: str, max_results: int = 10) -> list[ResearchResult]: ...
    @abstractmethod
    def health(self) -> dict: ...
