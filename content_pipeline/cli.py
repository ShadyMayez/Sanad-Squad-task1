from __future__ import annotations

import argparse
import asyncio
import json
import os
import sys
import time
from datetime import datetime
from pathlib import Path
from .config import ROOT, load_brand, load_kb, load_plan, load_registry, settings
from .export import export_run
from .graph import build_week_graph
from .llm import LocalModel
from .schemas import Plan, Slot
from .proposition_catalog import load_catalog
from .business_policy import load_business_policy


def default_output(base: str) -> Path:
    return Path(base) / datetime.now().strftime("run-%Y%m%d-%H%M%S-%f")


async def execute(
    plan: Plan,
    output: Path,
    model=None,
    mode: str | None = None,
    policy: str | None = None,
    authorization_mode: str = "publication_eligible",
    research_mode: str | None = None,
) -> dict:
    mode = mode or os.getenv("SANADSQUAD_MODE", "evidence_first_v2")
    research_mode = research_mode or os.getenv("SANADSQUAD_RESEARCH_MODE", "fixture")
    if output.exists():
        raise FileExistsError(f"Output already exists: {output}")
    brand_text, brand_rules = load_brand()
    kb = load_kb()
    registry = load_registry()
    unknown = [s.type for s in plan.slots if s.type not in registry.types]
    if unknown:
        raise ValueError(f"Unsupported content type(s): {unknown}")
    cfg = settings()
    model = model or LocalModel(cfg["model"], cfg["base_url"], cfg["max_concurrency"], cfg["timeout"], cfg["transport_retries"])

    catalog = None
    business_policy = None
    if mode in ("evidence_first_v2", "evidence_first_v3", "v3"):
        catalog = load_catalog(ROOT / "knowledge" / "evidence_first_v2" / "catalog.json")
        policy_source = policy or (ROOT / "knowledge" / "evidence_first_v2" / "policies" / "security_audit_firm.json")
        business_policy = load_business_policy(policy_source)

    from .research import ResearchService, FixtureResearchProvider, LiveResearchProvider, load_sources_config
    sources_cfg = load_sources_config()
    if research_mode == "live":
        prov = LiveResearchProvider(sources_cfg)
        if not prov.is_available():
            raise RuntimeError("Live research requested but web search API is not configured or available.")
    else:
        prov = FixtureResearchProvider(sources_cfg)
    res_service = ResearchService(config=sources_cfg, provider=prov)

    app, _ = build_week_graph(
        model,
        kb,
        registry,
        brand_text,
        brand_rules,
        mode=mode,
        catalog=catalog,
        business_policy=business_policy,
        authorization_mode=authorization_mode,
        research_service=res_service,
    )
    started = time.monotonic()
    state = await app.ainvoke({
        "plan": plan,
        "results": [],
        "authorization_mode": authorization_mode,
        "research_mode": research_mode,
    })
    summary = export_run(output, plan, state["results"], time.monotonic() - started, cfg["model"], model.peak_active, mode=mode)
    print(json.dumps(summary, indent=2))
    return summary


def week_main(argv=None) -> int:
    parser = argparse.ArgumentParser(description="Generate one week of grounded X content")
    parser.add_argument("--plan", type=Path, default=ROOT / "plan.json")
    parser.add_argument("--output", type=Path)
    parser.add_argument("--set", action="append", default=[], metavar="SLOT_ID=FOCUS")
    parser.add_argument("--mode", choices=["legacy", "evidence_first_v2", "v3", "evidence_first_v3"], default=os.getenv("SANADSQUAD_MODE", "evidence_first_v2"))
    parser.add_argument("--research-mode", choices=["fixture", "live"], default=os.getenv("SANADSQUAD_RESEARCH_MODE", "fixture"))
    parser.add_argument("--policy", help="Business policy profile name (e.g. security_audit_firm) or JSON path")
    parser.add_argument(
        "--authorization-mode",
        choices=["publication_eligible", "pilot_evaluation"],
        default="publication_eligible",
        help="Authorization clearance mode (default: publication_eligible)",
    )
    args = parser.parse_args(argv)
    try:
        registry = load_registry()
        plan = load_plan(args.plan, registry)
        slot_map = {s.id: s for s in plan.slots}
        for assignment in args.set:
            if "=" not in assignment:
                raise ValueError(f"Invalid --set {assignment!r}; expected SLOT_ID=FOCUS")
            id, focus = assignment.split("=", 1)
            if id not in slot_map:
                raise ValueError(f"Unknown slot ID {id!r}; valid IDs: {list(slot_map)}")
            if not focus.strip():
                raise ValueError("Override focus cannot be empty")
            slot_map[id].focus = focus.strip()
        exec_kwargs = {}
        if args.mode:
            exec_kwargs["mode"] = args.mode
            if args.policy:
                exec_kwargs["policy"] = args.policy
            if args.authorization_mode:
                exec_kwargs["authorization_mode"] = args.authorization_mode
            if getattr(args, "research_mode", None):
                exec_kwargs["research_mode"] = args.research_mode
        summary = asyncio.run(
            execute(
                plan,
                args.output or default_output(settings()["output_base"]),
                **exec_kwargs,
            )
        )
        return 0 if summary["failed"] == 0 and summary["shipped"] > 0 else 1
    except (ValueError, OSError) as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 2


def piece_main(argv=None) -> int:
    parser = argparse.ArgumentParser(description="Generate and review one grounded X content piece")
    parser.add_argument("--type", required=True, help="Registered content type")
    parser.add_argument("--topic", required=True)
    parser.add_argument("--output", type=Path)
    parser.add_argument("--mode", choices=["legacy", "evidence_first_v2", "v3", "evidence_first_v3"], default=os.getenv("SANADSQUAD_MODE", "evidence_first_v2"))
    parser.add_argument("--research-mode", choices=["fixture", "live"], default=os.getenv("SANADSQUAD_RESEARCH_MODE", "fixture"))
    parser.add_argument("--policy", help="Business policy profile name (e.g. security_audit_firm) or JSON path")
    parser.add_argument(
        "--authorization-mode",
        choices=["publication_eligible", "pilot_evaluation"],
        default="publication_eligible",
        help="Authorization clearance mode (default: publication_eligible)",
    )
    args = parser.parse_args(argv)
    try:
        registry = load_registry()
        if args.type not in registry.types:
            raise ValueError(f"Unsupported content type {args.type!r}; supported: {list(registry.types)}")
        plan = Plan(slots=[Slot(id="piece_1", type=args.type, focus=args.topic)])
        exec_kwargs = {}
        if args.mode:
            exec_kwargs["mode"] = args.mode
            if args.policy:
                exec_kwargs["policy"] = args.policy
            if args.authorization_mode:
                exec_kwargs["authorization_mode"] = args.authorization_mode
            if getattr(args, "research_mode", None):
                exec_kwargs["research_mode"] = args.research_mode
        summary = asyncio.run(
            execute(
                plan,
                args.output or default_output(settings()["output_base"]),
                **exec_kwargs,
            )
        )
        return 0 if summary["shipped"] == 1 else 1
    except (ValueError, OSError) as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(week_main())
