from __future__ import annotations

from eval.metrics import fact_recall, forbidden_rate, ragas_context_recall


def test_fact_recall_scores_expected_fact() -> None:
    assert fact_recall("Expenses over 500 dollars require manager approval before purchase.", ["manager approval"]) == 1.0


def test_forbidden_rate_scores_hallucinated_fact() -> None:
    assert forbidden_rate("No approval is needed.", ["No approval is needed"]) == 1.0


def test_context_recall_finds_grounding() -> None:
    context = "Customer data must be encrypted in transit and at rest."
    assert ragas_context_recall(context, ["Customer data must be encrypted in transit and at rest"]) == 1.0

