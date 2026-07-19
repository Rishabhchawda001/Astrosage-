"""Test MCP server tools."""
import json
import pytest
from unittest.mock import patch

# Create a test client that uses the MCP server directly
import sys
sys.path.insert(0, ".")
from mcp_server import handle_mcp_request, TOOLS


def test_mcp_list_tools():
    """Test listing available tools."""
    request = {"jsonrpc": "2.0", "id": 1, "method": "list_tools"}
    response = handle_mcp_request(request)
    assert "result" in response
    assert "tools" in response["result"]
    tool_names = [t["name"] for t in response["result"]["tools"]]
    assert "search_knowledge" in tool_names
    assert "get_entity" in tool_names
    assert "list_scriptures" in tool_names
    assert "answer_question" in tool_names
    assert "knowledge_stats" in tool_names


def test_mcp_tool_definitions_have_schemas():
    """All tools have valid input schemas."""
    for name, info in TOOLS.items():
        assert "description" in info
        assert "inputSchema" in info
        assert info["inputSchema"]["type"] == "object"


def test_mcp_ping():
    """Test ping/pong."""
    request = {"jsonrpc": "2.0", "id": 1, "method": "ping"}
    response = handle_mcp_request(request)
    assert response["result"] == "pong"


def test_mcp_unknown_tool():
    """Test unknown tool returns error."""
    request = {
        "jsonrpc": "2.0",
        "id": 1,
        "method": "call_tool",
        "params": {"name": "nonexistent_tool", "arguments": {}},
    }
    response = handle_mcp_request(request)
    assert "error" in response
    assert response["error"]["code"] == -32601


def test_mcp_initialize():
    """Test initialization."""
    request = {"jsonrpc": "2.0", "id": 1, "method": "initialize"}
    response = handle_mcp_request(request)
    assert response["result"]["serverInfo"]["name"] == "astrosage"
    assert "tools" in response["result"]["capabilities"]


@pytest.mark.parametrize("tool_name", [
    "search_knowledge",
    "get_entity",
    "get_entity_relationships",
    "list_scriptures",
    "get_scripture",
    "answer_question",
    "knowledge_stats",
])
def test_mcp_tool_handlers_exist(tool_name):
    """All tool handlers are callable."""
    assert tool_name in TOOLS
    assert callable(TOOLS[tool_name]["handler"])
