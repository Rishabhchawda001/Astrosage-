"""Recovery plugins — ABC-based interfaces for recovery implementations."""
from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Optional


@dataclass
class RecoveryCandidate:
    """A candidate recovery text."""
    text: str
    source: str = ""
    confidence: float = 0.0
    evidence: list[str] = field(default_factory=list)


class RecoveryPlugin(ABC):
    """Abstract interface for recovery plugins."""

    @abstractmethod
    def name(self) -> str:
        ...

    @abstractmethod
    def version(self) -> str:
        ...

    @abstractmethod
    def recover(self, original_text: str, context: dict = None) -> list[RecoveryCandidate]:
        """Attempt to recover/improve the original text."""
        ...

    @abstractmethod
    def health_check(self) -> bool:
        ...
