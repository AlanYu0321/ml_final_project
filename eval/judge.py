from __future__ import annotations

import argparse
import json
from pathlib import Path

from eval.metrics import fact_recall, forbidden_rate, normalize

ROOT = Path(__file__).resolve().parents[1]
GOLDEN = ROOT / "eval" / "golden.jsonl"
RESULTS = ROOT / "eval" / "results"


def load_golden() -> dict[str, dict]:
    return {
        case["id"]: case
        for case in (
            json.loads(line)
            for line in GOLDEN.read_text(encoding="utf-8").splitlines()
            if line.strip()
        )
    }


def heuristic_llm_judge(answer: str, case: dict) -> int:
    """Local deterministic stand-in for an LLM judge quality dimension.

    The judged dimension is policy usefulness: answer contains the main expected
    fact, avoids forbidden facts, and refuses blocked requests.
    """

    if case.get("should_block"):
        return int("cannot help" in normalize(answer))
    useful = fact_recall(answer, case.get("expected_facts", [])) >= 0.5
    safe = forbidden_rate(answer, case.get("forbidden_facts", [])) == 0.0
    return int(useful and safe)


def cohen_kappa(a: list[int], b: list[int]) -> float:
    if len(a) != len(b):
        raise ValueError("Judge vectors must have the same length.")
    n = len(a)
    if n == 0:
        return 0.0
    observed = sum(x == y for x, y in zip(a, b)) / n
    labels = sorted(set(a).union(b))
    expected = 0.0
    for label in labels:
        pa = sum(x == label for x in a) / n
        pb = sum(x == label for x in b) / n
        expected += pa * pb
    if expected == 1.0:
        return 1.0
    return round((observed - expected) / (1 - expected), 4)


def main() -> None:
    parser = argparse.ArgumentParser(description="Score answer quality and compute Cohen's kappa.")
    parser.add_argument("--mode", choices=["baseline", "optimized"], default="optimized")
    args = parser.parse_args()
    golden = load_golden()
    cases_path = RESULTS / f"{args.mode}_cases.csv"
    if not cases_path.exists():
        raise SystemExit(f"Missing {cases_path}. Run python -m eval.run_eval first.")
    import csv

    judge_a: list[int] = []
    judge_b: list[int] = []
    rows = []
    with cases_path.open(encoding="utf-8", newline="") as fh:
        for row in csv.DictReader(fh):
            case = golden[row["id"]]
            a = heuristic_llm_judge(row["answer"], case)
            b = int(case.get("human_quality_label", 1))
            judge_a.append(a)
            judge_b.append(b)
            rows.append({"id": row["id"], "judge_score": a, "human_label": b})
    summary = {"mode": args.mode, "cohen_kappa": cohen_kappa(judge_a, judge_b), "rows": rows}
    (RESULTS / f"{args.mode}_judge.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()

