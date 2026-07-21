#!/usr/bin/env python3
"""
AstroSage Hero Artwork Generator
Uses Pollinations.ai free API for image generation.
"""

import urllib.request
import urllib.parse
import os
import sys
import json
import time

OUTPUT_DIR = os.path.join(os.path.dirname(__file__), "..", "public", "hero-artwork")
os.makedirs(OUTPUT_DIR, exist_ok=True)

# ── Prompts ──
# Each prompt is crafted for a specific artistic vision.
# We generate multiple candidates and evaluate them.

PROMPTS = [
    {
        "id": "v1_classical_dawn",
        "prompt": (
            "Cinematic matte painting of dawn on the ancient Kurukshetra battlefield. "
            "A royal golden chariot drawn by four majestic white horses stands on a ridge. "
            "Krishna, a serene blue-skinned figure in golden crown and yellow robes, "
            "stands as charioteer holding the reins. Arjuna sits respectfully behind him. "
            "A triangular dharma flag flutters from the chariot pole. "
            "In the far left distance, a monumental Himalayan peak with a seated meditation "
            "figure silhouette representing Shiva. Ancient stone temple with golden spire "
            "visible in the midground. Golden sunrise light streaming from the right. "
            "Cool blue mountain shadows on the left. Sea of morning clouds below the ridge. "
            "Atmospheric perspective with layered mountains. "
            "Style: AAA cinematic key art, museum-quality digital matte painting, "
            "physically believable sunrise lighting, no fantasy glow, no cartoon. "
            "Color palette: cloud white, ivory, warm marble, muted gold, bronze, morning blue. "
            "16:9 aspect ratio, ultra wide composition, premium editorial quality."
        ),
        "width": 1536,
        "height": 864,
        "seed": 101,
    },
    {
        "id": "v2_epic_composition",
        "prompt": (
            "Original cinematic digital matte painting. Early morning Himalayan dawn. "
            "Center-right: a golden royal chariot with four white horses, "
            "Krishna standing tall as charioteer in golden crown and silk dhoti, "
            "Arjuna seated in reverent posture. Dharma flag with gentle movement. "
            "Far left: massive snow-capped Mount Kailash with a subtle seated "
            "meditation figure silhouette in deep blue-grey tones. "
            "Ancient stone temple with carved shikhara in the midground. "
            "Layers of Himalayan ridges receding into golden morning haze. "
            "Sea of clouds filling the valleys below. "
            "Volumetric golden sun rays from the upper right. "
            "Atmospheric dust particles illuminated by sunlight. "
            "Style: high-end matte painting, AAA game cinematic, "
            "photorealistic lighting, no artificial effects, no fantasy elements. "
            "Museum quality, luxury editorial, premium craftsmanship. "
            "Warm gold highlights, cool blue-grey shadows. "
            "Ultra wide 21:9 cinematic aspect ratio."
        ),
        "width": 1536,
        "height": 640,
        "seed": 202,
    },
    {
        "id": "v3_painterly_tradition",
        "prompt": (
            "A majestic digital matte painting in the tradition of classical Indian art. "
            "Dawn light on the sacred Kurukshetra plain. "
            "A resplendent golden chariot drawn by four powerful white horses. "
            "Lord Krishna, divine charioteer, stands with serene confidence, "
            "golden crown with peacock feather, yellow silk garments. "
            "Prince Arjuna sits with folded hands in deep contemplation. "
            "A saffron dharma flag ripples in the morning breeze. "
            "In the distant left, the eternal Mount Kailash rises, "
            "with the faint silhouette of Lord Shiva in deep meditation. "
            "Ancient Hindu stone temple with ornate spire in the warm midground. "
            "Rolling Himalayan ridges in atmospheric perspective. "
            "Golden volumetric light rays. Morning mist in valleys. "
            "Photorealistic sunrise. No fantasy elements. No glowing auras. "
            "Physically accurate atmospheric scattering. "
            "Cinematic 2.39:1 widescreen composition. "
            "Color temperature: warm gold to cool blue-grey. "
            "Museum-quality, gallery-worthy, hand-painted feel."
        ),
        "width": 1536,
        "height": 640,
        "seed": 303,
    },
    {
        "id": "v4_editorial_wide",
        "prompt": (
            "Ultra-wide cinematic matte painting, 21:9 aspect ratio. "
            "Sacred dawn on an ancient Indian plain. "
            "Right side: golden chariot with four white horses in dynamic but calm composition. "
            "Krishna standing as divine charioteer, serene expression, "
            "ornate golden mukuta crown, flowing yellow silk. "
            "Arjuna seated respectfully, warrior posture but contemplative mood. "
            "Dharma flag with natural fabric movement. "
            "Left side: distant Himalayan mountain range receding into mist. "
            "The tallest peak (Kailash) has a subtle meditating figure silhouette. "
            "Center: ancient stone temple with carved details catching golden light. "
            "Atmosphere: golden hour, volumetric light, atmospheric haze, "
            "cloud sea in valleys, morning dust motes. "
            "No fantasy. No magic. No glowing effects. "
            "Physically accurate sunrise cinematography. "
            "Premium editorial photography composition. "
            "Color palette: ivory, warm marble, sandstone gold, bronze, "
            "morning blue-grey, cloud white. "
            "Hand-crafted museum quality. Not AI-generated aesthetic."
        ),
        "width": 1536,
        "height": 640,
        "seed": 404,
    },
]


def generate_image(prompt_data):
    """Generate an image using Pollinations.ai."""
    encoded = urllib.parse.quote(prompt_data["prompt"])
    url = (
        f"https://image.pollinations.ai/prompt/{encoded}"
        f"?width={prompt_data['width']}"
        f"&height={prompt_data['height']}"
        f"&nologo=true"
        f"&seed={prompt_data['seed']}"
    )

    outpath = os.path.join(OUTPUT_DIR, f"{prompt_data['id']}.jpg")
    print(f"Generating {prompt_data['id']}...")

    try:
        req = urllib.request.Request(url, headers={"User-Agent": "AstroSage/1.0"})
        with urllib.request.urlopen(req, timeout=120) as resp:
            data = resp.read()
            with open(outpath, "wb") as f:
                f.write(data)
        size_kb = os.path.getsize(outpath) / 1024
        print(f"  ✓ Saved {outpath} ({size_kb:.0f} KB)")
        return outpath
    except Exception as e:
        print(f"  ✗ Failed: {e}")
        return None


if __name__ == "__main__":
    results = []
    for p in PROMPTS:
        path = generate_image(p)
        results.append({"id": p["id"], "path": path, "prompt": p["prompt"][:100]})
        time.sleep(2)  # polite delay

    print(f"\nGenerated {sum(1 for r in results if r['path'])} images")
    for r in results:
        status = "✓" if r["path"] else "✗"
        print(f"  {status} {r['id']}")
