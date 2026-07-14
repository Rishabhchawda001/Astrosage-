"""Component Version Registry — Tracks versions of all AstroSage components."""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone


@dataclass
class ComponentVersion:
    name: str
    version: str
    component_type: str = ""  # plugin, service, adapter, schema
    description: str = ""
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    deprecated: bool = False
    replaces: str = ""  # name of component this replaces


class ComponentVersionRegistry:
    """Registry tracking versions of all AstroSage components."""

    def __init__(self):
        self._versions: dict[str, list[ComponentVersion]] = {}

    def register(self, name: str, version: str, component_type: str = "", description: str = "") -> None:
        if name not in self._versions:
            self._versions[name] = []
        self._versions[name].append(ComponentVersion(
            name=name, version=version, component_type=component_type, description=description,
        ))

    def get_current(self, name: str) -> ComponentVersion | None:
        versions = self._versions.get(name, [])
        return versions[-1] if versions else None

    def get_all_versions(self, name: str) -> list[ComponentVersion]:
        return list(self._versions.get(name, []))

    def list_components(self) -> list[str]:
        return list(self._versions.keys())

    def summary(self) -> dict:
        return {name: versions[-1].version for name, versions in self._versions.items() if versions}
