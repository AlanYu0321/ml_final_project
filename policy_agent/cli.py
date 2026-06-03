from __future__ import annotations

import argparse
import json

from .agent import PolicyOpsAgent


def main() -> None:
    parser = argparse.ArgumentParser(description="Ask the Policy Ops Agent a question.")
    parser.add_argument("question", nargs="*", help="Question to ask. If omitted, enters interactive mode.")
    parser.add_argument("--user-id", default="demo")
    parser.add_argument("--mode", choices=["baseline", "optimized"], default="optimized")
    parser.add_argument("--json", action="store_true", help="Print raw JSON response.")
    args = parser.parse_args()

    agent = PolicyOpsAgent()
    if args.question:
        _print_response(agent.ask(" ".join(args.question), user_id=args.user_id, mode=args.mode), args.json)
        return

    while True:
        try:
            question = input("policy-agent> ").strip()
        except EOFError:
            break
        if question.lower() in {"exit", "quit"}:
            break
        if question:
            _print_response(agent.ask(question, user_id=args.user_id, mode=args.mode), args.json)


def _print_response(response, as_json: bool) -> None:
    if as_json:
        print(
            json.dumps(
                {
                    "answer": response.answer,
                    "citations": response.citations,
                    "blocked": response.blocked,
                    "decision": response.decision,
                    "latency_ms": response.latency_ms,
                    "tool_calls": [call.name for call in response.tool_calls],
                    "metadata": response.metadata,
                },
                indent=2,
            )
        )
        return
    print(response.answer)
    if response.citations:
        print("Citations: " + ", ".join(response.citations))
    print("Tools: " + ", ".join(call.name for call in response.tool_calls))


if __name__ == "__main__":
    main()

