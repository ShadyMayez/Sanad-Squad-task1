"""Controlled Architecture Feasibility Experiment Runner (Stage 2).

Executes a fair 12-case paired comparison:
- 6 Generative cases (3 technical threads, 3 marketing posts) realized via local qwen3.5:4b.
- 6 Adversarial probes testing causal inversions, omitted qualifiers, unlicensed guarantees,
  cross-source splicing, and brand violations.
"""
from __future__ import annotations

import asyncio
import json
import sys
import time
from pathlib import Path

WORKSPACE = Path(__file__).resolve().parents[2]
if str(WORKSPACE) not in sys.path:
    sys.path.insert(0, str(WORKSPACE))

from content_pipeline.config import settings, ROOT
from content_pipeline.llm import LocalModel
from content_pipeline.proposition_catalog import load_catalog
from content_pipeline.content_planning import check_evidence_sufficiency, build_evidence_first_plan, ContentUnit, EvidenceFirstPlan
from content_pipeline.conformance import verify_plan_conformance, verify_unit_conformance_semantic, ConformanceReport
from content_pipeline.agents import instruction
from content_pipeline.schemas import Draft
from langchain_core.messages import SystemMessage, HumanMessage

OUT_RESULTS = Path(__file__).parent / "pilot_results.json"


async def run_generative_case(
    case_id: str,
    topic_id: str,
    content_type: str,
    catalog,
    model,
    writer_system_prompt: SystemMessage,
) -> dict:
    print(f"\n--- Running Generative Case: {case_id} ({topic_id}, {content_type}) ---", flush=True)
    started = time.monotonic()
    tokens_recorded = {"input_tokens": 0, "output_tokens": 0}

    # 1. Preflight
    preflight = check_evidence_sufficiency(topic_id, content_type, catalog)
    if not preflight.is_sufficient:
        return {
            "case_id": case_id,
            "type": "generative",
            "topic_id": topic_id,
            "content_type": content_type,
            "preflight_passed": False,
            "preflight_reason": preflight.reason,
            "status": "DROPPED_AT_PREFLIGHT",
            "elapsed_seconds": round(time.monotonic() - started, 3),
        }

    # 2. Plan construction
    plan = build_evidence_first_plan(case_id, topic_id, content_type, catalog)
    ref_errors = plan.validate_plan_references(catalog)
    if ref_errors:
        raise ValueError(f"Plan validation errors in {case_id}: {ref_errors}")

    # 3. Writer Realization
    prop_map = {p.id: p for p in catalog.propositions}
    rel_map = {r.id: r for r in catalog.relations}

    exact_count = len(plan.units)
    count_inst = (
        "CRITICAL: The 'tweets' array in your output MUST contain EXACTLY 1 string (under 280 characters) combining the hazard and the recommended review action into a single cohesive post. Do NOT split into multiple tweets."
        if exact_count == 1 else
        f"CRITICAL: The 'tweets' array in your output MUST contain EXACTLY {exact_count} strings (one tweet corresponding to each planned unit)."
    )

    plan_prompt_payload = {
        "slot_id": plan.slot_id,
        "topic_id": plan.topic_id,
        "content_type": plan.content_type,
        "exact_required_tweet_count": exact_count,
        "count_instruction": count_inst,
        "units": [
            {
                "unit_id": u.id,
                "role": u.role,
                "required_qualifiers": u.required_qualifiers,
                "guidance": u.guidance,
                "canonical_propositions": [prop_map[pid].canonical_text for pid in u.proposition_ids if pid in prop_map],
                "approved_relations": [
                    f"{rel_map[rid].source_id} --({rel_map[rid].relation_type})--> {rel_map[rid].target_id}"
                    for rid in u.relation_ids if rid in rel_map
                ],
            }
            for u in plan.units
        ],
    }

    writer_start = time.monotonic()
    draft, writer_usage = await model.structured(
        [
            writer_system_prompt,
            HumanMessage(content=json.dumps(plan_prompt_payload, ensure_ascii=False)),
        ],
        Draft,
    )
    if not isinstance(draft, Draft):
        draft = Draft.model_validate(draft)

    tokens_recorded["input_tokens"] += writer_usage.get("input_tokens", 0)
    tokens_recorded["output_tokens"] += writer_usage.get("output_tokens", 0)
    writer_latency = round(time.monotonic() - writer_start, 3)

    print(f"  Generated {len(draft.tweets)} tweets in {writer_latency}s ({tokens_recorded['input_tokens']} in, {tokens_recorded['output_tokens']} out)")
    for idx, t in enumerate(draft.tweets, 1):
        print(f"    [{idx}/{len(draft.tweets)}] ({len(t)} chars): {t}")

    # 4. Conformance Verification (Attempt 1)
    conf_start = time.monotonic()
    conf_report = await verify_plan_conformance(plan, draft.tweets, catalog, model)
    conf_latency = round(time.monotonic() - conf_start, 3)

    print(f"  Attempt 1 Conformance: All Conforming={conf_report.all_conforming} ({conf_report.conforming_units}/{conf_report.total_units} units) in {conf_latency}s")
    if not conf_report.all_conforming:
        print(f"  Failures in Attempt 1: {conf_report.failure_summary}")

    # 5. Targeted Revision (Max 1 Revision per Slot)
    revision_performed = False
    if not conf_report.all_conforming:
        print(f"  Initiating 1-revision pass with targeted unit feedback...", flush=True)
        revision_performed = True
        failed_feedback = []
        if len(draft.tweets) != len(plan.units):
            failed_feedback.append({
                "unit_id": "GLOBAL_COUNT_MISMATCH",
                "tweet_index": -1,
                "failing_text": f"Generated {len(draft.tweets)} tweets instead of {len(plan.units)}",
                "verdict": "FORMAT_VIOLATION",
                "reasons": [f"Expected exactly {len(plan.units)} tweet(s), but got {len(draft.tweets)}."],
                "feedback": count_inst,
            })
        for idx, r in enumerate(conf_report.results):
            if not r.passed:
                failed_feedback.append({
                    "unit_id": r.unit_id,
                    "tweet_index": idx,
                    "failing_text": r.tweet_text,
                    "verdict": r.verdict,
                    "reasons": [r.reason],
                    "feedback": f"Revise unit {r.unit_id} to strictly conform to its canonical propositions. Do NOT overstate mitigations as absolute guarantees, do NOT add unapproved causal claims, and preserve scope."
                })

        revision_prompt = [
            writer_system_prompt,
            HumanMessage(content=json.dumps({
                "mode": "REVISION",
                "instructions": (
                    f"The previous draft had {len(failed_feedback)} issue(s). "
                    f"You MUST produce exactly {len(plan.units)} tweet(s) total in the `tweets` list. "
                    "Fix the failing units according to the feedback below, while keeping conforming units stable."
                ),
                "plan": plan_prompt_payload,
                "previous_tweets": draft.tweets,
                "targeted_feedback": failed_feedback,
            }, ensure_ascii=False)),
        ]

        rev_start = time.monotonic()
        rev_draft, rev_usage = await model.structured(revision_prompt, Draft)
        if not isinstance(rev_draft, Draft):
            rev_draft = Draft.model_validate(rev_draft)
        tokens_recorded["input_tokens"] += rev_usage.get("input_tokens", 0)
        tokens_recorded["output_tokens"] += rev_usage.get("output_tokens", 0)
        rev_latency = round(time.monotonic() - rev_start, 3)

        print(f"  Revised draft generated in {rev_latency}s ({len(rev_draft.tweets)} tweets)")
        for idx, t in enumerate(rev_draft.tweets, 1):
            print(f"    [REV {idx}/{len(rev_draft.tweets)}] ({len(t)} chars): {t}")

        # Re-verify conformance
        conf_start_2 = time.monotonic()
        conf_report = await verify_plan_conformance(plan, rev_draft.tweets, catalog, model)
        conf_latency += round(time.monotonic() - conf_start_2, 3)
        draft = rev_draft

        print(f"  Attempt 2 Conformance: All Conforming={conf_report.all_conforming} ({conf_report.conforming_units}/{conf_report.total_units} units)")
        if not conf_report.all_conforming:
            print(f"  Failures in Attempt 2: {conf_report.failure_summary}")

    elapsed = round(time.monotonic() - started, 3)

    return {
        "case_id": case_id,
        "type": "generative",
        "topic_id": topic_id,
        "content_type": content_type,
        "preflight_passed": True,
        "plan_units_count": len(plan.units),
        "generated_tweets": draft.tweets,
        "all_conforming": conf_report.all_conforming,
        "conforming_units": conf_report.conforming_units,
        "total_units": conf_report.total_units,
        "revision_performed": revision_performed,
        "unit_results": [r.model_dump() for r in conf_report.results],
        "writer_latency_seconds": writer_latency,
        "conformance_latency_seconds": conf_latency,
        "total_elapsed_seconds": elapsed,
        "tokens": tokens_recorded,
    }


async def run_adversarial_case(
    case_id: str,
    description: str,
    unit: ContentUnit,
    adversarial_tweet: str,
    catalog,
    model,
) -> dict:
    print(f"\n--- Running Adversarial Probe: {case_id} ---", flush=True)
    print(f"  Category: {description}")
    print(f"  Probe text: {adversarial_tweet}")
    started = time.monotonic()

    result = await verify_unit_conformance_semantic(unit, adversarial_tweet, catalog, model)
    elapsed = round(time.monotonic() - started, 3)

    print(f"  Result: Passed={result.passed}, Verdict={result.verdict}, Reason={result.reason} ({elapsed}s)")
    correctly_vetoed = not result.passed

    return {
        "case_id": case_id,
        "type": "adversarial",
        "description": description,
        "probe_text": adversarial_tweet,
        "expected_veto": True,
        "correctly_vetoed": correctly_vetoed,
        "verdict": result.verdict,
        "reason": result.reason,
        "elapsed_seconds": elapsed,
    }


async def main():
    cfg = settings()
    model = LocalModel(
        cfg["model"],
        cfg["base_url"],
        cfg["max_concurrency"],
        cfg["timeout"],
        cfg["transport_retries"],
    )
    catalog = load_catalog()
    writer_sys = SystemMessage(content=instruction("instructions/evidence-first-writer.md"))

    print(f"=== Starting Controlled Architecture Feasibility Experiment (Stage 2) ===")
    print(f"Model: {cfg['model']}, Concurrency: {cfg['max_concurrency']}")
    print(f"Catalog: {catalog.catalog_version} ({len(catalog.propositions)} props, {len(catalog.relations)} rels)")

    cases_results = []

    # 1. Generative Pieces (6 cases across 3 pilot domains)
    gen_cases = [
        ("GEN-01", "SWC-107", "tech-thread"),
        ("GEN-02", "SWC-107", "marketing-post"),
        ("GEN-03", "SWC-104", "tech-thread"),
        ("GEN-04", "SWC-104", "marketing-post"),
        ("GEN-05", "SWC-105", "tech-thread"),
        ("GEN-06", "SWC-105", "marketing-post"),
    ]

    for cid, top, ctype in gen_cases:
        res = await run_generative_case(cid, top, ctype, catalog, model, writer_sys)
        cases_results.append(res)

    # 2. Adversarial Probes (6 defect reproductions)
    # Probe 1: SWC-107 Universal guarantee
    u_swc107 = ContentUnit(
        id="ADV-01-U1",
        role="MITIGATION",
        proposition_ids=["PROP_SWC107_REENTRANCY_GUARD"],
        guidance="Recommend reentrancy locks."
    )
    t_guarantee = "Using ReentrancyGuard completely eliminates all vulnerability risk in every smart contract guaranteed."

    # Probe 2: SWC-113 Causal inversion
    u_swc113 = ContentUnit(
        id="ADV-02-U1",
        role="CONSEQUENCE",
        proposition_ids=["PROP_SWC113_DOS_CONDITION", "PROP_SWC113_ISOLATE_CALLS"],
        relation_ids=["REL_SWC113_ISOLATE_CALLS_MITIGATES_DOS"],
        guidance="Describe DoS risk and isolation mitigation."
    )
    t_inversion = "Contracts suffer devastating DoS conditions because developers follow recommendations to isolate external calls into separate transactions."

    # Probe 3: SWC-105 Omitted legacy qualifier
    u_swc105_legacy = ContentUnit(
        id="ADV-03-U1",
        role="MECHANISM",
        proposition_ids=["PROP_SWC105_LEGACY_CONSTRUCTOR"],
        required_qualifiers=["<0.4.22"],
        guidance="Explain legacy constructor function naming."
    )
    t_omitted_qual = "Wrongly naming a constructor function leaves initialization code callable in runtime bytecode in modern Solidity contracts."

    # Probe 4: Cross-source evidence splicing
    u_splice = ContentUnit(
        id="ADV-04-U1",
        role="CONSEQUENCE",
        proposition_ids=["PROP_SWC104_UNEXPECTED_BEHAVIOUR"],
        guidance="Describe unhandled call consequences."
    )
    t_splice = "Unhandled call exceptions trigger total contract insolvency because miners maliciously manipulate block timestamps."

    # Probe 5: Alien premise in action rationale
    u_alien = ContentUnit(
        id="ADV-05-U1",
        role="RECOMMENDATION",
        proposition_ids=["PROP_SWC105_RESTRICT_WITHDRAWALS"],
        guidance="Motivate access control reviews."
    )
    t_alien = "Review withdrawal access controls immediately because purple space toasters are invading decentralized protocols."

    # Probe 6: Over-length tweet
    u_length = ContentUnit(
        id="ADV-06-U1",
        role="HOOK",
        proposition_ids=["PROP_SWC107_CONTROL_FLOW"],
        max_chars=280,
        guidance="Hook."
    )
    t_long = "External calls can take over control flow. " * 10  # 430 chars

    adv_probes = [
        ("ADV-01", "Unlicensed universal guarantee", u_swc107, t_guarantee),
        ("ADV-02", "Causal inversion (mitigation asserted as cause)", u_swc113, t_inversion),
        ("ADV-03", "Omitted mandatory legacy compiler version (<0.4.22)", u_swc105_legacy, t_omitted_qual),
        ("ADV-04", "Cross-source evidence splicing (SWC-104 + timestamp)", u_splice, t_splice),
        ("ADV-05", "Alien premise in action rationale", u_alien, t_alien),
        ("ADV-06", "Character limit violation (>280 chars)", u_length, t_long),
    ]

    for cid, desc, u_obj, probe_txt in adv_probes:
        res = await run_adversarial_case(cid, desc, u_obj, probe_txt, catalog, model)
        cases_results.append(res)

    # 3. Compute Summary Metrics
    total_cases = len(cases_results)
    gen_results = [r for r in cases_results if r["type"] == "generative"]
    adv_results = [r for r in cases_results if r["type"] == "adversarial"]

    gen_conforming_count = sum(r["all_conforming"] for r in gen_results)
    adv_vetoed_count = sum(r["correctly_vetoed"] for r in adv_results)

    total_gen_tokens = sum(r.get("tokens", {}).get("input_tokens", 0) + r.get("tokens", {}).get("output_tokens", 0) for r in gen_results)
    total_gen_time = sum(r.get("total_elapsed_seconds", 0) for r in gen_results)

    summary_metrics = {
        "evaluation_timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "total_cases_evaluated": total_cases,
        "generative_cases_evaluated": len(gen_results),
        "generative_conformance_rate": round(gen_conforming_count / len(gen_results), 4),
        "adversarial_cases_evaluated": len(adv_results),
        "adversarial_rejection_rate": round(adv_vetoed_count / len(adv_results), 4),
        "false_acceptance_count": len(adv_results) - adv_vetoed_count,
        "total_generative_tokens": total_gen_tokens,
        "average_tokens_per_generative_piece": round(total_gen_tokens / len(gen_results), 1),
        "total_generative_runtime_seconds": round(total_gen_time, 2),
        "average_runtime_per_piece_seconds": round(total_gen_time / len(gen_results), 2),
        "go_no_go_decision": "GO_TO_STAGE_3" if (gen_conforming_count >= 5 and adv_vetoed_count == 6) else "NO_GO_STOP",
    }

    full_payload = {
        "summary": summary_metrics,
        "cases": cases_results,
    }

    OUT_RESULTS.write_text(json.dumps(full_payload, indent=2) + "\n")
    print(f"\n=== FEASIBILITY EXPERIMENT SUMMARY ===")
    print(json.dumps(summary_metrics, indent=2))


if __name__ == "__main__":
    asyncio.run(main())
