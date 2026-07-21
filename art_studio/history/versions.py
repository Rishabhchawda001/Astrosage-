"""Hero artwork version history.

Every accepted artwork becomes a permanent version.
Previous versions are never overwritten.
"""

import json
import os
import shutil
from dataclasses import dataclass, field, asdict
from typing import Optional
from datetime import datetime


@dataclass
class HeroVersion:
    """A single version of the hero artwork."""
    version: str  # e.g., "v1", "v2"
    image_filename: str
    prompt_id: str
    provider: str
    generation_settings: dict = field(default_factory=dict)
    quality_scores: dict = field(default_factory=dict)
    acceptance_notes: str = ""
    integration_commit: str = ""
    created_at: str = ""
    is_active: bool = False

    def to_dict(self) -> dict:
        return asdict(self)


class VersionManager:
    """Manages hero artwork versions."""

    def __init__(self, studio_root: str):
        self.studio_root = studio_root
        self.history_path = os.path.join(studio_root, "history", "versions.json")
        self.generated_dir = os.path.join(studio_root, "generated")
        self.exports_dir = os.path.join(studio_root, "exports")
        os.makedirs(self.generated_dir, exist_ok=True)
        os.makedirs(self.exports_dir, exist_ok=True)
        self._data = self._load()

    def _load(self) -> dict:
        if os.path.exists(self.history_path):
            with open(self.history_path) as f:
                return json.load(f)
        return {"versions": [], "next_version": 1}

    def _save(self):
        with open(self.history_path, "w") as f:
            json.dump(self._data, f, indent=2)

    def next_version_id(self) -> str:
        n = self._data["next_version"]
        return f"v{n}"

    def add_version(
        self,
        image_path: str,
        prompt_id: str,
        provider: str,
        generation_settings: Optional[dict] = None,
        quality_scores: Optional[dict] = None,
        acceptance_notes: str = "",
        integration_commit: str = "",
        activate: bool = False,
    ) -> HeroVersion:
        """Register a new artwork version."""
        vid = self.next_version_id()
        filename = f"{vid}_{prompt_id}.jpg"

        # Copy image to generated/
        dest = os.path.join(self.generated_dir, filename)
        if os.path.exists(image_path) and image_path != dest:
            shutil.copy2(image_path, dest)

        # Copy to exports/ for easy access
        export_dest = os.path.join(self.exports_dir, filename)
        if os.path.exists(dest):
            shutil.copy2(dest, export_dest)

        version = HeroVersion(
            version=vid,
            image_filename=filename,
            prompt_id=prompt_id,
            provider=provider,
            generation_settings=generation_settings or {},
            quality_scores=quality_scores or {},
            acceptance_notes=acceptance_notes,
            integration_commit=integration_commit,
            created_at=datetime.utcnow().isoformat() + "Z",
            is_active=activate,
        )

        # Deactivate others if this one is active
        if activate:
            for v in self._data["versions"]:
                v["is_active"] = False

        self._data["versions"].append(version.to_dict())
        self._data["next_version"] = self._data["next_version"] + 1
        self._save()
        return version

    def get_active(self) -> Optional[HeroVersion]:
        for vd in self._data["versions"]:
            if vd.get("is_active"):
                return HeroVersion(**vd)
        return None

    def get_all(self) -> list[HeroVersion]:
        return [HeroVersion(**vd) for vd in self._data["versions"]]

    def get_image_path(self, version: HeroVersion) -> str:
        return os.path.join(self.generated_dir, version.image_filename)

    def export_active_to_frontend(self, frontend_public: str) -> Optional[str]:
        """Copy the active version to the frontend public directory."""
        active = self.get_active()
        if not active:
            return None
        src = self.get_image_path(active)
        dest_dir = os.path.join(frontend_public, "hero-artwork")
        os.makedirs(dest_dir, exist_ok=True)
        dest = os.path.join(dest_dir, "hero_active.jpg")
        if os.path.exists(src):
            shutil.copy2(src, dest)
            return dest
        return None
