"""
Confidence Engine — Aggregates confidence scores from all pipeline stages.

Supports:
  - OCR confidence
  - Parser confidence
  - Metadata confidence
  - Recovery confidence
  - Edition agreement confidence
  - Verification confidence
  - Overall trust score

All weights configurable via JSON configuration.
"""
from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional


@dataclass
class ConfidenceComponent:
    """A single confidence measurement."""
    name: str
    score: float  # 0.0 to 1.0
    weight: float = 1.0
    metadata: dict = field(default_factory=dict)


@dataclass
class ConfidenceProfile:
    """Complete confidence profile for a knowledge object."""
    object_id: str
    components: list[ConfidenceComponent] = field(default_factory=list)
    overall_score: float = 0.0
    min_component: str = ""
    max_component: str = ""

    def compute_overall(self) -> float:
        if not self.components:
            return 0.0
        total_weight = sum(c.weight for c in self.components)
        if total_weight == 0:
            return 0.0
        self.overall_score = sum(c.score * c.weight for c in self.components) / total_weight
        scores = {c.name: c.score for c in self.components}
        self.min_component = min(scores, key=scores.get) if scores else ""
        self.max_component = max(scores, key=scores.get) if scores else ""
        return self.overall_score


class ConfidenceEngine:
    """
    Aggregates confidence scores from all pipeline stages.

    All weights are loaded from configuration.
    Supports adding components dynamically.
    """

    DEFAULT_WEIGHTS = {
        "ocr": 0.25,
        "parser": 0.15,
        "metadata": 0.10,
        "recovery": 0.25,
        "edition_agreement": 0.15,
        "verification": 0.10,
    }

    def __init__(self, config_path: Optional[str] = None):
        self.weights = dict(self.DEFAULT_WEIGHTS)
        if config_path:
            self._load_config(config_path)

    def _load_config(self, path: str):
        filepath = Path(path)
        if filepath.exists():
            with open(filepath, "r") as f:
                data = json.load(f)
            if "weights" in data:
                self.weights.update(data["weights"])

    def create_profile(self, object_id: str) -> ConfidenceProfile:
        return ConfidenceProfile(object_id=object_id)

    def add_component(self, profile: ConfidenceProfile, name: str, score: float, metadata: Optional[dict] = None):
        weight = self.weights.get(name, 1.0)
        profile.components.append(ConfidenceComponent(
            name=name,
            score=max(0.0, min(1.0, score)),
            weight=weight,
            metadata=metadata or {},
        ))

    def compute(self, profile: ConfidenceProfile) -> float:
        return profile.compute_overall()

    def get_confidence_level(self, score: float) -> str:
        if score >= 0.8:
            return "high"
        elif score >= 0.5:
            return "medium"
        elif score >= 0.3:
            return "low"
        else:
            return "very_low"

    def save_config(self, path: str):
        with open(path, "w") as f:
            json.dump({"weights": self.weights}, f, indent=2)
