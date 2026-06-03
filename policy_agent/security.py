from __future__ import annotations

import re
from dataclasses import dataclass


class SecurityError(ValueError):
    pass


@dataclass(frozen=True)
class SecurityDecision:
    allowed: bool
    reason: str
    tags: list[str]


PII_PATTERNS = [
    re.compile(r"\b\d{3}-\d{2}-\d{4}\b"),
    re.compile(r"\b(?:\d[ -]*?){13,16}\b"),
]

INJECTION_PATTERNS = [
    re.compile(r"ignore (all )?(previous|prior) instructions", re.I),
    re.compile(r"reveal (the )?(system|developer) prompt", re.I),
    re.compile(r"bypass (approval|policy|guardrail)", re.I),
    re.compile(r"exfiltrate|dump all|secret token", re.I),
]

DANGEROUS_ACTIONS = [
    "delete approval",
    "approve my own",
    "skip legal",
    "send customer pii",
    "disable audit",
]


def validate_question(question: str) -> str:
    cleaned = " ".join(question.strip().split())
    if not cleaned:
        raise SecurityError("Question cannot be empty.")
    if len(cleaned) > 1200:
        raise SecurityError("Question is too long for this assistant.")
    return cleaned


def inspect_question(question: str) -> SecurityDecision:
    tags: list[str] = []
    if any(pattern.search(question) for pattern in PII_PATTERNS):
        tags.append("pii")
    if any(pattern.search(question) for pattern in INJECTION_PATTERNS):
        tags.append("prompt_injection")
    lowered = question.lower()
    if any(action in lowered for action in DANGEROUS_ACTIONS):
        tags.append("dangerous_action")
    if tags:
        return SecurityDecision(False, "Blocked by policy guardrails: " + ", ".join(tags), tags)
    return SecurityDecision(True, "allowed", tags)


def authorize_tool(tool_name: str, question: str) -> SecurityDecision:
    lowered = question.lower()
    if tool_name == "create_escalation_ticket" and ("bypass" in lowered or "skip legal" in lowered):
        return SecurityDecision(False, "Escalation tool cannot be used to bypass approvals.", ["tool_permission"])
    return SecurityDecision(True, "allowed", [])

