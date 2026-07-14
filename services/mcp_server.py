"""
MCP Server — AstroSage MCP server architecture preparation.

This module defines the MCP server structure and adapter interfaces.
No hardcoded implementations.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Callable


@dataclass
class MCPServerConfig:
    name: str = "astrosage"
    version: str = "1.0.0"
    transport: str = "stdio"  # stdio, sse, streamable-http
    tools: list[dict] = field(default_factory=list)


class MCPServer:
    """
    AstroSage MCP server — Scaffold only.

    Adapters register tools. The server exposes them via MCP protocol.
    """

    def __init__(self, config: MCPServerConfig | None = None):
        self.config = config or MCPServerConfig()
        self._tools: dict[str, Callable] = {}
        self._adapters: dict[str, Any] = {}

    def register_tool(self, name: str, handler: Callable, description: str = "") -> None:
        self._tools[name] = handler

    def register_adapter(self, name: str, adapter: Any) -> None:
        self._adapters[name] = adapter

    def list_tools(self) -> list[dict]:
        return [
            {"name": name, "handler": handler.__name__ if hasattr(handler, "__name__") else str(handler)}
            for name, handler in self._tools.items()
        ]

    def list_adapters(self) -> list[str]:
        return list(self._adapters.keys())

    def health(self) -> dict:
        return {
            "status": "scaffold",
            "tools": len(self._tools),
            "adapters": len(self._adapters),
        }
