"""Prompt library with versioned, composable prompt variants."""

import json
import os
from dataclasses import dataclass, field, asdict
from typing import Optional


@dataclass
class PromptVariant:
    """A single prompt variant with full metadata."""
    id: str
    version: str = "1.0"
    scene: str = ""
    composition: str = ""
    lighting: str = ""
    historical_notes: str = ""
    camera_framing: str = ""
    negative_prompt: str = ""
    color_script: str = ""
    mood: str = ""
    output_width: int = 1536
    output_height: int = 640
    provider: str = "pollinations"
    provider_params: dict = field(default_factory=dict)
    tags: list[str] = field(default_factory=list)
    seed: Optional[int] = None

    @property
    def full_prompt(self) -> str:
        """Assemble the complete prompt from parts."""
        parts = [
            self.scene,
            self.composition,
            self.lighting,
            self.camera_framing,
            self.color_script,
            self.mood,
            self.historical_notes,
        ]
        return " ".join(p.strip() for p in parts if p.strip())

    def to_dict(self) -> dict:
        d = asdict(self)
        d["full_prompt"] = self.full_prompt
        return d


@dataclass
class PromptLibrary:
    """Collection of versioned prompt variants."""
    variants: list[PromptVariant] = field(default_factory=list)
    active_id: Optional[str] = None

    @property
    def active(self) -> Optional[PromptVariant]:
        if not self.active_id:
            return self.variants[0] if self.variants else None
        for v in self.variants:
            if v.id == self.active_id:
                return v
        return self.variants[0] if self.variants else None

    def get(self, variant_id: str) -> Optional[PromptVariant]:
        for v in self.variants:
            if v.id == variant_id:
                return v
        return None

    def add(self, variant: PromptVariant):
        self.variants.append(variant)

    def list_ids(self) -> list[str]:
        return [v.id for v in self.variants]

    def save(self, path: str):
        data = {
            "active_id": self.active_id,
            "variants": [asdict(v) for v in self.variants],
        }
        with open(path, "w") as f:
            json.dump(data, f, indent=2)

    @classmethod
    def load(cls, path: str) -> "PromptLibrary":
        with open(path) as f:
            data = json.load(f)
        lib = cls(active_id=data.get("active_id"))
        for vd in data.get("variants", []):
            # Remove computed fields that aren't constructor args
            vd.pop("full_prompt", None)
            lib.variants.append(PromptVariant(**vd))
        return lib


def load_library() -> PromptLibrary:
    """Load the prompt library, creating defaults if needed."""
    lib_path = os.path.join(os.path.dirname(__file__), "variants.json")

    if os.path.exists(lib_path):
        return PromptLibrary.load(lib_path)

    # Create default library with existing prompts
    lib = PromptLibrary()

    lib.add(PromptVariant(
        id="v1_classical_dawn",
        version="1.0",
        scene=(
            "Cinematic matte painting of dawn on the ancient Kurukshetra battlefield. "
            "A royal golden chariot drawn by four majestic white horses stands on a ridge. "
            "Krishna, a serene blue-skinned figure in golden crown and yellow robes, "
            "stands as charioteer holding the reins. Arjuna sits respectfully behind him. "
            "A triangular dharma flag flutters from the chariot pole."
        ),
        composition=(
            "In the far left distance, a monumental Himalayan peak with a seated meditation "
            "figure silhouette representing Shiva. Ancient stone temple with golden spire "
            "visible in the midground. Sea of morning clouds below the ridge. "
            "Atmospheric perspective with layered mountains."
        ),
        lighting=(
            "Golden sunrise light streaming from the right. "
            "Cool blue mountain shadows on the left. "
            "Volumetric golden sun rays. Atmospheric dust particles illuminated by sunlight."
        ),
        historical_notes=(
            "Style: AAA cinematic key art, museum-quality digital matte painting, "
            "physically believable sunrise lighting, no fantasy glow, no cartoon."
        ),
        camera_framing="16:9 aspect ratio, ultra wide composition, premium editorial quality.",
        negative_prompt="fantasy glow, cartoon, anime, AI artifacts, neon, excessive particles",
        color_script="cloud white, ivory, warm marble, muted gold, bronze, morning blue",
        mood="serene, sacred, timeless, premium",
        output_width=1536,
        output_height=864,
        seed=101,
        tags=["dawn", "classical", "wide"],
    ))

    lib.add(PromptVariant(
        id="v3_painterly_tradition",
        version="1.0",
        scene=(
            "A majestic digital matte painting in the tradition of classical Indian art. "
            "Dawn light on the sacred Kurukshetra plain. "
            "A resplendent golden chariot drawn by four powerful white horses. "
            "Lord Krishna, divine charioteer, stands with serene confidence, "
            "golden crown with peacock feather, yellow silk garments. "
            "Prince Arjuna sits with folded hands in deep contemplation. "
            "A saffron dharma flag ripples in the morning breeze."
        ),
        composition=(
            "In the distant left, the eternal Mount Kailash rises, "
            "with the faint silhouette of Lord Shiva in deep meditation. "
            "Ancient Hindu stone temple with ornate spire in the warm midground. "
            "Rolling Himalayan ridges in atmospheric perspective."
        ),
        lighting=(
            "Golden volumetric light rays. Morning mist in valleys. "
            "Photorealistic sunrise. Physically accurate atmospheric scattering."
        ),
        historical_notes=(
            "Style: museum-quality, gallery-worthy, hand-painted feel. "
            "Cinematic 2.39:1 widescreen composition."
        ),
        camera_framing="Ultra wide cinematic composition, premium editorial quality.",
        negative_prompt="fantasy glow, cartoon, anime, AI artifacts, neon, excessive particles, glowing auras",
        color_script="warm gold to cool blue-grey, ivory, warm marble, sandstone, bronze",
        mood="serene, sacred, timeless, premium, scholarly",
        output_width=1536,
        output_height=640,
        seed=303,
        tags=["painterly", "classical", "active"],
        provider_params={"seed": 303},
    ))

    lib.active_id = "v3_painterly_tradition"
    lib.save(lib_path)
    return lib
