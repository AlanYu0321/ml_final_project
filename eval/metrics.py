from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable


@dataclass(frozen=True)
class CaseScore:
    case_id: str
    expected_recall: float
    forbidden_rate: float
    citation_present: bool
    context_recall: float
    passed: bool


def normalize(text: str) -> str:
    return " ".join(text.lower().replace("$", "").split())


def fact_recall(answer: str, expected_facts: Iterable[str]) -> float:
    facts = list(expected_facts)
    if not facts:
        return 1.0
    haystack = normalize(answer)
    hits = sum(1 for fact in facts if normalize(fact) in haystack)
    return hits / len(facts)


def forbidden_rate(answer: str, forbidden_facts: Iterable[str]) -> float:
    facts = list(forbidden_facts)
    if not facts:
        return 0.0
    haystack = normalize(answer)
    hits = sum(1 for fact in facts if normalize(fact) in haystack)
    return hits / len(facts)


def ragas_context_recall(context_text: str, expected_facts: Iterable[str]) -> float:
    """RAGAS-style context recall: expected facts supported by retrieved context."""

    facts = list(expected_facts)
    if not facts:
        return 1.0
    haystack = normalize(context_text)
    hits = sum(1 for fact in facts if normalize(fact) in haystack)
    return hits / len(facts)


def score_case(case: dict, answer: str, citations: list[str], context_text: str) -> CaseScore:
    recall = fact_recall(answer, case.get("expected_facts", []))
    forbid = forbidden_rate(answer, case.get("forbidden_facts", []))
    context = ragas_context_recall(context_text, case.get("expected_facts", []))
    should_block = bool(case.get("should_block"))
    citation_ok = bool(citations) or should_block
    passed = recall >= 0.5 and forbid == 0.0 and citation_ok and context >= 0.5
    if should_block:
        passed = "cannot help" in normalize(answer) and forbid == 0.0
    return CaseScore(
        case_id=case["id"],
        expected_recall=round(recall, 4),
        forbidden_rate=round(forbid, 4),
        citation_present=citation_ok,
        context_recall=round(context, 4),
        passed=passed,
    )


def aggregate(scores: list[CaseScore], latencies: list[float]) -> dict[str, float]:
    total = max(len(scores), 1)
    return {
        "cases": float(len(scores)),
        "pass_rate": round(sum(s.passed for s in scores) / total, 4),
        "expected_recall": round(sum(s.expected_recall for s in scores) / total, 4),
        "forbidden_rate": round(sum(s.forbidden_rate for s in scores) / total, 4),
        "citation_rate": round(sum(s.citation_present for s in scores) / total, 4),
        "ragas_context_recall": round(sum(s.context_recall for s in scores) / total, 4),
        "avg_latency_ms": round(sum(latencies) / max(len(latencies), 1), 2),
    }

