"""Verification plugins — ABC-based interfaces for verification."""
from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import Enum
from typing import Optional


class VerificationOutcome(str, Enum):
    VERIFIED = "verified"
    REJECTED = "rejected"
    CONFLICT = "conflict"
    MANUAL_REVIEW = "manual_review"


@dataclass
class VerificationRequest:
    original: str
    candidate: str
    evidence: list[str] = field(default_factory=list)
    metadata: dict = field(default_factory=dict)


@dataclass
class VerificationResponse:
    outcome: VerificationOutcome
    confidence: float = 0.0
    reason: str = ""
    details: dict = field(default_factory=dict)


class VerificationPlugin(ABC):
    """Abstract interface for verification plugins."""

    @abstractmethod
    def name(self) -> str:
        ...

    @abstractmethod
    def verify(self, request: VerificationRequest) -> VerificationResponse:
        ...

    @abstractmethod
    def health_check(self) -> bool:
        ...
