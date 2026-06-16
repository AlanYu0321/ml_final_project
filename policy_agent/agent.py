from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from time import perf_counter
from typing import Any

from .audit import AuditLogger
from .memory import JsonMemoryStore
from .retrieval import PolicyRetriever, RetrievalResult
from .security import SecurityError, inspect_question, validate_question
from .synthesizer import ExtractiveSynthesizer, SynthesizedAnswer, SynthesisError
from .tools import ToolCall, ToolError, ToolRegistry, route_tools


@dataclass(frozen=True)
class AgentResponse:
    answer: str
    citations: list[str]
    tool_calls: list[ToolCall]
    blocked: bool
    decision: str
    latency_ms: float
    metadata: dict[str, Any]


class PolicyOpsAgent:
    def __init__(
        self,
        *,
        retriever: PolicyRetriever | None = None,
        memory_path: Path | None = None,
        audit_path: Path | None = None,
        synthesizer: ExtractiveSynthesizer | None = None,
        max_retries: int = 1,
    ) -> None:
        self.retriever = retriever or PolicyRetriever()
        self.memory = JsonMemoryStore(memory_path)
        self.audit = AuditLogger(audit_path)
        self.tools = ToolRegistry(self.retriever, self.memory)
        self.synthesizer = synthesizer or ExtractiveSynthesizer()
        self.max_retries = max_retries

    def ask(self, question: str, *, user_id: str = "demo", mode: str = "optimized") -> AgentResponse:
        start = perf_counter()
        tool_calls: list[ToolCall] = []
        mcp_start = len(self.tools.mcp_client.call_history)
        try:
            cleaned = validate_question(question)
        except SecurityError as exc:
            return self._blocked(str(exc), user_id, question, start)

        security = inspect_question(cleaned)
        if not security.allowed:
            return self._blocked(security.reason, user_id, cleaned, start, metadata={"tags": security.tags})

        contexts: list[RetrievalResult] = []
        escalation: dict[str, str] | None = None
        try:
            for tool_name in route_tools(cleaned):
                if tool_name == "retrieve_policy":
                    call = self.tools.call(tool_name, question=cleaned, query=cleaned, top_k=4, mode=mode)
                    contexts = call.result
                elif tool_name == "create_escalation_ticket":
                    call = self.tools.call(
                        tool_name,
                        question=cleaned,
                        user_id=user_id,
                        question_text=cleaned,
                        reason="policy exception or unclear approval path",
                    )
                    escalation = call.result
                else:
                    call = self.tools.call(
                        tool_name,
                        question=cleaned,
                        user_id=user_id,
                        note=_memory_note_from_question(cleaned),
                    )
                tool_calls.append(call)
        except ToolError as exc:
            return self._blocked(str(exc), user_id, cleaned, start)

        try:
            synthesis = self._synthesize_with_retry(
                question=cleaned,
                contexts=contexts,
                memory=self.memory.get_user(user_id),
                escalation=escalation,
            )
        except SynthesisError as exc:
            return self._blocked(f"Unable to answer with retrieved policy context: {exc}", user_id, cleaned, start)
        mcp_tools = [call.name for call in self.tools.mcp_client.call_history[mcp_start:]]
        self.audit.write(
            event_type="agent_response",
            user_id=user_id,
            question=cleaned,
            decision="answered",
            tool_calls=[call.name for call in tool_calls],
            metadata={"citations": synthesis.citations, "mode": mode, "mcp_tools": mcp_tools},
        )
        return AgentResponse(
            answer=synthesis.answer,
            citations=synthesis.citations,
            tool_calls=tool_calls,
            blocked=False,
            decision="answered",
            latency_ms=round((perf_counter() - start) * 1000, 2),
            metadata={"mode": mode, "retrieved": len(contexts), "mcp_tools": mcp_tools},
        )

    def _synthesize_with_retry(
        self,
        *,
        question: str,
        contexts: list[RetrievalResult],
        memory: dict[str, object],
        escalation: dict[str, str] | None,
    ) -> SynthesizedAnswer:
        last_error: Exception | None = None
        for _ in range(self.max_retries + 1):
            try:
                return self.synthesizer.synthesize(
                    question=question,
                    contexts=contexts,
                    memory=memory,
                    escalation=escalation,
                )
            except SynthesisError as exc:
                last_error = exc
        raise SynthesisError(f"Synthesis failed after retries: {last_error}")

    def _blocked(
        self,
        reason: str,
        user_id: str,
        question: str,
        start: float,
        metadata: dict[str, Any] | None = None,
    ) -> AgentResponse:
        self.audit.write(
            event_type="agent_response",
            user_id=user_id,
            question=question,
            decision="blocked",
            tool_calls=[],
            metadata=metadata or {"reason": reason},
        )
        return AgentResponse(
            answer=f"I cannot help with that request. {reason}",
            citations=[],
            tool_calls=[],
            blocked=True,
            decision="blocked",
            latency_ms=round((perf_counter() - start) * 1000, 2),
            metadata=metadata or {"reason": reason},
        )


def _memory_note_from_question(question: str) -> str:
    return question[:180]
