"""Run the golden set against a live Craftify /ask backend."""

from __future__ import annotations

import argparse
import json
import sys
from collections import defaultdict
from pathlib import Path

import httpx

HERE = Path(__file__).resolve().parent
QUESTIONS_PATH = HERE / "questions.json"
ABSTAIN = "I couldn't find enough information in the provided documentation to answer that."


def load_questions() -> list[dict]:
    return json.loads(QUESTIONS_PATH.read_text(encoding="utf-8"))


def ask(client: httpx.Client, base_url: str, question: str) -> dict:
    response = client.post(f"{base_url.rstrip('/')}/ask", json={"question": question})
    response.raise_for_status()
    return response.json()


def contains_all(text: str, needles: list[str]) -> bool:
    hay = text.lower()
    return all(n.lower() in hay for n in needles)


def score_item(item: dict, result: dict) -> dict:
    expected = item["expected_type"]
    actual = result.get("type")
    routing = 2 if actual == expected else 0
    notes: list[str] = []
    metrics: dict[str, int] = {}
    passed = actual == expected

    if expected == "answer":
        answer = result.get("answer") or ""
        sources = result.get("sources") or []
        docs = {s.get("document", "") for s in sources}
        expected_docs = set(item.get("expected_documents") or [])
        must = item.get("must_include") or []
        hits = sum(1 for n in must if n.lower() in answer.lower())
        correctness = 3 if actual == "answer" and hits == len(must) else (
            2 if actual == "answer" and hits else (1 if actual == "answer" else 0)
        )
        grounding = 2 if expected_docs and expected_docs & docs else (
            1 if docs else 0
        )
        completeness = 2 if hits == len(must) and must else (1 if hits else 0)
        metrics = {
            "correctness": correctness,
            "grounding": grounding,
            "completeness": completeness,
        }
        passed = correctness >= 2 and grounding >= 2
        if expected_docs and not (expected_docs & docs):
            notes.append(f"missing sources {sorted(expected_docs)}")
        if hits < len(must):
            notes.append(f"missing keywords {must}")

    elif expected == "tool_call":
        args = result.get("arguments") or {}
        summary = args.get("summary") or ""
        arg_needles = item.get("summary_must_include") or []
        args_ok = 1 if contains_all(summary, arg_needles) else 0
        metrics = {"routing": routing, "tool_arguments": args_ok}
        passed = routing == 2 and args_ok == 1
        if not args_ok:
            notes.append(f"summary missing {arg_needles}: {summary!r}")

    elif expected in {"clarification", "refusal", "abstention"}:
        metrics = {"guardrail": routing}
        if expected == "abstention":
            message = result.get("message") or ""
            if message != ABSTAIN:
                notes.append("abstention wording drifted")
                passed = False
        passed = passed and routing == 2

    else:
        metrics = {"routing": routing}

    return {
        "id": item["id"],
        "category": item["category"],
        "question": item["question"],
        "expected_type": expected,
        "actual_type": actual,
        "passed": passed,
        "metrics": metrics,
        "notes": notes,
        "result": result,
    }


def print_report(rows: list[dict]) -> int:
    by_cat: dict[str, list[dict]] = defaultdict(list)
    for row in rows:
        by_cat[row["category"]].append(row)

    print("Craftify golden-set evaluation")
    print("=" * 56)
    for category, items in by_cat.items():
        passed = sum(1 for i in items if i["passed"])
        print(f"\n{category}: {passed}/{len(items)} passed")
        for item in items:
            mark = "PASS" if item["passed"] else "FAIL"
            print(f"  [{mark}] {item['id']} type={item['actual_type']} {item['metrics']}")
            if item["notes"]:
                print(f"         {'; '.join(item['notes'])}")
            if item["actual_type"] == "answer":
                print(f"         {item['result'].get('answer', '')[:160]}")

    total = len(rows)
    passed = sum(1 for r in rows if r["passed"])
    failed = total - passed
    accuracy = (passed / total * 100) if total else 0.0
    print("\n" + "=" * 56)
    print(f"Total: {total}   Passed: {passed}   Failed: {failed}   Accuracy: {accuracy:.1f}%")
    return 0 if failed == 0 else 1


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--base-url", default="http://127.0.0.1:8000")
    args = parser.parse_args()
    questions = load_questions()
    rows: list[dict] = []
    with httpx.Client(timeout=90.0) as client:
        try:
            health = client.get(f"{args.base_url.rstrip('/')}/health")
            health.raise_for_status()
        except httpx.HTTPError as exc:
            print(f"Backend is not reachable at {args.base_url}: {exc}", file=sys.stderr)
            return 2
        for item in questions:
            try:
                result = ask(client, args.base_url, item["question"])
            except httpx.HTTPError as exc:
                result = {"type": "error", "message": str(exc)}
            rows.append(score_item(item, result))
    return print_report(rows)


if __name__ == "__main__":
    raise SystemExit(main())
