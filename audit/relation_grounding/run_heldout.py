"""Run the frozen relation set once against real qwen3.5:4b; never tune on results."""
from __future__ import annotations

import asyncio
import json
import os
from collections import Counter
from pathlib import Path

from content_pipeline.config import load_kb, settings
from content_pipeline.llm import LocalModel
from content_pipeline.schemas import AtomicClaim
from content_pipeline.semantic_verification import SemanticVerifier

HERE = Path(__file__).parent
OUT = Path(os.environ.get("SANADSQUAD_RELATION_BENCHMARK_OUTPUT", str(HERE / "heldout-results.json")))
LABELS = ("SUPPORTED", "CONTRADICTED", "INSUFFICIENT_EVIDENCE", "AMBIGUOUS", "VERIFICATION_ERROR")


async def main():
    cases = json.loads((HERE / "fixtures/heldout.json").read_text())
    assert len(cases) == 20 and len({c["id"] for c in cases}) == 20
    assert sum(c["expected"] == "SUPPORTED" for c in cases) == 10
    sources = {e.id: e for v in load_kb().vulnerabilities for e in v.evidence}
    cfg = settings()
    model = LocalModel(cfg["model"], cfg["base_url"], cfg["max_concurrency"], cfg["timeout"], cfg["transport_retries"])
    verifier = SemanticVerifier(model)
    rows = []
    for c in cases:
        claim = AtomicClaim(id=c["id"], tweet_index=0, start=0, end=len(c["claim"]),
            span=c["claim"], proposition=c["claim"], sentence=c["claim"], candidate_evidence_ids=[c["evidence_id"]])
        report, usage, elapsed = await verifier.run([claim], [sources[c["evidence_id"]]])
        v = report.verdicts[0]
        row = {**c, "actual": v.verdict, "latency_seconds": round(elapsed, 3),
            "prompt_tokens": usage.get("input_tokens"), "completion_tokens": usage.get("output_tokens"),
            "initial_relation": v.initial_pass.evidence_relation if v.initial_pass else None,
            "skeptical_relation": v.skeptical_pass.evidence_relation if v.skeptical_pass else None,
            "relation_integrity_passed": v.relation_integrity_passed,
            "relation_error": v.relation_error, "reason": v.reason,
            "selected_source_roles": v.selected_source_roles}
        rows.append(row)
        OUT.with_name(OUT.stem + "-progress.json").write_text(json.dumps(rows, indent=2) + "\n")
        print(f'{c["id"]} {c["expected"]} -> {v.verdict} ({elapsed:.1f}s)', flush=True)
    expected_supported = [r for r in rows if r["expected"] == "SUPPORTED"]
    predicted_supported = [r for r in rows if r["actual"] == "SUPPORTED"]
    adverse = [r for r in rows if r["expected"] != "SUPPORTED"]
    causal_negative = [r for r in rows if r["category"] in {"unsupported_causal_inversion", "cause_effect_reversal", "topic_only"}]
    causal_positive = [r for r in rows if r["category"] == "supported_causal"]
    recommendations = [r for r in rows if "supported_recommendation" in r["category"] or r["category"] == "supported_conditional_recommendation"]
    metrics = {
        "count": len(rows),
        "supported_precision": sum(r["expected"] == "SUPPORTED" for r in predicted_supported) / len(predicted_supported) if predicted_supported else None,
        "supported_recall": sum(r["actual"] == "SUPPORTED" for r in expected_supported) / len(expected_supported),
        "false_acceptance_rate": sum(r["actual"] == "SUPPORTED" for r in adverse) / len(adverse),
        "unsupported_causal_false_accepts": [r["id"] for r in causal_negative if r["actual"] == "SUPPORTED"],
        "supported_causal_false_rejects": [r["id"] for r in causal_positive if r["actual"] != "SUPPORTED"],
        "recommendation_paraphrase_recall": sum(r["actual"] == "SUPPORTED" for r in recommendations) / len(recommendations),
        "five_label_accuracy": sum(r["expected"] == r["actual"] for r in rows) / len(rows),
        "source_relation_classification_accuracy": sum(r["expected_relation"] == r["initial_relation"] for r in rows) / len(rows),
        "confusion_matrix": {e: {a: sum(r["expected"] == e and r["actual"] == a for r in rows) for a in LABELS} for e in LABELS},
        "mean_latency_seconds": round(sum(r["latency_seconds"] for r in rows) / len(rows), 3),
        "prompt_tokens_recorded": sum(r["prompt_tokens"] or 0 for r in rows),
        "completion_tokens_recorded": sum(r["completion_tokens"] or 0 for r in rows),
        "usage_complete": all(r["prompt_tokens"] is not None and r["completion_tokens"] is not None for r in rows),
        "external_model_api_charges_usd": 0.0,
    }
    OUT.write_text(json.dumps({"model": cfg["model"], "metrics": metrics, "rows": rows}, indent=2) + "\n")
    print(json.dumps(metrics, indent=2))


if __name__ == "__main__":
    asyncio.run(main())
