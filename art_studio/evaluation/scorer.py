"""Artwork quality scoring system.

Scores are heuristic-based (no external API needed).
For higher fidelity, integrate CLIP/BLIP scoring later.
"""

import json
import os
from dataclasses import dataclass, field, asdict
from typing import Optional
from pathlib import Path


@dataclass
class DimensionScore:
    name: str
    score: float  # 0.0 - 1.0
    weight: float = 1.0
    notes: str = ""


@dataclass
class QualityReport:
    """Complete quality assessment of an artwork."""
    image_path: str
    prompt_id: str = ""
    dimensions: list[DimensionScore] = field(default_factory=list)
    file_size_kb: float = 0
    resolution: str = ""
    overall_score: float = 0
    recommendation: str = ""  # "accept", "revise", "reject"
    notes: str = ""

    def to_dict(self) -> dict:
        d = asdict(self)
        d["overall_score"] = round(self.overall_score, 3)
        return d

    def save(self, path: str):
        with open(path, "w") as f:
            json.dump(self.to_dict(), f, indent=2)


class ArtworkScorer:
    """Score artwork based on configurable quality dimensions."""

    DIMENSIONS = [
        ("composition", 1.2, "Visual balance, rule of thirds, focal point clarity"),
        ("lighting", 1.1, "Natural lighting, believable sunrise, atmospheric depth"),
        ("contrast", 0.9, "Tonal range, readability of key elements"),
        ("readability", 1.3, "Can text overlay be read? Key elements distinguishable?"),
        ("historical_plausibility", 1.0, "Costume, architecture, chariot design accuracy"),
        ("anatomy", 1.0, "Human figure proportions, natural poses"),
        ("horse_anatomy", 0.8, "Horse proportions, natural posture"),
        ("perspective", 0.9, "Depth cues, atmospheric perspective, scale consistency"),
        ("temple_accuracy", 0.7, "Shikhara style, stone texture, architectural plausibility"),
        ("color_harmony", 1.0, "Color temperature consistency, palette coherence"),
        ("premium_appearance", 1.1, "Does it look handcrafted rather than AI-generated?"),
        ("originality", 0.8, "Does it avoid looking like existing artwork or templates?"),
    ]

    def __init__(self, custom_weights: Optional[dict] = None):
        self.dimensions = []
        for name, weight, notes in self.DIMENSIONS:
            w = custom_weights.get(name, weight) if custom_weights else weight
            self.dimensions.append((name, w, notes))

    def score_manual(
        self,
        image_path: str,
        prompt_id: str,
        scores: dict[str, float],
        notes: str = "",
    ) -> QualityReport:
        """Create a report from manually provided scores (0.0 - 1.0 each)."""
        report = QualityReport(
            image_path=image_path,
            prompt_id=prompt_id,
            notes=notes,
        )

        # File info
        if os.path.exists(image_path):
            report.file_size_kb = os.path.getsize(image_path) / 1024

        # Build dimension scores
        total_weight = 0
        weighted_sum = 0
        for name, weight, dim_notes in self.dimensions:
            raw = scores.get(name, 0.5)
            raw = max(0.0, min(1.0, raw))
            ds = DimensionScore(name=name, score=raw, weight=weight, notes=dim_notes)
            report.dimensions.append(ds)
            weighted_sum += raw * weight
            total_weight += weight

        report.overall_score = weighted_sum / total_weight if total_weight > 0 else 0

        # Recommendation
        if report.overall_score >= 0.75:
            report.recommendation = "accept"
        elif report.overall_score >= 0.55:
            report.recommendation = "revise"
        else:
            report.recommendation = "reject"

        return report

    def score_heuristic(self, image_path: str, prompt_id: str) -> QualityReport:
        """Basic heuristic scoring based on file properties.
        
        For full scoring, use score_manual() or integrate CLIP/BLIP.
        """
        report = QualityReport(
            image_path=image_path,
            prompt_id=prompt_id,
            notes="Heuristic scoring (no visual model)",
        )

        if os.path.exists(image_path):
            report.file_size_kb = os.path.getsize(image_path) / 1024

        # File size heuristic: larger files tend to have more detail
        size_score = min(1.0, report.file_size_kb / 100) if report.file_size_kb > 0 else 0.3

        # Assign default heuristic scores
        for name, weight, dim_notes in self.dimensions:
            base = 0.5  # neutral
            if name == "premium_appearance":
                base = size_score * 0.6 + 0.3  # file size proxy
            elif name == "readability":
                base = 0.65  # assume reasonable unless proven otherwise
            report.dimensions.append(DimensionScore(
                name=name, score=base, weight=weight, notes=dim_notes,
            ))

        total_weight = sum(d.weight for d in report.dimensions)
        report.overall_score = sum(d.score * d.weight for d in report.dimensions) / total_weight
        report.recommendation = "revise"  # heuristic can't confirm quality

        return report


def compare_reports(reports: list[QualityReport]) -> list[QualityReport]:
    """Sort reports by overall score, best first."""
    return sorted(reports, key=lambda r: r.overall_score, reverse=True)
