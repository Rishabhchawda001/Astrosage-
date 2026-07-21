"""Provider abstraction layer for image generation."""

from .base import ImageProvider, GenerationRequest, GenerationResult
from .pollinations import PollinationsProvider

PROVIDERS = {
    "pollinations": PollinationsProvider,
}

def get_provider(name: str) -> ImageProvider:
    """Get a provider instance by name."""
    if name not in PROVIDERS:
        raise ValueError(f"Unknown provider: {name}. Available: {list(PROVIDERS.keys())}")
    return PROVIDERS[name]()

def list_providers() -> list[str]:
    return list(PROVIDERS.keys())
