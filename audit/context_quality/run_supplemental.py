"""Four predeclared coverage probes for AMBIGUOUS and VERIFICATION_ERROR."""
from __future__ import annotations

import asyncio
import hashlib
import json
from pathlib import Path

from content_pipeline.config import ROOT, settings
from content_pipeline.llm import LocalModel
from content_pipeline.schemas import AtomicClaim, Evidence
from content_pipeline.semantic_verification import SemanticVerifier

HERE = Path(__file__).parent
CASES = [
    ("ambiguous-a", "The vault can fail.", "AMBIGUOUS", False),
    ("ambiguous-b", "The bridge can be stale.", "AMBIGUOUS", False),
    ("ambiguous-a", "The vault can fail.", "VERIFICATION_ERROR", True),
    ("ambiguous-b", "The bridge can be stale.", "VERIFICATION_ERROR", True),
]


async def main() -> None:
    cfg = settings()
    verifier = SemanticVerifier(LocalModel(cfg["model"], cfg["base_url"], cfg["max_concurrency"], cfg["timeout"], cfg["transport_retries"]))
    rows = []
    for index, (name, claim, expected, tamper) in enumerate(CASES, 1):
        path = HERE / "fixtures" / f"{name}.txt"
        quote = path.read_text().strip()
        evidence = Evidence(id=f"SYNTH-{name}", url="https://example.invalid/ambiguity-fixture",
            excerpt=quote, source_title="Synthetic ambiguity fixture", source_type="synthetic test",
            snapshot_path=str(path.relative_to(ROOT)),
            snapshot_sha256="0" * 64 if tamper else hashlib.sha256(path.read_bytes()).hexdigest(),
            retrieved_at="2026-10-16", source_quote=quote, quote_start=0, quote_end=len(quote),
            scope="Synthetic language ambiguity test only")
        atomic = AtomicClaim(id=f"supplemental-{index}", tweet_index=0, start=0, end=len(claim),
            span=claim, proposition=claim, sentence=claim, candidate_evidence_ids=[evidence.id])
        report, usage, latency = await verifier.run([atomic], [evidence])
        verdict = report.verdicts[0]
        rows.append({"id": index, "source": name, "claim": claim, "expected": expected,
            "actual": verdict.verdict, "reason": verdict.reason, "latency_seconds": round(latency, 3),
            "input_tokens": usage.get("input_tokens"), "output_tokens": usage.get("output_tokens")})
        print(f"{index}: {expected} -> {verdict.verdict}", flush=True)
    (HERE / "supplemental-results.json").write_text(json.dumps(rows, indent=2) + "\n")


if __name__ == "__main__":
    asyncio.run(main())
