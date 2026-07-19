"""
AstroSage MCP Server — Exposes knowledge tools via Model Context Protocol.

Run with:
  python3 mcp_server.py  # stdio mode (for Claude Desktop)
  python3 mcp_server.py --sse  # SSE mode (for web)

Tools exposed:
  - search_knowledge: BM25 semantic search over 120K chunks
  - get_entity: Knowledge graph entity lookup
  - get_entity_relationships: Entity relationship exploration
  - list_scriptures: List all 54 indexed scriptures
  - get_scripture: Scripture metadata and coverage
  - answer_question: Grounded answer with evidence
  - knowledge_stats: Knowledge base statistics
"""
from __future__ import annotations

import argparse
import json
import sys
import time
from typing import Any

# Add the repo root to path so we can import api services
sys.path.insert(0, ".")

from api.services import get_graph_service, get_search_service, get_answer_service
from api.services.knowledge import KnowledgeGraphService, BM25SearchService


def search_knowledge(args: dict) -> dict:
    """Search the knowledge base using BM25 retrieval."""
    query = args.get("query", "")
    top_k = min(args.get("limit", 10), 50)
    search = get_search_service()
    results = search.search(query, top_k=top_k)
    return {
        "query": query,
        "results": [
            {
                "text": r["text"][:300],
                "scripture": r["scripture_id"],
                "level": r["level"],
                "score": r["score"],
                "chunk_id": r["chunk_id"],
            }
            for r in results
        ],
        "total": len(results),
    }


def get_entity(args: dict) -> dict:
    """Get details about a knowledge graph entity."""
    name = args.get("name", "")
    graph = get_graph_service()
    entity = graph.find_entity(name)
    if not entity:
        return {"error": f"Entity '{name}' not found", "found": False}

    guid = entity.get("GUID", "")
    relationships = graph.get_entity_relationships(guid)

    return {
        "found": True,
        "name": entity.get("name", ""),
        "type": entity.get("type", ""),
        "total_mentions": entity.get("total_mentions", 0),
        "sources": entity.get("sources", [])[:10],
        "relationship_count": len(relationships),
        "relationships": [
            {
                "type": r["type"],
                "direction": r["direction"],
                "target": r["target_name"],
                "target_type": r["target_type"],
            }
            for r in relationships[:20]
        ],
    }


def get_entity_relationships(args: dict) -> dict:
    """Get relationships for an entity."""
    name = args.get("name", "")
    graph = get_graph_service()
    entity = graph.find_entity(name)
    if not entity:
        return {"error": f"Entity '{name}' not found", "found": False}

    guid = entity.get("GUID", "")
    relationships = graph.get_entity_relationships(guid)

    return {
        "entity": name,
        "type": entity.get("type", ""),
        "total_relationships": len(relationships),
        "by_type": _group_relationships_by_type(relationships),
        "relationships": [
            {
                "type": r["type"],
                "target": r["target_name"],
                "target_type": r["target_type"],
                "direction": r["direction"],
            }
            for r in relationships
        ],
    }


def list_scriptures(args: dict) -> dict:
    """List all indexed scriptures with metadata."""
    graph = get_graph_service()
    scriptures = graph.list_scriptures()
    return {
        "total": len(scriptures),
        "scriptures": scriptures,
    }


def get_scripture(args: dict) -> dict:
    """Get metadata for a specific scripture."""
    scripture_id = args.get("id", "")
    graph = get_graph_service()
    s = graph.get_scripture(scripture_id)
    if not s:
        return {"error": f"Scripture '{scripture_id}' not found", "found": False}
    return {
        "found": True,
        "id": s.get("id", ""),
        "name": s.get("canonical_name", s.get("id", "")),
        "verses": s.get("total_verses", 0),
        "coverage": s.get("coverage", 0),
        "certification": s.get("certification", ""),
        "source": s.get("primary_source", ""),
    }


def answer_question(args: dict) -> dict:
    """Answer a question using the grounded knowledge engine."""
    question = args.get("question", "")
    top_k = min(args.get("limit", 5), 20)
    answer_svc = get_answer_service()
    result = answer_svc.answer(question, top_k=top_k)
    return {
        "question": question,
        "summary": result["answer"]["summary"],
        "entities_found": [e["name"] for e in result["entities"]],
        "evidence_count": result["answer"]["evidence_count"],
        "confidence": result["answer"]["confidence"],
        "sources": [
            {
                "text": s.get("text", "")[:200],
                "scripture": s.get("scripture", ""),
                "score": s.get("score", 0),
            }
            for s in result["sources"]
        ],
    }


def knowledge_stats(args: dict) -> dict:
    """Get statistics about the knowledge base."""
    graph = get_graph_service()
    search = get_search_service()
    return {
        "entities": graph.stats["entities"],
        "scriptures": graph.stats["scriptures"],
        "edges": graph.stats["edges"],
        "edge_types": graph.stats["edge_types"],
        "chunks": search.stats["total_chunks"],
        "vocabulary": search.stats["vocabulary_size"],
        "knowledge_version": "v1.0.0",
    }


def _group_relationships_by_type(rels: list[dict]) -> dict:
    """Group relationships by type for easier consumption."""
    by_type: dict[str, list[str]] = {}
    for r in rels:
        rtype = r["type"]
        if rtype not in by_type:
            by_type[rtype] = []
        by_type[rtype].append(r["target_name"])
    return by_type


# ── Tool Registry ─────────────────────────────────────────────────

TOOLS = {
    "search_knowledge": {
        "handler": search_knowledge,
        "description": "Search the knowledge base by keyword using BM25 retrieval",
        "inputSchema": {
            "type": "object",
            "properties": {
                "query": {"type": "string", "description": "Search query"},
                "limit": {"type": "integer", "description": "Max results (1-50)", "default": 10},
            },
            "required": ["query"],
        },
    },
    "get_entity": {
        "handler": get_entity,
        "description": "Look up an entity in the knowledge graph with relationships",
        "inputSchema": {
            "type": "object",
            "properties": {
                "name": {"type": "string", "description": "Entity name (e.g., Krishna, Vishnu, Arjuna)"},
            },
            "required": ["name"],
        },
    },
    "get_entity_relationships": {
        "handler": get_entity_relationships,
        "description": "Get all relationships for an entity with type grouping",
        "inputSchema": {
            "type": "object",
            "properties": {
                "name": {"type": "string", "description": "Entity name"},
            },
            "required": ["name"],
        },
    },
    "list_scriptures": {
        "handler": list_scriptures,
        "description": "List all 54 indexed scriptures with metadata",
        "inputSchema": {
            "type": "object",
            "properties": {},
        },
    },
    "get_scripture": {
        "handler": get_scripture,
        "description": "Get metadata and coverage for a specific scripture",
        "inputSchema": {
            "type": "object",
            "properties": {
                "id": {"type": "string", "description": "Scripture ID (e.g., BG, UPANISHADS, YOGA_SUTRA)"},
            },
            "required": ["id"],
        },
    },
    "answer_question": {
        "handler": answer_question,
        "description": "Answer a question using the grounded knowledge engine with citations",
        "inputSchema": {
            "type": "object",
            "properties": {
                "question": {"type": "string", "description": "Natural language question"},
                "limit": {"type": "integer", "description": "Max evidence sources", "default": 5},
            },
            "required": ["question"],
        },
    },
    "knowledge_stats": {
        "handler": knowledge_stats,
        "description": "Get statistics about the knowledge base",
        "inputSchema": {
            "type": "object",
            "properties": {},
        },
    },
}


def handle_mcp_request(request: dict) -> dict:
    """Handle an MCP JSON-RPC request."""
    method = request.get("method", "")
    req_id = request.get("id")

    if method == "list_tools":
        return {
            "jsonrpc": "2.0",
            "id": req_id,
            "result": {
                "tools": [
                    {
                        "name": name,
                        "description": info["description"],
                        "inputSchema": info["inputSchema"],
                    }
                    for name, info in TOOLS.items()
                ]
            },
        }

    if method == "call_tool":
        params = request.get("params", {})
        tool_name = params.get("name", "")
        arguments = params.get("arguments", {})

        if tool_name not in TOOLS:
            return {
                "jsonrpc": "2.0",
                "id": req_id,
                "error": {"code": -32601, "message": f"Tool not found: {tool_name}"},
            }

        try:
            result = TOOLS[tool_name]["handler"](arguments)
            return {
                "jsonrpc": "2.0",
                "id": req_id,
                "result": {"content": [{"type": "text", "text": json.dumps(result, indent=2, ensure_ascii=False)}]},
            }
        except Exception as e:
            return {
                "jsonrpc": "2.0",
                "id": req_id,
                "error": {"code": -32000, "message": str(e)},
            }

    if method == "ping":
        return {"jsonrpc": "2.0", "id": req_id, "result": "pong"}

    if method == "initialize":
        return {
            "jsonrpc": "2.0",
            "id": req_id,
            "result": {
                "protocolVersion": "2025-03-26",
                "capabilities": {"tools": {}},
                "serverInfo": {"name": "astrosage", "version": "2.0.0"},
            },
        }

    return {"jsonrpc": "2.0", "id": req_id, "error": {"code": -32601, "message": f"Method not found: {method}"}}


def run_stdio():
    """Run MCP server in stdio mode (for Claude Desktop)."""
    import sys

    # Preload knowledge services
    print("Loading knowledge services...", file=sys.stderr)
    get_graph_service()
    get_search_service()
    print("Ready.", file=sys.stderr)

    for line in sys.stdin:
        line = line.strip()
        if not line:
            continue
        try:
            request = json.loads(line)
            response = handle_mcp_request(request)
            sys.stdout.write(json.dumps(response) + "\n")
            sys.stdout.flush()
        except json.JSONDecodeError:
            error_response = {
                "jsonrpc": "2.0",
                "error": {"code": -32700, "message": "Parse error"},
            }
            sys.stdout.write(json.dumps(error_response) + "\n")
            sys.stdout.flush()


def run_sse(host: str = "0.0.0.0", port: int = 8090):
    """Run MCP server in SSE mode (for web)."""
    from http.server import HTTPServer, BaseHTTPRequestHandler
    import urllib.parse

    class MCPHandler(BaseHTTPRequestHandler):
        def do_POST(self):
            content_length = int(self.headers.get("Content-Length", 0))
            body = self.rfile.read(content_length).decode("utf-8")

            try:
                request = json.loads(body)
                response = handle_mcp_request(request)
            except json.JSONDecodeError:
                response = {"jsonrpc": "2.0", "error": {"code": -32700, "message": "Parse error"}}

            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps(response).encode("utf-8"))

        def log_message(self, format, *args):
            pass  # Suppress HTTP server logs

    # Preload
    print(f"Starting MCP SSE server on {host}:{port}...", file=sys.stderr)
    get_graph_service()
    get_search_service()

    server = HTTPServer((host, port), MCPHandler)
    print(f"MCP server running at http://{host}:{port}", file=sys.stderr)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nShutting down...", file=sys.stderr)
        server.shutdown()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="AstroSage MCP Server")
    parser.add_argument("--sse", action="store_true", help="Run in SSE mode instead of stdio")
    parser.add_argument("--host", default="0.0.0.0", help="SSE server host")
    parser.add_argument("--port", type=int, default=8090, help="SSE server port")
    args = parser.parse_args()

    if args.sse:
        run_sse(host=args.host, port=args.port)
    else:
        run_stdio()
