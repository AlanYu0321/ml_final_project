from __future__ import annotations

import hashlib
from dataclasses import dataclass
from typing import Any, Callable

from .mcp import MCPClient, MCPError, PolicyMCPServer
from .memory import JsonMemoryStore
from .retrieval import PolicyRetriever, RetrievalResult
from .security import authorize_tool


@dataclass(frozen=True)
class ToolCall:
    name: str
    args: dict[str, Any]
    result: Any


class ToolError(RuntimeError):
    pass


class ToolRegistry:
    def __init__(
        self,
        retriever: PolicyRetriever,
        memory: JsonMemoryStore,
        mcp_client: MCPClient | None = None,
    ) -> None:
        self.retriever = retriever
        self.memory = memory
        self.mcp_client = mcp_client or MCPClient(PolicyMCPServer(retriever))
        self._tools: dict[str, Callable[..., Any]] = {
            "retrieve_policy": self.retrieve_policy,
            "create_escalation_ticket": self.create_escalation_ticket,
            "remember_user_context": self.remember_user_context,
        }

    def call(self, tool_name: str, *, question: str, **kwargs: Any) -> ToolCall:
        decision = authorize_tool(tool_name, question)
        if not decision.allowed:
            raise ToolError(decision.reason)
        if tool_name not in self._tools:
            raise ToolError(f"Unknown tool: {tool_name}")
        result = self._tools[tool_name](**kwargs)
        return ToolCall(tool_name, kwargs, result)

    def retrieve_policy(self, query: str, top_k: int = 4, mode: str = "optimized") -> list[RetrievalResult]:
        try:
            return self.mcp_client.call_tool("policy.search", {"query": query, "top_k": top_k, "mode": mode})
        except MCPError as exc:
            raise ToolError(str(exc)) from exc

    def create_escalation_ticket(self, user_id: str, question_text: str, reason: str) -> dict[str, str]:
        digest = hashlib.sha256(f"{user_id}|{question_text}|{reason}".encode("utf-8")).hexdigest()
        ticket_id = f"ESC-{int(digest[:8], 16) % 100000:05d}"
        return {"ticket_id": ticket_id, "status": "created", "reason": reason}

    def remember_user_context(self, user_id: str, note: str) -> dict[str, str]:
        self.memory.append_note(user_id, note)
        return {"status": "remembered"}


def route_tools(question: str) -> list[str]:
    lowered = question.lower()
    route = ["retrieve_policy"]
    if any(term in lowered for term in ["exception", "escalate", "approval unclear", "manager refused"]):
        route.append("create_escalation_ticket")
    if any(term in lowered for term in ["remember", "my team", "for future"]):
        route.append("remember_user_context")
    return route
