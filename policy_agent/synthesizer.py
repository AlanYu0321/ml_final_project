from __future__ import annotations

import re
from dataclasses import dataclass

from .retrieval import RetrievalResult


class SynthesisError(RuntimeError):
    pass


@dataclass(frozen=True)
class SynthesizedAnswer:
    answer: str
    citations: list[str]


class ExtractiveSynthesizer:
    """Deterministic answer composer used in place of an external LLM."""

    def synthesize(
        self,
        *,
        question: str,
        contexts: list[RetrievalResult],
        memory: dict[str, object],
        escalation: dict[str, str] | None = None,
    ) -> SynthesizedAnswer:
        if not contexts:
            raise SynthesisError("No policy context retrieved.")
        bullets: list[str] = []
        citations: list[str] = []
        for result in contexts[:3]:
            sentences = _split_sentences(result.chunk.text)
            selected = _select_sentences(question, sentences)
            for sentence in selected[:2]:
                if sentence not in bullets:
                    bullets.append(sentence)
            citations.append(f"{result.chunk.source}#{result.chunk.doc_id}")
        if memory.get("notes"):
            bullets.append(f"User context remembered: {'; '.join(str(n) for n in memory['notes'][-2:])}.")
        if escalation:
            bullets.append(f"Escalation ticket {escalation['ticket_id']} was created because {escalation['reason']}.")
        answer = " ".join(bullets[:7])
        return SynthesizedAnswer(answer=answer, citations=citations)


def _split_sentences(text: str) -> list[str]:
    cleaned = " ".join(line.strip("- ").strip() for line in text.splitlines() if line.strip())
    return [s.strip() for s in re.split(r"(?<=[.!?])\s+", cleaned) if len(s.strip()) > 8]


def _select_sentences(question: str, sentences: list[str]) -> list[str]:
    q_tokens = set(re.findall(r"[a-z0-9]+", question.lower()))
    scored: list[tuple[int, str]] = []
    for sentence in sentences:
        s_tokens = set(re.findall(r"[a-z0-9]+", sentence.lower()))
        scored.append((len(q_tokens.intersection(s_tokens)), sentence))
    ranked = [s for score, s in sorted(scored, key=lambda item: item[0], reverse=True) if score > 0]
    return ranked or sentences[:2]

