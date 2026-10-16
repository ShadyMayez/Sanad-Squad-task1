"""Standalone qualification script for SWC-113 marketing post and SCWE-028 oracle thread.
Runs real local Ollama inference under Evidence-First V2 with full semantic conformance checks.
"""
import asyncio
import json
import time
from pathlib import Path

from content_pipeline.config import ROOT, load_brand, load_kb, load_registry, settings
from content_pipeline.export import export_run
from content_pipeline.graph import build_week_graph
from content_pipeline.llm import LocalModel
from content_pipeline.schemas import Plan, Slot
from content_pipeline.proposition_catalog import load_catalog
from content_pipeline.business_policy import load_business_policy


async def run_standalone_slot(slot: Slot, out_dir: Path, topic_focus: str):
    print(f"\n========================================================")
    print(f"Running standalone qualification for {slot.id} ({slot.type}) - Focus: {topic_focus}")
    print(f"Output directory: {out_dir}")
    print(f"========================================================")

    if out_dir.exists():
        import shutil
        shutil.rmtree(out_dir)

    brand_text, brand_rules = load_brand()
    kb = load_kb()
    registry = load_registry()
    cfg = settings()
    model = LocalModel(cfg["model"], cfg["base_url"], cfg["max_concurrency"], cfg["timeout"], cfg["transport_retries"])
    catalog = load_catalog(ROOT / "knowledge" / "evidence_first_v2" / "catalog.json")
    policy = load_business_policy(ROOT / "knowledge" / "evidence_first_v2" / "policies" / "security_audit_firm.json")

    app, _ = build_week_graph(
        model,
        kb,
        registry,
        brand_text,
        brand_rules,
        mode="evidence_first_v2",
        catalog=catalog,
        business_policy=policy,
        authorization_mode="publication_eligible",
    )

    plan = Plan(slots=[slot])
    started = time.monotonic()
    state = await app.ainvoke({
        "plan": plan,
        "results": [],
        "authorization_mode": "publication_eligible",
    })
    elapsed = time.monotonic() - started

    summary = export_run(out_dir, plan, state["results"], elapsed, cfg["model"], model.peak_active, mode="evidence_first_v2")
    res = state["results"][0]

    print("\n--- Result Summary ---")
    print(f"Status: {res.status}")
    print(f"Wall time: {elapsed:.3f} s")
    print(f"Revisions: {len(res.drafts) - 1}")
    if res.drafts:
        final_draft = res.drafts[-1]
        print(f"Tweets count: {len(final_draft.tweets)}")
        for idx, tw in enumerate(final_draft.tweets, 1):
            print(f"  Tweet {idx} ({len(tw)} chars): {tw}")
    if res.conformance_report:
        print(f"Conformance all_conforming: {res.conformance_report.get('all_conforming')}")
        for u in res.conformance_report.get("results", []):
            print(f"  Unit {u.get('unit_id')}: verdict={u.get('verdict')} passed={u.get('passed')}")
            print(f"    reason: {u.get('reason')}")
    if res.reviews:
        final_rev = res.reviews[-1]
        print(f"Reviewer approved: {final_rev.approved}")
        print(f"Reviewer assessment: {final_rev.grounding_assessment}")

    return res, summary


async def main():
    # 1. SWC-113 standalone marketing post
    slot_swc113 = Slot(id="post_3_qual", type="marketing-post", focus="failed call")
    out_swc113 = ROOT / "output" / "qual-grounded-swc113"
    res113, sum113 = await run_standalone_slot(slot_swc113, out_swc113, "failed call")

    # 2. SCWE-028 standalone oracle thread
    slot_oracle = Slot(id="thread_3_qual", type="tech-thread", focus="oracle manipulation")
    out_oracle = ROOT / "output" / "qual-grounded-oracle"
    res_oracle, sum_oracle = await run_standalone_slot(slot_oracle, out_oracle, "oracle manipulation")

    print("\n========================================================")
    print("STANDALONE QUALIFICATIONS COMPLETE")
    print(f"SWC-113: status={res113.status}, shipped={sum113['shipped']}/{sum113['planned']}")
    print(f"Oracle:  status={res_oracle.status}, shipped={sum_oracle['shipped']}/{sum_oracle['planned']}")
    print("========================================================")


if __name__ == "__main__":
    asyncio.run(main())
