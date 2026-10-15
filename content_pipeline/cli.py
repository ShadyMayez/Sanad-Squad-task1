from __future__ import annotations

import argparse
import asyncio
import json
import sys
import time
from datetime import datetime
from pathlib import Path
from .config import ROOT, load_brand, load_kb, load_plan, load_registry, settings
from .export import export_run
from .graph import build_week_graph
from .llm import LocalModel
from .schemas import Plan, Slot


def default_output(base: str) -> Path:
    return Path(base) / datetime.now().strftime("run-%Y%m%d-%H%M%S-%f")


async def execute(plan: Plan, output: Path, model=None) -> dict:
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
    app, _ = build_week_graph(model, kb, registry, brand_text, brand_rules)
    started = time.monotonic()
    state = await app.ainvoke({"plan": plan, "results": []})
    summary = export_run(output, plan, state["results"], time.monotonic() - started, cfg["model"], model.peak_active)
    print(json.dumps(summary, indent=2))
    return summary


def week_main(argv=None) -> int:
    parser = argparse.ArgumentParser(description="Generate one week of grounded X content")
    parser.add_argument("--plan", type=Path, default=ROOT / "plan.json")
    parser.add_argument("--output", type=Path)
    parser.add_argument("--set", action="append", default=[], metavar="SLOT_ID=FOCUS")
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
        summary = asyncio.run(execute(plan, args.output or default_output(settings()["output_base"])))
        return 0 if summary["failed"] == 0 and summary["shipped"] > 0 else 1
    except (ValueError, OSError) as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 2


def piece_main(argv=None) -> int:
    parser = argparse.ArgumentParser(description="Generate and review one grounded X content piece")
    parser.add_argument("--type", required=True, help="Registered content type")
    parser.add_argument("--topic", required=True)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args(argv)
    try:
        registry = load_registry()
        if args.type not in registry.types:
            raise ValueError(f"Unsupported content type {args.type!r}; supported: {list(registry.types)}")
        plan = Plan(slots=[Slot(id="piece_1", type=args.type, focus=args.topic)])
        summary = asyncio.run(execute(plan, args.output or default_output(settings()["output_base"])))
        return 0 if summary["shipped"] == 1 else 1
    except (ValueError, OSError) as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 2

