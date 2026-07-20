"""Golden dataset loader and validator."""
import json
from pathlib import Path
from dataclasses import dataclass, field
from typing import Optional


@dataclass
class EvalQuestion:
    id: str
    category: str
    question: str
    expected_entities: list[str] = field(default_factory=list)
    expected_scriptures: list[str] = field(default_factory=list)
    expected_relationships: list[str] = field(default_factory=list)
    difficulty: str = "medium"
    min_confidence: str = "medium"
    max_confidence: Optional[str] = None
    min_evidence_sources: int = 0
    max_evidence_sources: Optional[int] = None
    source: str = ""
    notes: str = ""


class GoldenDatasetLoader:
    def __init__(self, dataset_path: str = "evaluation/golden_dataset.json"):
        self.path = Path(dataset_path)
        self._data = None
        self._questions = None

    def load(self) -> "GoldenDatasetLoader":
        with open(self.path) as f:
            self._data = json.load(f)
        self._questions = [
            EvalQuestion(**q) for q in self._data["questions"]
        ]
        return self

    @property
    def questions(self) -> list[EvalQuestion]:
        if self._questions is None:
            self.load()
        return self._questions

    @property
    def version(self) -> str:
        if self._data is None:
            self.load()
        return self._data.get("version", "unknown")

    @property
    def total(self) -> int:
        return len(self.questions)

    def by_category(self, category: str) -> list[EvalQuestion]:
        return [q for q in self.questions if q.category == category]

    def by_difficulty(self, difficulty: str) -> list[EvalQuestion]:
        return [q for q in self.questions if q.difficulty == difficulty]

    @property
    def categories(self) -> dict[str, int]:
        cats: dict[str, int] = {}
        for q in self.questions:
            cats[q.category] = cats.get(q.category, 0) + 1
        return cats

    def validate(self) -> dict:
        issues = []
        ids_seen = set()
        for q in self.questions:
            if q.id in ids_seen:
                issues.append(f"Duplicate ID: {q.id}")
            ids_seen.add(q.id)
            if not q.question.strip():
                issues.append(f"Empty question: {q.id}")
            if q.min_evidence_sources < 0:
                issues.append(f"Negative min_evidence_sources: {q.id}")
        return {
            "valid": len(issues) == 0,
            "total_questions": self.total,
            "categories": self.categories,
            "issues": issues,
        }
