"""Execute real Ollama 3-post marketing qualification under Directive SANADSQUAD_V3_MARKETING_PUBLICATION_INTEGRITY_03.

Runs real Ollama (qwen3.5:4b) inference across the 3 marketing service lines:
- Slot 1: web3-security (Differentiation post)
- Slot 2: agentic-security (News reaction post with verified link)
- Slot 3: agentic-payments (Learning resource post with verified link and accurate x402 mechanics)

All posts are generated with company-contact.json on disk (approved: false), verifying:
- 0 unapproved contact details or synthetic demo placeholders exported.
- Valid live HTTP 200 source URLs on allowlisted domains.
- Meaningful format semantics and exact source-to-claim alignment.
- Output exported to output/v3_marketing_publication_qualification/.
"""
from __future__ import annotations

import asyncio
import json
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from content_pipeline.cli import execute
from content_pipeline.schemas import Plan, Slot


async def main():
    output_dir = ROOT / "output" / "v3_marketing_publication_qualification"
    if output_dir.exists():
        import shutil
        shutil.rmtree(output_dir)

    plan = Plan(slots=[
        Slot(id="post_1", type="marketing-post", focus="web3-security"),
        Slot(id="post_2", type="marketing-post", focus="agentic-security"),
        Slot(id="post_3", type="marketing-post", focus="agentic-payments"),
    ])

    print("Starting real Ollama (qwen3.5:4b) 3-post marketing qualification...")
    print(f"Output directory: {output_dir}")
    print(f"Mode: v3, Research Mode: fixture, Authorization Mode: publication_eligible")

    summary = await execute(
        plan=plan,
        output=output_dir,
        mode="v3",
        research_mode="fixture",
        authorization_mode="publication_eligible",
    )

    print("\n--- Marketing Qualification Summary ---")
    print(json.dumps(summary, indent=2))
    return 0 if summary.get("shipped", 0) == 3 else 1


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
