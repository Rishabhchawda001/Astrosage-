"""
Tier-Aware Document Router — Language-based processing tiers.

Reads configuration from config/processing_tiers.json.
Routes documents to appropriate processing depth based on detected language.

Tier 1: Full Processing (English, Hindi, Sanskrit)
Tier 2: Deferred (Register + preserve, skip expensive OCR/parsing)
Tier 3: Media (Register only)
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Optional


class TierConfig:
    """Loads and manages processing tier configuration."""

    def __init__(self, config_path: Optional[Path] = None):
        if config_path is None:
            config_path = Path(__file__).parent.parent.parent.parent / "config" / "processing_tiers.json"
        self.config_path = config_path
        self.config = self._load_config()

    def _load_config(self) -> dict:
        if self.config_path.exists():
            return json.loads(self.config_path.read_text())
        # Default config
        return {
            "version": "1.0.0",
            "tiers": {
                "tier1": {"name": "Full Processing", "languages": ["english", "hindi", "sanskrit"], "scripts": ["latin", "devanagari"]},
                "tier2": {"name": "Deferred", "languages": ["telugu", "kannada", "tamil", "malayalam", "gujarati", "bengali", "punjabi"]},
                "tier3": {"name": "Media", "extensions": [".mp3", ".mp4", ".jpg", ".png", ".zip"]},
            },
            "routing": {"fallback_tier": "tier2", "unknown_language_tier": "tier2"},
        }

    def get_tier_for_language(self, language: str) -> str:
        """Determine processing tier for a detected language."""
        lang_lower = language.lower()
        tier1_langs = [l.lower() for l in self.config["tiers"]["tier1"].get("languages", [])]
        if lang_lower in tier1_langs:
            return "tier1"
        tier2_langs = [l.lower() for l in self.config["tiers"]["tier2"].get("languages", [])]
        if lang_lower in tier2_langs:
            return "tier2"
        return self.config["routing"].get("fallback_tier", "tier2")

    def get_tier_for_extension(self, extension: str) -> str:
        """Determine processing tier for a file extension."""
        tier3_exts = [e.lower() for e in self.config["tiers"]["tier3"].get("extensions", [])]
        if extension.lower() in tier3_exts:
            return "tier3"
        return "tier1"

    def get_tier_config(self, tier: str) -> dict:
        """Get configuration for a specific tier."""
        return self.config["tiers"].get(tier, {})

    def should_ocr(self, tier: str) -> bool:
        """Check if OCR should be run for this tier."""
        tier_cfg = self.get_tier_config(tier)
        return tier_cfg.get("processing", {}).get("ocr", False)

    def should_parse(self, tier: str) -> bool:
        """Check if parsing should be run for this tier."""
        tier_cfg = self.get_tier_config(tier)
        return tier_cfg.get("processing", {}).get("parsing", False)

    def should_extract_metadata(self, tier: str) -> bool:
        """Check if metadata extraction should be run."""
        tier_cfg = self.get_tier_config(tier)
        return tier_cfg.get("processing", {}).get("metadata_extraction", True)

    def should_write_bronze(self, tier: str) -> bool:
        """Check if bronze output should be written."""
        tier_cfg = self.get_tier_config(tier)
        return tier_cfg.get("processing", {}).get("bronze", False)

    def should_write_silver(self, tier: str) -> bool:
        """Check if silver output should be written."""
        tier_cfg = self.get_tier_config(tier)
        return tier_cfg.get("processing", {}).get("silver", False)

    def get_tier_name(self, tier: str) -> str:
        """Get human-readable tier name."""
        return self.get_tier_config(tier).get("name", tier)

    def register_document(self, filepath: Path, tier: str, language: str, script: str, metadata: dict) -> dict:
        """Register a document in the Knowledge Registry with tier information."""
        return {
            "filepath": str(filepath),
            "tier": tier,
            "tier_name": self.get_tier_name(tier),
            "language": language,
            "script": script,
            "metadata": metadata,
            "processing_depth": self.get_tier_config(tier).get("processing", {}),
            "registered": True,
        }
