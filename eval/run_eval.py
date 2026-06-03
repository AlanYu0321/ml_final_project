from __future__ import annotations

import argparse
import csv
import json
import tempfile
from pathlib import Path

from policy_agent import PolicyOpsAgent
from eval.metrics import aggregate, score_case

ROOT = Path(__file__).resolve().parents[1]
GOLDEN = ROOT / "eval" / "golden.jsonl"
RESULTS = ROOT / "eval" / "results"


def load_golden(path: Path = GOLDEN) -> list[dict]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def run(mode: str) -> dict:
    RESULTS.mkdir(parents=True, exist_ok=True)
    cases = load_golden()
    with tempfile.TemporaryDirectory() as tmp:
        tmp_path = Path(tmp)
        agent = PolicyOpsAgent(memory_path=tmp_path / "memory.json", audit_path=tmp_path / "audit.log")
        rows = []
        scores = []
        latencies = []
        for case in cases:
            response = agent.ask(case["input"], user_id=case.get("user_id", "eval"), mode=mode)
            context_text = ""
            for call in response.tool_calls:
                if call.name == "retrieve_policy":
                    context_text = "\n".join(result.chunk.text for result in call.result)
            score = score_case(case, response.answer, response.citations, context_text)
            scores.append(score)
            latencies.append(response.latency_ms)
            rows.append(
                {
                    "id": case["id"],
                    "tags": ",".join(case.get("tags", [])),
                    "passed": score.passed,
                    "expected_recall": score.expected_recall,
                    "forbidden_rate": score.forbidden_rate,
                    "context_recall": score.context_recall,
                    "citation_present": score.citation_present,
                    "latency_ms": response.latency_ms,
                    "answer": response.answer,
                    "citations": ";".join(response.citations),
                }
            )
    summary = aggregate(scores, latencies)
    (RESULTS / f"{mode}_summary.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
    with (RESULTS / f"{mode}_cases.csv").open("w", encoding="utf-8", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)
    return {"mode": mode, "summary": summary}


def main() -> None:
    parser = argparse.ArgumentParser(description="Run golden-set evaluation.")
    parser.add_argument("--mode", choices=["baseline", "optimized", "both"], default="both")
    args = parser.parse_args()
    modes = ["baseline", "optimized"] if args.mode == "both" else [args.mode]
    outputs = [run(mode) for mode in modes]
    print(json.dumps(outputs, indent=2))


if __name__ == "__main__":
    main()

