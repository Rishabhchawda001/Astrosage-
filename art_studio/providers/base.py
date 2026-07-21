"""Base provider interface for image generation."""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Optional
import time


@dataclass
class GenerationRequest:
    """A request to generate an image."""
    prompt: str
    negative_prompt: str = ""
    width: int = 1536
    height: int = 640
    seed: Optional[int] = None
    steps: Optional[int] = None
    cfg_scale: Optional[float] = None
    model: Optional[str] = None
    extra_params: dict = field(default_factory=dict)


@dataclass
class GenerationResult:
    """Result of an image generation."""
    success: bool
    image_path: Optional[str] = None
    image_bytes: Optional[bytes] = None
    width: int = 0
    height: int = 0
    provider: str = ""
    prompt: str = ""
    seed: Optional[int] = None
    generation_time_ms: float = 0
    file_size_kb: float = 0
    error: Optional[str] = None
    metadata: dict = field(default_factory=dict)


class ImageProvider(ABC):
    """Base class for image generation providers."""

    @property
    @abstractmethod
    def name(self) -> str:
        """Provider name."""
        ...

    @property
    @abstractmethod
    def description(self) -> str:
        """Provider description."""
        ...

    @abstractmethod
    def generate(self, request: GenerationRequest) -> GenerationResult:
        """Generate an image from a request."""
        ...

    def generate_with_timing(self, request: GenerationRequest) -> GenerationResult:
        """Generate with automatic timing."""
        start = time.time()
        result = self.generate(request)
        result.generation_time_ms = (time.time() - start) * 1000
        return result

    def health_check(self) -> bool:
        """Check if the provider is available."""
        return True
