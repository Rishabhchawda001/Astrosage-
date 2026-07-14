"""Guardrails adapter interfaces."""
from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field


@dataclass
class GuardrailResult:
    passed: bool = True
    score: float = 1.0
    violations: list[str] = field(default_factory=list)
    details: dict = field(default_factory=dict)


class GuardrailAdapter(ABC):
    @abstractmethod
    def name(self) -> str: ...
    @abstractmethod
    def check(self, text: str, context: dict = None) -> GuardrailResult: ...
    @abstractmethod
    def health(self) -> dict: ...


class RAGASAdapter(GuardrailAdapter):
    def name(self): return "ragas"
    def check(self, text, context=None): return GuardrailResult()
    def health(self): return {"status": "scaffold"}


class DeepEvalAdapter(GuardrailAdapter):
    def name(self): return "deepeval"
    def check(self, text, context=None): return GuardrailResult()
    def health(self): return {"status": "scaffold"}


class LangfuseAdapter(GuardrailAdapter):
    def name(self): return "langfuse"
    def check(self, text, context=None): return GuardrailResult()
    def health(self): return {"status": "scaffold"}
