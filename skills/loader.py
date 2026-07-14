"""
Skill Loader — Discovers, validates, and loads SKILL.md files.

Skills are defined as directories containing a SKILL.md file.
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Optional


@dataclass
class Skill:
    name: str = ""
    version: str = "1.0.0"
    description: str = ""
    category: str = ""  # core, engineering, research, recovery, verification, qa, benchmark, doc
    dependencies: list[str] = field(default_factory=list)
    inputs: list[str] = field(default_factory=list)
    outputs: list[str] = field(default_factory=list)
    examples: list[str] = field(default_factory=list)
    skill_path: str = ""
    raw_content: str = ""


class SkillLoader:
    """
    Discovers and loads SKILL.md files from directories.

    Each skill is a directory containing a SKILL.md file.
    """

    def __init__(self, skill_dirs: list[str | Path] | None = None):
        self.skill_dirs = [Path(d) for d in (skill_dirs or [])]
        self._skills: dict[str, Skill] = {}

    def discover(self) -> dict[str, Skill]:
        for skill_dir in self.skill_dirs:
            if not skill_dir.exists():
                continue
            self._scan_directory(skill_dir)
        return dict(self._skills)

    def _scan_directory(self, directory: Path):
        for skill_md in directory.rglob("SKILL.md"):
            try:
                skill = self._parse_skill(skill_md)
                if skill:
                    self._skills[skill.name] = skill
            except Exception:
                pass

    def _parse_skill(self, skill_md_path: Path) -> Optional[Skill]:
        content = skill_md_path.read_text(encoding="utf-8", errors="replace")
        if not content.strip():
            return None

        skill = Skill(
            skill_path=str(skill_md_path),
            raw_content=content,
        )

        # Parse name from first heading
        name_match = re.search(r"^#\s+(.+)$", content, re.MULTILINE)
        if name_match:
            skill.name = name_match.group(1).strip()
        else:
            skill.name = skill_md_path.parent.name

        # Parse version
        version_match = re.search(r"(?:version|Version)[:\s]+(\S+)", content)
        if version_match:
            skill.version = version_match.group(1)

        # Parse description
        desc_match = re.search(r"(?:description|Description)[:\s]+(.+)$", content, re.MULTILINE)
        if desc_match:
            skill.description = desc_match.group(1).strip()

        # Parse category from path
        parts = skill_md_path.parts
        for part in parts:
            if part in ("core", "engineering", "research", "recovery", "verification", "qa", "benchmark", "doc"):
                skill.category = part
                break

        return skill

    def get_skill(self, name: str) -> Optional[Skill]:
        return self._skills.get(name)

    def list_skills(self) -> list[Skill]:
        return list(self._skills.values())

    def list_by_category(self, category: str) -> list[Skill]:
        return [s for s in self._skills.values() if s.category == category]

    @property
    def count(self) -> int:
        return len(self._skills)

    def summary(self) -> dict:
        cats = {}
        for s in self._skills.values():
            cat = s.category or "uncategorized"
            cats[cat] = cats.get(cat, 0) + 1
        return {"total": self.count, "by_category": cats}
