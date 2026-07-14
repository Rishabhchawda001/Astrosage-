"""OpenAPI Schemas — Service specifications for future APIs."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class OpenAPIService:
    name: str = ""
    version: str = "1.0.0"
    description: str = ""
    base_url: str = ""
    endpoints: list[dict] = field(default_factory=list)
    schemas: dict = field(default_factory=dict)


ASTROSAGE_SERVICES = [
    OpenAPIService(name="knowledge_service", description="Knowledge Lake query and management"),
    OpenAPIService(name="recovery_service", description="Knowledge recovery operations"),
    OpenAPIService(name="verification_service", description="Answer and citation verification"),
    OpenAPIService(name="corpus_service", description="Corpus management and statistics"),
    OpenAPIService(name="ocr_service", description="OCR processing and management"),
    OpenAPIService(name="citation_service", description="Citation tracking and verification"),
    OpenAPIService(name="knowledge_graph_service", description="Knowledge graph queries"),
    OpenAPIService(name="research_service", description="Research discovery and technology watch"),
    OpenAPIService(name="github_service", description="GitHub integration"),
    OpenAPIService(name="browser_service", description="Web browsing and research"),
]
