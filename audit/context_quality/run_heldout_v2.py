"""Fresh independently labeled 20-case holdout after coreference calibration."""
from __future__ import annotations

import asyncio
import csv
import json
from pathlib import Path

from content_pipeline.config import load_kb, settings
from content_pipeline.llm import LocalModel
from content_pipeline.schemas import AtomicClaim
from content_pipeline.semantic_verification import SemanticVerifier
from run_benchmark import metrics

HERE = Path(__file__).parent


async def main() -> None:
    with (HERE / "fixtures/heldout-v2.tsv").open(newline="") as file:
        cases = list(csv.DictReader(file, delimiter="|"))
    assert len(cases) == 20 and sum(c["expected"] == "SUPPORTED" for c in cases) == 10
    evidence = {e.id: e for v in load_kb().vulnerabilities for e in v.evidence}
    cfg = settings()
    verifier = SemanticVerifier(LocalModel(cfg["model"], cfg["base_url"], cfg["max_concurrency"], cfg["timeout"], cfg["transport_retries"]))
    rows = []
    for case in cases:
        text = case["claim"]
        atomic = AtomicClaim(id=case["id"], tweet_index=0, start=0, end=len(text),
            span=text, proposition=text, sentence=text, candidate_evidence_ids=[case["evidence_id"]])
        report, usage, latency = await verifier.run([atomic], [evidence[case["evidence_id"]]])
        verdict = report.verdicts[0]
        rows.append({**case, "actual": verdict.verdict, "reason": verdict.reason,
            "initial": verdict.initial_pass.model_dump() if verdict.initial_pass else None,
            "skeptical": verdict.skeptical_pass.model_dump() if verdict.skeptical_pass else None,
            "latency_seconds": round(latency, 3), "input_tokens": usage.get("input_tokens"),
            "output_tokens": usage.get("output_tokens")})
        (HERE / "heldout-v2-progress.json").write_text(json.dumps(rows, indent=2) + "\n")
        print(case["id"], case["expected"], "->", verdict.verdict, flush=True)
    result = {"model": cfg["model"], "thresholds_predeclared": {
        "supported_recall_minimum": 0.70, "supported_precision_minimum": 0.90,
        "false_acceptance_maximum": 0.10}, "metrics": metrics(rows), "rows": rows}
    (HERE / "heldout-v2-results.json").write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps(result["metrics"], indent=2), flush=True)


if __name__ == "__main__":
    asyncio.run(main())
