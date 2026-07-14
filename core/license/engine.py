"""
License Engine — Track licensing for every source and document.

Tracks: public domain, open license, restricted, unknown.
Never violates licensing. Always stores attribution.
"""
from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Optional


class LicenseType(str, Enum):
    PUBLIC_DOMAIN = "public_domain"
    OPEN = "open"
    CREATIVE_COMMONS = "creative_commons"
    RESTRICTED = "restricted"
    UNKNOWN = "unknown"
    GOVERNMENT = "government"
    FAIR_USE = "fair_use"


class LicenseStatus(str, Enum):
    VERIFIED = "verified"
    ASSUMED = "assumed"
    PENDING = "pending"
    VIOLATION = "violation"


@dataclass
class LicenseRecord:
    """License record for a source or document."""
    license_id: str = ""
    source_id: str = ""
    edition_id: str = ""
    license_type: LicenseType = LicenseType.UNKNOWN
    license_name: str = ""
    license_url: str = ""
    license_text: str = ""
    attribution: str = ""
    status: LicenseStatus = LicenseStatus.PENDING
    allows_distribution: bool = False
    allows_commercial: bool = False
    requires_attribution: bool = False
    expires_at: str = ""
    verified_at: str = ""
    metadata: dict[str, Any] = field(default_factory=dict)
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

    def __post_init__(self):
        if not self.license_id:
            self.license_id = f"LC-{uuid.uuid4().hex[:12]}"

    @property
    def is_clear(self) -> bool:
        return self.license_type in (LicenseType.PUBLIC_DOMAIN, LicenseType.OPEN, LicenseType.GOVERNMENT)


class LicenseEngine:
    """License tracking and compliance engine."""

    def __init__(self):
        self._records: dict[str, LicenseRecord] = {}
        self._by_source: dict[str, list[str]] = {}

    def register(self, record: LicenseRecord) -> str:
        self._records[record.license_id] = record
        self._by_source.setdefault(record.source_id, []).append(record.license_id)
        return record.license_id

    def get(self, license_id: str) -> Optional[LicenseRecord]:
        return self._records.get(license_id)

    def get_by_source(self, source_id: str) -> list[LicenseRecord]:
        ids = self._by_source.get(source_id, [])
        return [self._records[lid] for lid in ids if lid in self._records]

    def is_distributable(self, source_id: str) -> bool:
        records = self.get_by_source(source_id)
        if not records:
            return False
        return any(r.allows_distribution or r.is_clear for r in records)

    def get_violations(self) -> list[LicenseRecord]:
        return [r for r in self._records.values() if r.status == LicenseStatus.VIOLATION]

    def count(self) -> int:
        return len(self._records)

    def summary(self) -> dict:
        type_counts: dict[str, int] = {}
        for r in self._records.values():
            type_counts[r.license_type.value] = type_counts.get(r.license_type.value, 0) + 1
        return {"total": self.count(), "by_type": type_counts, "violations": len(self.get_violations())}
