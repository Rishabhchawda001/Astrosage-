"""Command Registry — Infrastructure for slash commands."""
from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any


@dataclass
class CommandMetadata:
    name: str
    description: str
    category: str = ""  # recovery, verification, research, benchmark, index, ocr, etc.
    aliases: list[str] = field(default_factory=list)
    examples: list[str] = field(default_factory=list)


class Command(ABC):
    @abstractmethod
    def metadata(self) -> CommandMetadata: ...

    @abstractmethod
    def execute(self, args: dict[str, Any]) -> dict[str, Any]: ...

    @abstractmethod
    def health(self) -> dict: ...


class CommandRegistry:
    """Registry of all AstroSage slash commands."""

    def __init__(self):
        self._commands: dict[str, Command] = {}

    def register(self, command: Command) -> None:
        meta = command.metadata()
        self._commands[meta.name] = command
        for alias in meta.aliases:
            self._commands[alias] = command

    def get(self, name: str) -> Command | None:
        return self._commands.get(name)

    def list_commands(self) -> list[CommandMetadata]:
        seen = set()
        commands = []
        for name, cmd in self._commands.items():
            meta = cmd.metadata()
            if meta.name not in seen:
                seen.add(meta.name)
                commands.append(meta)
        return commands

    def list_by_category(self, category: str) -> list[CommandMetadata]:
        return [c for c in self.list_commands() if c.category == category]

    @property
    def count(self) -> int:
        return len(set(id(cmd) for cmd in self._commands.values()))

    def summary(self) -> dict:
        cats = {}
        for c in self.list_commands():
            cat = c.category or "uncategorized"
            cats[cat] = cats.get(cat, 0) + 1
        return {"total": self.count, "by_category": cats}
