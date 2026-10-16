"""Re-evaluate the saved attempt-two oracle claim against its pinned source."""
from __future__ import annotations

import asyncio
import json
from pathlib import Path

from content_pipeline.config import load_kb, settings
from content_pipeline.llm import LocalModel
from content_pipeline.schemas import AtomicClaim
from content_pipeline.semantic_verification import SemanticVerifier


async def main() -> None:
    evidence = next(e for v in load_kb().vulnerabilities for e in v.evidence if e.id == "SCWE-028")
    sentence = "It may cause loss of funds or data."
    claim = AtomicClaim(id="thread_3_attempt_2_t3s1c1", tweet_index=2, start=0, end=len(sentence),
        span=sentence, proposition=sentence, sentence=sentence, candidate_evidence_ids=[evidence.id])
    cfg = settings()
    model = LocalModel(cfg["model"], cfg["base_url"], cfg["max_concurrency"], cfg["timeout"], cfg["transport_retries"])
    report, usage, latency = await SemanticVerifier(model).run([claim], [evidence])
    result = {"model": cfg["model"], "claim": claim.model_dump(), "source_id": evidence.id,
        "snapshot_sha256": evidence.snapshot_sha256, "report": report.model_dump(),
        "usage": usage, "latency_seconds": round(latency, 3)}
    path = Path(__file__).parent / "thread3-reproduction.json"
    path.write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps({"verdict": report.verdicts[0].verdict, "latency_seconds": round(latency, 3),
        "usage": usage}, indent=2))


if __name__ == "__main__":
    asyncio.run(main())
