from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from .retrieval import PolicyRetriever, RetrievalResult


class MCPError(RuntimeError):
    pass


@dataclass(frozen=True)
class MCPTool:
    name: str
    description: str
    input_schema: dict[str, Any]


@dataclass(frozen=True)
class MCPRequest:
    method: str
    params: dict[str, Any]


@dataclass(frozen=True)
class MCPResponse:
    result: Any


@dataclass(frozen=True)
class MCPToolCall:
    name: str
    arguments: dict[str, Any]


class PolicyMCPServer:
    """Local MCP-style server exposing policy knowledge as tools.

    This keeps the capstone runnable with only the Python standard library while
    preserving the MCP boundary: the agent asks a client to call a named tool,
    and the server owns the retrieval implementation behind that tool.
    """

    def __init__(self, retriever: PolicyRetriever) -> None:
        self.retriever = retriever
        self._tools = {
            "policy.search": MCPTool(
                name="policy.search",
                description="Search policy documents and return cited chunks.",
                input_schema={
                    "type": "object",
                    "properties": {
                        "query": {"type": "string"},
                        "top_k": {"type": "integer", "minimum": 1, "maximum": 10},
                        "mode": {"type": "string", "enum": ["baseline", "optimized"]},
                    },
                    "required": ["query"],
                },
            )
        }

    def handle(self, request: MCPRequest) -> MCPResponse:
        if request.method == "tools/list":
            return MCPResponse(result=list(self._tools.values()))
        if request.method == "tools/call":
            name = str(request.params.get("name", ""))
            arguments = request.params.get("arguments", {})
            if not isinstance(arguments, dict):
                raise MCPError("MCP tool arguments must be an object.")
            return MCPResponse(result=self._call_tool(name, arguments))
        raise MCPError(f"Unknown MCP method: {request.method}")

    def _call_tool(self, name: str, arguments: dict[str, Any]) -> list[RetrievalResult]:
        if name != "policy.search":
            raise MCPError(f"Unknown MCP tool: {name}")
        query = str(arguments.get("query", "")).strip()
        if not query:
            raise MCPError("policy.search requires a non-empty query.")
        top_k = int(arguments.get("top_k", 4))
        mode = str(arguments.get("mode", "optimized"))
        if mode not in {"baseline", "optimized"}:
            raise MCPError(f"Unsupported retrieval mode: {mode}")
        return self.retriever.search(query, top_k=top_k, mode=mode)


class MCPClient:
    def __init__(self, server: PolicyMCPServer) -> None:
        self.server = server
        self.call_history: list[MCPToolCall] = []

    def list_tools(self) -> list[MCPTool]:
        response = self.server.handle(MCPRequest(method="tools/list", params={}))
        return response.result

    def call_tool(self, name: str, arguments: dict[str, Any]) -> Any:
        self.call_history.append(MCPToolCall(name=name, arguments=dict(arguments)))
        response = self.server.handle(
            MCPRequest(method="tools/call", params={"name": name, "arguments": arguments})
        )
        return response.result
