"""Real-Model Qualification Runner for Marketing Yield and Performance Closure.

Directive: SANADSQUAD_V3_MARKETING_YIELD_PERFORMANCE_CLOSURE_01

Executes:
A. 5-Service Qualification (Ollama qwen3.5:4b) into output/v3_five_service_closure/
B. 6-Slot Weekly Execution (3 technical threads, 3 marketing posts) into output/v3_weekly_closure/

Records exact runtimes, token usage, post texts, character counts, revision frequency,
and verification verdicts without mocks or fixture substitutions for model generation.
"""
from __future__ import annotations

import asyncio
import json
import os
import shutil
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from content_pipeline.cli import execute
from content_pipeline.contact_config import load_company_contact
from content_pipeline.schemas import Plan, Slot
from content_pipeline.marketing_planner import OFFICIAL_COMMERCIAL_SERVICES


SERVICES_CONFIG = [
    {
        "slot_id": "service_1_audit",
        "service": "blockchain-security-audits",
        "focus": "smart contract invariant verification and post-audit deployment drift",
        "official_url": "https://sanadsquad.com/services/blockchain-security-audits/",
    },
    {
        "slot_id": "service_2_pentest",
        "service": "penetration-testing",
        "focus": "API security and CI/CD build pipeline infrastructure attack surface",
        "official_url": "https://sanadsquad.com/services/penetration-testing/",
    },
    {
        "slot_id": "service_3_tooling",
        "service": "agentic-security-tooling",
        "focus": "custom AI security tools and automated PR reviewer detectors",
        "official_url": "https://sanadsquad.com/services/ai-security-tooling/",
    },
    {
        "slot_id": "service_4_payments",
        "service": "agentic-payments",
        "focus": "x402 versus MPP payment settlement mechanics and facilitator trust",
        "official_url": "https://sanadsquad.com/services/agentic-payments/",
    },
    {
        "slot_id": "service_5_consulting",
        "service": "security-consulting",
        "focus": "security consulting and pre-implementation protocol architecture design",
        "official_url": "https://sanadsquad.com/services/consulting/",
    },
]


async def run_five_service_qualification(output_subdir: str = "v3_five_service_knowledge_integration") -> dict:
    output_base = ROOT / "output" / output_subdir
    if output_base.exists():
        shutil.rmtree(output_base)

    contact_cfg = load_company_contact()
    print("\n" + "=" * 76)
    print("A. FIVE-SERVICE MARKETING REAL-MODEL QUALIFICATION (qwen3.5:4b)")
    print("=" * 76)
    print(f"Output: {output_base}")
    print(f"Contact status: {contact_cfg.status} (approved={contact_cfg.approved})")

    slots = [
        Slot(
            id=cfg["slot_id"],
            type="marketing-post",
            focus=cfg["focus"],
            service_line=cfg["service"],
        )
        for cfg in SERVICES_CONFIG
    ]
    plan = Plan(slots=slots)

    start_time = time.monotonic()
    summary = await execute(
        plan=plan,
        output=output_base,
        mode="v3",
        research_mode="fixture",
        authorization_mode="publication_eligible",
    )
    elapsed = time.monotonic() - start_time

    print(f"\nFive-service run finished in {elapsed:.2f}s")
    print(f"Shipped: {summary.get('shipped', 0)} / {len(slots)}")
    print(f"Dropped: {summary.get('dropped', 0)}")
    print(f"Failed: {summary.get('failed', 0)}")

    csv_file = output_base / "posts.csv"
    if csv_file.exists():
        print("\n--- Exported posts.csv ---")
        print(csv_file.read_text(encoding="utf-8"))

    return summary


async def run_six_slot_weekly() -> dict:
    output_base = ROOT / "output" / "v3_weekly_closure"
    if output_base.exists():
        shutil.rmtree(output_base)

    print("\n" + "=" * 76)
    print("B. SIX-SLOT WEEKLY REAL-MODEL QUALIFICATION (3 tech threads, 3 marketing)")
    print("=" * 76)
    print(f"Output: {output_base}")

    slots = [
        Slot(id="thread_1", type="tech-thread", focus="reentrancy"),
        Slot(id="post_1", type="marketing-post", focus=None),
        Slot(id="thread_2", type="tech-thread", focus="access control"),
        Slot(id="post_2", type="marketing-post", focus=None),
        Slot(id="thread_3", type="tech-thread", focus="oracle manipulation"),
        Slot(id="post_3", type="marketing-post", focus=None),
    ]
    plan = Plan(slots=slots)

    start_time = time.monotonic()
    summary = await execute(
        plan=plan,
        output=output_base,
        mode="v3",
        research_mode="fixture",
        authorization_mode="publication_eligible",
    )
    elapsed = time.monotonic() - start_time

    print(f"\nSix-slot weekly run finished in {elapsed:.2f}s")
    print(f"Shipped: {summary.get('shipped', 0)} / {len(slots)}")
    print(f"Dropped: {summary.get('dropped', 0)}")
    print(f"Failed: {summary.get('failed', 0)}")

    csv_file = output_base / "posts.csv"
    if csv_file.exists():
        print("\n--- Exported posts.csv ---")
        print(csv_file.read_text(encoding="utf-8"))

    return summary


async def main():
    target = sys.argv[1] if len(sys.argv) > 1 else "all"
    if target in ("all", "five-service", "5"):
        await run_five_service_qualification()
    if target in ("all", "weekly", "6"):
        await run_six_slot_weekly()


if __name__ == "__main__":
    asyncio.run(main())
