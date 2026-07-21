"""Master pipeline for artwork generation, evaluation, and integration."""

import json
import os
import time
from dataclasses import dataclass
from typing import Optional

from ..providers import get_provider, GenerationRequest
from ..prompts import get_library
from ..evaluation.scorer import ArtworkScorer, QualityReport, compare_reports
from ..history.versions import VersionManager


@dataclass
class PipelineConfig:
    studio_root: str
    frontend_public: str
    provider_name: str = "pollinations"
    auto_score: bool = True
    auto_version: bool = True
    auto_integrate: bool = False
    generate_variants: int = 1
    delay_between_generations: float = 2.0


class ArtPipeline:
    """End-to-end artwork generation and integration pipeline."""

    def __init__(self, config: PipelineConfig):
        self.config = config
        self.provider = get_provider(config.provider_name)
        self.library = get_library()
        self.scorer = ArtworkScorer()
        self.versions = VersionManager(config.studio_root)
        self.output_dir = os.path.join(config.studio_root, "generated")
        os.makedirs(self.output_dir, exist_ok=True)

    def generate(
        self,
        variant_id: Optional[str] = None,
        seed_override: Optional[int] = None,
    ) -> list[dict]:
        """Generate artwork from a prompt variant.

        Returns a list of generation results with paths and metadata.
        """
        variant = self.library.get(variant_id) if variant_id else self.library.active
        if not variant:
            raise ValueError("No prompt variant specified and no active variant set")

        results = []
        num = self.config.generate_variants

        for i in range(num):
            seed = seed_override if seed_override is not None else variant.seed
            if seed and num > 1:
                seed = seed + i

            request = GenerationRequest(
                prompt=variant.full_prompt,
                negative_prompt=variant.negative_prompt,
                width=variant.output_width,
                height=variant.output_height,
                seed=seed,
                provider=variant.provider,
                extra_params=variant.provider_params,
            )

            print(f"[{i+1}/{num}] Generating with {self.provider.name} "
                  f"(seed={seed}, {variant.output_width}x{variant.output_height})...")

            result = self.provider.generate_with_timing(request)

            if result.success:
                outpath = os.path.join(
                    self.output_dir,
                    f"{variant.id}_seed{seed}.jpg"
                )
                with open(outpath, "wb") as f:
                    f.write(result.image_bytes)
                result.image_path = outpath
                result.file_size_kb = os.path.getsize(outpath) / 1024
                print(f"  ✓ Saved {outpath} ({result.file_size_kb:.0f} KB, "
                      f"{result.generation_time_ms:.0f}ms)")
            else:
                print(f"  ✗ Failed: {result.error}")

            results.append({
                "variant_id": variant.id,
                "seed": seed,
                "result": result,
            })

            if i < num - 1:
                time.sleep(self.config.delay_between_generations)

        return results

    def evaluate(self, image_path: str, prompt_id: str) -> QualityReport:
        """Run quality evaluation on an image."""
        report = self.scorer.score_heuristic(image_path, prompt_id)
        print(f"  Evaluation: {report.overall_score:.2f} — {report.recommendation}")
        return report

    def evaluate_manual(
        self,
        image_path: str,
        prompt_id: str,
        scores: dict[str, float],
        notes: str = "",
    ) -> QualityReport:
        """Run manual scoring."""
        report = self.scorer.score_manual(image_path, prompt_id, scores, notes)
        print(f"  Manual score: {report.overall_score:.2f} — {report.recommendation}")
        return report

    def accept_version(
        self,
        image_path: str,
        prompt_id: str,
        quality_report: Optional[QualityReport] = None,
        notes: str = "",
        commit: str = "",
    ) -> dict:
        """Accept an artwork and register it as a version."""
        scores = {}
        if quality_report:
            scores = {d.name: d.score for d in quality_report.dimensions}

        version = self.versions.add_version(
            image_path=image_path,
            prompt_id=prompt_id,
            provider=self.provider.name,
            quality_scores=scores,
            acceptance_notes=notes,
            integration_commit=commit,
            activate=True,
        )

        # Export to frontend
        exported = self.versions.export_active_to_frontend(self.config.frontend_public)
        print(f"  ✓ Version {version.version} registered and exported")
        if exported:
            print(f"  ✓ Exported to {exported}")

        return {
            "version": version.to_dict(),
            "exported_path": exported,
        }

    def status(self) -> dict:
        """Get current pipeline status."""
        versions = self.versions.get_all()
        active = self.versions.get_active()
        return {
            "provider": self.provider.name,
            "provider_available": self.provider.health_check(),
            "active_variant": self.library.active.id if self.library.active else None,
            "total_versions": len(versions),
            "active_version": active.version if active else None,
            "versions": [v.to_dict() for v in versions],
            "prompt_variants": self.library.list_ids(),
        }
