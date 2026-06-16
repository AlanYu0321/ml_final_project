from __future__ import annotations

from pathlib import Path

import pytest

from policy_agent import PolicyOpsAgent
from policy_agent.mcp import MCPClient, MCPError, PolicyMCPServer
from policy_agent.retrieval import PolicyRetriever


def test_mcp_server_lists_policy_search_tool() -> None:
    client = MCPClient(PolicyMCPServer(PolicyRetriever()))

    tools = client.list_tools()

    assert [tool.name for tool in tools] == ["policy.search"]
    assert tools[0].input_schema["required"] == ["query"]


def test_mcp_policy_search_returns_retrieval_results() -> None:
    client = MCPClient(PolicyMCPServer(PolicyRetriever()))

    results = client.call_tool(
        "policy.search",
        {"query": "vendor customer data approval", "top_k": 2, "mode": "optimized"},
    )

    assert results
    assert results[0].chunk.source.endswith(".md")
    assert client.call_history[0].name == "policy.search"


def test_mcp_rejects_unknown_tool() -> None:
    client = MCPClient(PolicyMCPServer(PolicyRetriever()))

    with pytest.raises(MCPError):
        client.call_tool("policy.delete", {"query": "test"})


def test_agent_records_mcp_tool_usage(tmp_path: Path) -> None:
    agent = PolicyOpsAgent(memory_path=tmp_path / "mem.json", audit_path=tmp_path / "audit.log")

    response = agent.ask("What approvals are required before using a vendor that touches customer data?")

    assert response.metadata["mcp_tools"] == ["policy.search"]
    assert "retrieve_policy" in [call.name for call in response.tool_calls]
