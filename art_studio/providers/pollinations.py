"""Pollinations.ai provider adapter."""

import urllib.request
import urllib.parse
from .base import ImageProvider, GenerationRequest, GenerationResult


class PollinationsProvider(ImageProvider):
    """Free image generation via Pollinations.ai."""

    BASE_URL = "https://image.pollinations.ai/prompt"

    @property
    def name(self) -> str:
        return "pollinations"

    @property
    def description(self) -> str:
        return "Free AI image generation via Pollinations.ai (no API key required)"

    def generate(self, request: GenerationRequest) -> GenerationResult:
        encoded = urllib.parse.quote(request.prompt)
        url = (
            f"{self.BASE_URL}/{encoded}"
            f"?width={request.width}"
            f"&height={request.height}"
            f"&nologo=true"
        )
        if request.seed is not None:
            url += f"&seed={request.seed}"

        try:
            req = urllib.request.Request(
                url,
                headers={"User-Agent": "AstroSage-ArtStudio/1.0"},
            )
            with urllib.request.urlopen(req, timeout=180) as resp:
                data = resp.read()

            return GenerationResult(
                success=True,
                image_bytes=data,
                width=request.width,
                height=request.height,
                provider=self.name,
                prompt=request.prompt,
                seed=request.seed,
                file_size_kb=len(data) / 1024,
                metadata={"url": url},
            )
        except Exception as e:
            return GenerationResult(
                success=False,
                provider=self.name,
                prompt=request.prompt,
                seed=request.seed,
                error=str(e),
            )

    def health_check(self) -> bool:
        try:
            url = f"{self.BASE_URL}/test?width=64&height=64&nologo=true&seed=1"
            req = urllib.request.Request(
                url, headers={"User-Agent": "AstroSage-ArtStudio/1.0"}
            )
            with urllib.request.urlopen(req, timeout=30) as resp:
                return resp.status == 200
        except Exception:
            return False
