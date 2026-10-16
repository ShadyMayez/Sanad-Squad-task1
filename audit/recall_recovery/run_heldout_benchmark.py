"""Run the 64-case frozen held-out benchmark against real local qwen3.5:4b."""
from __future__ import annotations

import asyncio
import json
import os
import sys
import time
from pathlib import Path

from content_pipeline.config import load_kb, settings
from content_pipeline.llm import LocalModel
from content_pipeline.schemas import AtomicClaim
from content_pipeline.semantic_verification import SemanticVerifier

HERE = Path(__file__).parent
FIXTURE = HERE / "fixtures/heldout_benchmark.json"
OUT = Path(os.environ.get("SANADSQUAD_BENCHMARK_OUTPUT", str(HERE / "heldout-benchmark-results.json")))
LABELS = ("SUPPORTED", "CONTRADICTED", "INSUFFICIENT_EVIDENCE", "AMBIGUOUS", "VERIFICATION_ERROR")


async def main():
    cases = json.loads(FIXTURE.read_text())
    assert len(cases) == 64, f"Expected 64 cases, got {len(cases)}"
    assert len({c["id"] for c in cases}) == 64, "Duplicate case IDs"
    sources = {e.id: e for v in load_kb().vulnerabilities for e in v.evidence}
    cfg = settings()
    model = LocalModel(cfg["model"], cfg["base_url"], cfg["max_concurrency"], cfg["timeout"], cfg["transport_retries"])
    verifier = SemanticVerifier(model)
    rows = []
    
    print(f"Starting 64-case frozen benchmark evaluation against {cfg['model']}...", flush=True)
    started_all = time.monotonic()
    
    for i, c in enumerate(cases, 1):
        claim = AtomicClaim(
            id=c["id"], tweet_index=0, start=0, end=len(c["claim"]),
            span=c["claim"], proposition=c["claim"], sentence=c["claim"],
            candidate_evidence_ids=[c["evidence_id"]]
        )
        report, usage, elapsed = await verifier.run([claim], [sources[c["evidence_id"]]])
        v = report.verdicts[0]
        row = {
            **c,
            "actual": v.verdict,
            "latency_seconds": round(elapsed, 3),
            "prompt_tokens": usage.get("input_tokens"),
            "completion_tokens": usage.get("output_tokens"),
            "initial_relation": v.initial_pass.evidence_relation if v.initial_pass else None,
            "initial_verdict": v.initial_pass.verdict if v.initial_pass else None,
            "skeptical_relation": v.skeptical_pass.evidence_relation if v.skeptical_pass else None,
            "skeptical_verdict": v.skeptical_pass.verdict if v.skeptical_pass else None,
            "relation_integrity_passed": v.relation_integrity_passed,
            "relation_error": v.relation_error,
            "reason": v.reason,
            "selected_source_roles": v.selected_source_roles,
        }
        rows.append(row)
        OUT.with_name(OUT.stem + "-progress.json").write_text(json.dumps(rows, indent=2) + "\n")
        print(f"[{i}/64] {c['id']} ({c['category']}): expected {c['expected']} -> actual {v.verdict} ({elapsed:.1f}s)", flush=True)

    total_elapsed = time.monotonic() - started_all
    expected_supported = [r for r in rows if r["expected"] == "SUPPORTED"]
    predicted_supported = [r for r in rows if r["actual"] == "SUPPORTED"]
    adverse = [r for r in rows if r["expected"] != "SUPPORTED"]
    causal_negative = [r for r in rows if r["category"] in {"unsupported_causal_inversion", "cause_effect_reversal", "category_confusion"}]
    causal_positive = [r for r in rows if r["category"] == "supported_causal"]
    recommendations = [r for r in rows if "recommendation" in r["category"]]

    supported_precision = sum(r["expected"] == "SUPPORTED" for r in predicted_supported) / len(predicted_supported) if predicted_supported else 0.0
    supported_recall = sum(r["actual"] == "SUPPORTED" for r in expected_supported) / len(expected_supported) if expected_supported else 0.0
    false_acceptance_rate = sum(r["actual"] == "SUPPORTED" for r in adverse) / len(adverse) if adverse else 0.0
    rec_recall = sum(r["actual"] == "SUPPORTED" for r in recommendations) / len(recommendations) if recommendations else 0.0
    five_label_acc = sum(r["expected"] == r["actual"] for r in rows) / len(rows)
    relation_acc = sum(r["expected_relation"] == r["initial_relation"] for r in rows) / len(rows)

    metrics = {
        "count": len(rows),
        "total_elapsed_seconds": round(total_elapsed, 2),
        "supported_precision": round(supported_precision, 4),
        "supported_recall": round(supported_recall, 4),
        "false_acceptance_rate": round(false_acceptance_rate, 4),
        "unsupported_causal_false_accepts": [r["id"] for r in causal_negative if r["actual"] == "SUPPORTED"],
        "supported_causal_false_rejects": [r["id"] for r in causal_positive if r["actual"] != "SUPPORTED"],
        "recommendation_paraphrase_recall": round(rec_recall, 4),
        "five_label_accuracy": round(five_label_acc, 4),
        "source_relation_classification_accuracy": round(relation_acc, 4),
        "confusion_matrix": {e: {a: sum(r["expected"] == e and r["actual"] == a for r in rows) for a in LABELS} for e in LABELS},
        "mean_latency_seconds": round(sum(r["latency_seconds"] for r in rows) / len(rows), 3),
        "prompt_tokens_recorded": sum(r["prompt_tokens"] or 0 for r in rows),
        "completion_tokens_recorded": sum(r["completion_tokens"] or 0 for r in rows),
        "usage_complete": all(r["prompt_tokens"] is not None and r["completion_tokens"] is not None for r in rows),
        "external_model_api_charges_usd": 0.0,
    }

    result_payload = {"model": cfg["model"], "metrics": metrics, "rows": rows}
    OUT.write_text(json.dumps(result_payload, indent=2) + "\n")
    print("\n=== BENCHMARK EVALUATION SUMMARY ===", flush=True)
    print(json.dumps(metrics, indent=2), flush=True)
    return metrics


if __name__ == "__main__":
    asyncio.run(main())
