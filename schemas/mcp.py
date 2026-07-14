"""MCP Schemas — Tool definitions for MCP servers."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Optional


@dataclass
class MCPTool:
    name: str
    description: str
    input_schema: dict = field(default_factory=dict)
    output_schema: dict = field(default_factory=dict)


@dataclass
class MCPToolCall:
    tool_name: str
    arguments: dict = field(default_factory=dict)
    call_id: str = ""


@dataclass
class MCPToolResult:
    call_id: str = ""
    content: Any = None
    is_error: bool = False
    error_message: str = ""


# Known MCP tools for AstroSage
ASTROSAGE_MCP_TOOLS = [
    MCPTool(name="search_books", description="Search across entire knowledge base",
            input_schema={"query": "string", "top_k": "integer", "filters": "object"}),
    MCPTool(name="search_pages", description="Page-level retrieval with OCR text",
            input_schema={"query": "string", "page_range": "string"}),
    MCPTool(name="list_books", description="Enumerate indexed documents",
            input_schema={"filter": "object"}),
    MCPTool(name="compare_sources", description="Compare information across documents",
            input_schema={"document_ids": "array"}),
    MCPTool(name="verify_answer", description="Check if answer is grounded in sources",
            input_schema={"answer": "string", "source_ids": "array"}),
    MCPTool(name="sync_library", description="Trigger re-sync from source",
            input_schema={"source": "string"}),
    MCPTool(name="reindex", description="Re-index a specific document or all",
            input_schema={"document_id": "string"}),
    MCPTool(name="pipeline_status", description="Check ingestion pipeline status",
            input_schema={}),
    MCPTool(name="audit_status", description="System health and integrity",
            input_schema={}),
    MCPTool(name="ocr_statistics", description="OCR processing metrics",
            input_schema={}),
    MCPTool(name="index_statistics", description="Index size and coverage",
            input_schema={}),
    MCPTool(name="knowledge_graph", description="Query concept relationships",
            input_schema={"query": "string", "depth": "integer"}),
]
