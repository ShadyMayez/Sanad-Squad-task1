from __future__ import annotations

import json
import os
from pathlib import Path
from pydantic import ValidationError
from dotenv import load_dotenv
from .schemas import BrandRules, KnowledgeBase, Plan, Registry

ROOT = Path(__file__).resolve().parent.parent
load_dotenv(ROOT / ".env")


def settings() -> dict:
    return {
        "model": os.getenv("OLLAMA_MODEL", "qwen3.5:4b"),
        "base_url": os.getenv("OLLAMA_BASE_URL", "http://127.0.0.1:11434"),
        "max_concurrency": max(1, int(os.getenv("OLLAMA_MAX_CONCURRENCY", "1"))),
        "timeout": max(1, int(os.getenv("OLLAMA_TIMEOUT_SECONDS", "180"))),
        "transport_retries": max(0, int(os.getenv("OLLAMA_TRANSPORT_RETRIES", "1"))),
        "output_base": os.getenv("OUTPUT_BASE", "output"),
    }


def read_json(path: Path, schema):
    try:
        return schema.model_validate_json(path.read_text())
    except (OSError, ValidationError, ValueError) as exc:
        raise ValueError(f"Invalid {path}: {exc}") from exc


def load_plan(path: Path, registry: Registry, weekly: bool = True) -> Plan:
    plan = read_json(path, Plan)
    unknown = [s.type for s in plan.slots if s.type not in registry.types]
    if unknown:
        raise ValueError(f"Unsupported content types: {unknown}; supported: {list(registry.types)}")
    if weekly and len(plan.slots) != 6:
        raise ValueError("Weekly plan requires exactly six slots")
    if weekly and all(s.type in {"tech-thread", "marketing-post"} for s in plan.slots) and (sum(s.type == "tech-thread" for s in plan.slots) != 3 or sum(s.type == "marketing-post" for s in plan.slots) != 3):
        raise ValueError("Assignment plan requires three tech-thread and three marketing-post slots")
    return plan


def load_brand(path: Path = ROOT / "brand-voice.md") -> tuple[str, BrandRules]:
    try:
        text = path.read_text()
        marker = "```json"
        block = text.split(marker, 1)[1].split("```", 1)[0]
        return text, BrandRules.model_validate(json.loads(block))
    except (OSError, IndexError, ValueError, ValidationError) as exc:
        raise ValueError(f"Invalid brand rules in {path}: {exc}") from exc


def load_registry() -> Registry:
    return read_json(ROOT / "content-types.json", Registry)


def load_kb() -> KnowledgeBase:
    # Shape errors are global input errors. Source availability and integrity
    # belong to the selected slot, so one broken snapshot cannot stop a week.
    return read_json(ROOT / "kb.json", KnowledgeBase)


def load_sources(path: Path = ROOT / "sources.json"):
    from .research.config import load_sources_config
    return load_sources_config(path)


def load_writing_rules(path: Path = ROOT / "writing-quality-rules.json") -> dict:
    from .writing_quality import load_writing_quality_rules
    return load_writing_quality_rules(path)


def load_marketing_rules(path: Path = ROOT / "marketing-rules.md") -> tuple[str, Any]:
    from .marketing_policy import load_marketing_policy
    text = path.read_text(encoding="utf-8") if path.exists() else ""
    return text, load_marketing_policy(path)
