
"""
Technology Scoring Framework.

Scores every open-source project using weighted criteria.
"""
from __future__ import annotations
import json
from dataclasses import dataclass, field, asdict
from pathlib import Path
from typing import Optional

WEIGHTS = {
    "engineering_quality": 0.15, "performance": 0.15, "documentation": 0.10,
    "testing": 0.10, "security": 0.10, "community": 0.08,
    "offline_capability": 0.12, "maintainability": 0.08,
    "integration_effort": 0.07, "future_outlook": 0.05,
}

@dataclass
class TechScore:
    name: str
    category: str
    url: str = ""
    stars: int = 0
    forks: int = 0
    license: str = ""
    last_commit: str = ""
    maintainers: int = 0
    contributors: int = 0
    description: str = ""
    engineering_quality: float = 0.0
    performance: float = 0.0
    documentation: float = 0.0
    testing: float = 0.0
    security: float = 0.0
    community: float = 0.0
    offline_capability: float = 0.0
    maintainability: float = 0.0
    integration_effort: float = 0.0
    future_outlook: float = 0.0
    python_version: str = ""
    gpu_support: bool = False
    cpu_support: bool = True
    docker_support: bool = False
    offline_support: bool = False
    integration_complexity: str = "medium"
    maintenance_burden: str = "medium"
    astrosage_compatibility: str = "high"
    overall_score: float = 0.0
    recommendation: str = ""
    notes: str = ""

    def compute_overall(self) -> float:
        scores = {k: getattr(self, k) for k in WEIGHTS}
        self.overall_score = round(sum(scores[k] * WEIGHTS[k] for k in scores), 2)
        if self.overall_score >= 7.0:
            self.recommendation = "integrate"
        elif self.overall_score >= 5.0:
            self.recommendation = "evaluate"
        elif self.overall_score >= 3.0:
            self.recommendation = "catalog"
        else:
            self.recommendation = "reject"
        return self.overall_score

    def to_dict(self) -> dict:
        d = asdict(self)
        d["overall_score"] = self.overall_score
        d["recommendation"] = self.recommendation
        return d

class TechnologyCatalog:
    INTEGRATION_THRESHOLD = 5.0
    EVALUATE_THRESHOLD = 3.0

    def __init__(self, catalog_path: Optional[Path] = None):
        self.catalog_path = catalog_path
        self.technologies: dict[str, TechScore] = {}

    def add(self, tech: TechScore) -> None:
        tech.compute_overall()
        self.technologies[tech.name] = tech

    def get_by_category(self, category: str) -> list[TechScore]:
        return sorted([t for t in self.technologies.values() if t.category == category], key=lambda t: -t.overall_score)

    def get_integrated(self) -> list[TechScore]:
        return [t for t in self.technologies.values() if t.recommendation == "integrate"]

    def get_candidates(self) -> list[TechScore]:
        return [t for t in self.technologies.values() if t.overall_score >= self.EVALUATE_THRESHOLD]

    def get_categories(self) -> list[str]:
        return sorted(set(t.category for t in self.technologies.values()))

    def summary(self) -> dict:
        cats = {}
        for cat in self.get_categories():
            techs = self.get_by_category(cat)
            cats[cat] = {"count": len(techs), "top": techs[0].name if techs else None, "top_score": techs[0].overall_score if techs else 0}
        return {
            "total_technologies": len(self.technologies),
            "integrate": sum(1 for t in self.technologies.values() if t.recommendation == "integrate"),
            "evaluate": sum(1 for t in self.technologies.values() if t.recommendation == "evaluate"),
            "catalog": sum(1 for t in self.technologies.values() if t.recommendation == "catalog"),
            "reject": sum(1 for t in self.technologies.values() if t.recommendation == "reject"),
            "categories": cats,
        }

    def save(self, path: Optional[Path] = None):
        p = path or self.catalog_path
        if not p: return
        data = {"summary": self.summary(), "technologies": {name: t.to_dict() for name, t in self.technologies.items()}}
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(json.dumps(data, indent=2, ensure_ascii=False))

    @classmethod
    def load(cls, path: Path) -> "TechnologyCatalog":
        catalog = cls(catalog_path=path)
        if not path.exists(): return catalog
        data = json.loads(path.read_text())
        for name, td in data.get("technologies", {}).items():
            fields = {k: v for k, v in td.items() if k in TechScore.__dataclass_fields__}
            tech = TechScore(**fields)
            tech.overall_score = td.get("overall_score", 0)
            tech.recommendation = td.get("recommendation", "")
            catalog.technologies[name] = tech
        return catalog
