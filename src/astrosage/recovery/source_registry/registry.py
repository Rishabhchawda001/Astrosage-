"""
Knowledge Source Registry — Catalog of all external knowledge sources.

Every external source AstroSage may use for recovery is registered here.
Supports Internet Archive, Open Library, Crossref, OpenAlex, government
digital libraries, university repositories, and public domain collections.
"""
from __future__ import annotations

import json
import uuid
from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from enum import Enum
from pathlib import Path
from typing import Optional


class SourceCategory(str, Enum):
    INTERNET_ARCHIVE = "internet_archive"
    OPEN_LIBRARY = "open_library"
    CROSSREF = "crossref"
    OPENALEX = "openalex"
    GOVERNMENT = "government"
    UNIVERSITY = "university"
    PUBLIC_DOMAIN = "public_domain"
    GITHUB = "github"
    WIKIDATA = "wikidata"
    CUSTOM = "custom"


class SourceTrustLevel(str, Enum):
    VERIFIED = "verified"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    UNTRUSTED = "untrusted"


class SourceHealthStatus(str, Enum):
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    DOWN = "down"
    UNKNOWN = "unknown"


class RecoveryMode(str, Enum):
    METADATA_ONLY = "metadata_only"
    TEXT_RECOVERY = "text_recovery"
    OCR_RECOVERY = "ocr_recovery"
    EDITION_COMPARISON = "edition_comparison"
    FULL_RECOVERY = "full_recovery"


@dataclass
class SourceRateLimit:
    requests_per_minute: int = 60
    requests_per_hour: int = 1000
    concurrent_requests: int = 5
    retry_after_seconds: int = 60


@dataclass
class KnowledgeSource:
    source_id: str
    name: str
    description: str
    category: SourceCategory
    country: str = ""
    license: str = ""
    url: str = ""
    authentication_required: bool = False
    authentication_method: str = ""  # api_key, oauth, none
    rate_limits: SourceRateLimit = field(default_factory=SourceRateLimit)
    languages: list[str] = field(default_factory=list)
    document_types: list[str] = field(default_factory=list)  # pdf, epub, txt, etc.
    metadata_types: list[str] = field(default_factory=list)
    api_support: bool = False
    offline_availability: bool = False
    trust_level: SourceTrustLevel = SourceTrustLevel.MEDIUM
    priority: int = 5  # 1=highest, 10=lowest
    version: str = "1.0.0"
    checksum: str = ""
    last_validation: str = ""
    usage_restrictions: list[str] = field(default_factory=list)
    health_status: SourceHealthStatus = SourceHealthStatus.UNKNOWN
    supported_recovery_modes: list[RecoveryMode] = field(
        default_factory=lambda: [RecoveryMode.METADATA_ONLY]
    )
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    updated_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


class KnowledgeSourceRegistry:
    """
    Registry of all external knowledge sources.

    Every source is cataloged with trust levels, rate limits,
    supported recovery modes, and health status.
    """

    def __init__(self, registry_dir: str = "knowledge/recovery/source_registry"):
        self.registry_dir = Path(registry_dir)
        self.registry_dir.mkdir(parents=True, exist_ok=True)
        self._sources: dict[str, KnowledgeSource] = {}
        # Load from disk if available, otherwise load defaults
        if (self.registry_dir / "sources.json").exists():
            self.load()
        else:
            self._load_defaults()

    def _load_defaults(self):
        """Load default AstroSage-recognized sources."""
        defaults = [
            KnowledgeSource(
                source_id="src_internet_archive",
                name="Internet Archive",
                description="Free digital library with millions of books, texts, and media",
                category=SourceCategory.INTERNET_ARCHIVE,
                country="US",
                license="Public Domain / Various",
                url="https://archive.org",
                api_support=True,
                offline_availability=True,
                trust_level=SourceTrustLevel.HIGH,
                priority=1,
                languages=["en", "hi", "sa", "te", "kn", "ta", "ml", "gu", "bn", "pa"],
                document_types=["pdf", "epub", "txt", "djvu"],
                supported_recovery_modes=[
                    RecoveryMode.METADATA_ONLY,
                    RecoveryMode.TEXT_RECOVERY,
                    RecoveryMode.EDITION_COMPARISON,
                ],
            ),
            KnowledgeSource(
                source_id="src_open_library",
                name="Open Library",
                description="Open, editable catalog of books",
                category=SourceCategory.OPEN_LIBRARY,
                country="US",
                license="Public Domain",
                url="https://openlibrary.org",
                api_support=True,
                offline_availability=False,
                trust_level=SourceTrustLevel.HIGH,
                priority=2,
                languages=["en", "hi"],
                document_types=["pdf", "epub"],
                supported_recovery_modes=[
                    RecoveryMode.METADATA_ONLY,
                    RecoveryMode.EDITION_COMPARISON,
                ],
            ),
            KnowledgeSource(
                source_id="src_crossref",
                name="Crossref",
                description="Official DOI registration agency for scholarly works",
                category=SourceCategory.CROSSREF,
                country="US",
                license="Public Domain (metadata)",
                url="https://api.crossref.org",
                api_support=True,
                offline_availability=False,
                trust_level=SourceTrustLevel.VERIFIED,
                priority=1,
                languages=["en"],
                document_types=["pdf"],
                metadata_types=["doi", "citation", "abstract"],
                supported_recovery_modes=[RecoveryMode.METADATA_ONLY],
            ),
            KnowledgeSource(
                source_id="src_openalex",
                name="OpenAlex",
                description="Open catalog of scholarly works, authors, venues, institutions",
                category=SourceCategory.OPENALEX,
                country="US",
                license="CC0",
                url="https://api.openalex.org",
                api_support=True,
                offline_availability=False,
                trust_level=SourceTrustLevel.HIGH,
                priority=2,
                languages=["en"],
                document_types=["pdf"],
                metadata_types=["doi", "citation", "abstract", "author"],
                supported_recovery_modes=[RecoveryMode.METADATA_ONLY],
            ),
            KnowledgeSource(
                source_id="src_wikidata",
                name="Wikidata",
                description="Structured knowledge base (metadata only, not article text)",
                category=SourceCategory.WIKIDATA,
                country="Global",
                license="CC0",
                url="https://www.wikidata.org",
                api_support=True,
                offline_availability=False,
                trust_level=SourceTrustLevel.HIGH,
                priority=3,
                languages=["en", "hi", "sa"],
                document_types=[],
                metadata_types=["entity", "relationship", "property"],
                supported_recovery_modes=[RecoveryMode.METADATA_ONLY],
            ),
        ]
        for source in defaults:
            self._sources[source.source_id] = source

    def register_source(self, source: KnowledgeSource) -> str:
        """Register a new knowledge source. Returns source_id."""
        if not source.source_id:
            source.source_id = f"src_{uuid.uuid4().hex[:12]}"
        source.updated_at = datetime.now(timezone.utc).isoformat()
        self._sources[source.source_id] = source
        return source.source_id

    def get_source(self, source_id: str) -> Optional[KnowledgeSource]:
        return self._sources.get(source_id)

    def list_sources(
        self,
        category: Optional[SourceCategory] = None,
        trust_level: Optional[SourceTrustLevel] = None,
    ) -> list[KnowledgeSource]:
        sources = list(self._sources.values())
        if category:
            sources = [s for s in sources if s.category == category]
        if trust_level:
            sources = [s for s in sources if s.trust_level == trust_level]
        return sorted(sources, key=lambda s: s.priority)

    def get_sources_for_recovery(self, mode: RecoveryMode) -> list[KnowledgeSource]:
        """Get all sources that support a specific recovery mode."""
        return [
            s for s in self._sources.values()
            if mode in s.supported_recovery_modes
            and s.health_status != SourceHealthStatus.DOWN
        ]

    def update_health(self, source_id: str, status: SourceHealthStatus):
        if source_id in self._sources:
            self._sources[source_id].health_status = status
            self._sources[source_id].updated_at = datetime.now(timezone.utc).isoformat()

    def save(self):
        """Save registry to disk."""
        data = {
            sid: {
                "source_id": s.source_id,
                "name": s.name,
                "description": s.description,
                "category": s.category.value,
                "country": s.country,
                "license": s.license,
                "url": s.url,
                "authentication_required": s.authentication_required,
                "authentication_method": s.authentication_method,
                "rate_limits": {
                    "requests_per_minute": s.rate_limits.requests_per_minute,
                    "requests_per_hour": s.rate_limits.requests_per_hour,
                    "concurrent_requests": s.rate_limits.concurrent_requests,
                    "retry_after_seconds": s.rate_limits.retry_after_seconds,
                },
                "languages": s.languages,
                "document_types": s.document_types,
                "metadata_types": s.metadata_types,
                "api_support": s.api_support,
                "offline_availability": s.offline_availability,
                "trust_level": s.trust_level.value,
                "priority": s.priority,
                "version": s.version,
                "checksum": s.checksum,
                "last_validation": s.last_validation,
                "usage_restrictions": s.usage_restrictions,
                "health_status": s.health_status.value,
                "supported_recovery_modes": [m.value for m in s.supported_recovery_modes],
                "created_at": s.created_at,
                "updated_at": s.updated_at,
            }
            for sid, s in self._sources.items()
        }
        filepath = self.registry_dir / "sources.json"
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

    def load(self):
        """Load registry from disk."""
        filepath = self.registry_dir / "sources.json"
        if not filepath.exists():
            return
        with open(filepath, "r", encoding="utf-8") as f:
            data = json.load(f)
        for sid, sdata in data.items():
            sdata["rate_limits"] = SourceRateLimit(**sdata.get("rate_limits", {}))
            sdata["category"] = SourceCategory(sdata["category"])
            sdata["trust_level"] = SourceTrustLevel(sdata["trust_level"])
            sdata["health_status"] = SourceHealthStatus(sdata["health_status"])
            sdata["supported_recovery_modes"] = [
                RecoveryMode(m) for m in sdata.get("supported_recovery_modes", [])
            ]
            self._sources[sid] = KnowledgeSource(**sdata)

    def summary(self) -> dict:
        categories = {}
        trust_counts = {}
        for s in self._sources.values():
            categories[s.category.value] = categories.get(s.category.value, 0) + 1
            trust_counts[s.trust_level.value] = trust_counts.get(s.trust_level.value, 0) + 1
        return {
            "total_sources": len(self._sources),
            "by_category": categories,
            "by_trust_level": trust_counts,
            "api_enabled": sum(1 for s in self._sources.values() if s.api_support),
        }
