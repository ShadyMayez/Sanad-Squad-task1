"""Frozen sixty-case, source-grounded local Ollama evaluation."""
from __future__ import annotations

import asyncio
import csv
import json
from collections import Counter
from pathlib import Path

from content_pipeline.config import load_kb, settings
from content_pipeline.llm import LocalModel
from content_pipeline.schemas import AtomicClaim
from content_pipeline.semantic_verification import SemanticVerifier

HERE = Path(__file__).parent
LABELS = ("SUPPORTED", "CONTRADICTED", "INSUFFICIENT_EVIDENCE", "AMBIGUOUS", "VERIFICATION_ERROR")


def metrics(rows: list[dict]) -> dict:
    positives = [r for r in rows if r["expected"] == "SUPPORTED"]
    adverse = [r for r in rows if r["expected"] != "SUPPORTED"]
    predicted = [r for r in rows if r["actual"] == "SUPPORTED"]
    tp = sum(r["expected"] == "SUPPORTED" for r in predicted)
    return {
        "cases": len(rows),
        "supported_precision": tp / len(predicted) if predicted else None,
        "supported_recall": tp / len(positives) if positives else None,
        "false_acceptance_rate": sum(r["actual"] == "SUPPORTED" for r in adverse) / len(adverse) if adverse else None,
        "false_rejection_rate": sum(r["actual"] != "SUPPORTED" for r in positives) / len(positives) if positives else None,
        "five_label_accuracy": sum(r["actual"] == r["expected"] for r in rows) / len(rows) if rows else None,
        "confusion_matrix": {label: {actual: sum(r["expected"] == label and r["actual"] == actual for r in rows)
            for actual in LABELS} for label in LABELS},
        "by_category": {category: {"cases": len(items), "correct": sum(r["actual"] == r["expected"] for r in items)}
            for category in sorted({r["category"] for r in rows})
            for items in [[r for r in rows if r["category"] == category]]},
        "mean_latency_seconds": sum(r["latency_seconds"] for r in rows) / len(rows) if rows else None,
        "prompt_tokens_recorded": sum(r["input_tokens"] or 0 for r in rows),
        "completion_tokens_recorded": sum(r["output_tokens"] or 0 for r in rows),
        "usage_complete": all(r["input_tokens"] is not None and r["output_tokens"] is not None for r in rows),
    }


async def main() -> None:
    with (HERE / "fixtures/benchmark.tsv").open(newline="") as file:
        cases = list(csv.DictReader(file, delimiter="|"))
    assert len(cases) == 60 and len({case["id"] for case in cases}) == 60
    kb = load_kb()
    evidence = {e.id: e for vulnerability in kb.vulnerabilities for e in vulnerability.evidence}
    cfg = settings()
    verifier = SemanticVerifier(LocalModel(cfg["model"], cfg["base_url"], cfg["max_concurrency"], cfg["timeout"], cfg["transport_retries"]))
    rows: list[dict] = []
    for index, case in enumerate(cases):
        claim = case["claim"]
        atomic = AtomicClaim(id=case["id"], tweet_index=0, start=0, end=len(claim),
            span=claim, proposition=claim, sentence=claim, candidate_evidence_ids=[case["evidence_id"]])
        report, usage, latency = await verifier.run([atomic], [evidence[case["evidence_id"]]])
        verdict = report.verdicts[0]
        row = {**case, "split": "development" if index < 40 else "held_out", "actual": verdict.verdict,
            "reason": verdict.reason, "initial": verdict.initial_pass.model_dump() if verdict.initial_pass else None,
            "skeptical": verdict.skeptical_pass.model_dump() if verdict.skeptical_pass else None,
            "context_windows": [w.model_dump() for w in verdict.context_windows],
            "latency_seconds": round(latency, 3), "input_tokens": usage.get("input_tokens"),
            "output_tokens": usage.get("output_tokens")}
        rows.append(row)
        (HERE / "benchmark-progress.json").write_text(json.dumps(rows, indent=2) + "\n")
        print(f"{case['id']} {case['expected']} -> {verdict.verdict} ({latency:.1f}s)", flush=True)
    result = {"model": cfg["model"], "thresholds_predeclared": {
        "held_out_supported_recall_minimum": 0.70, "held_out_supported_precision_minimum": 0.90,
        "held_out_false_acceptance_maximum": 0.10},
        "development": metrics(rows[:40]), "held_out": metrics(rows[40:]), "all": metrics(rows), "rows": rows}
    (HERE / "benchmark-results.json").write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps({key: value for key, value in result.items() if key != "rows"}, indent=2), flush=True)


if __name__ == "__main__":
    asyncio.run(main())
