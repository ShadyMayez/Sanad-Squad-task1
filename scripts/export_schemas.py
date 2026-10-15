"""Regenerate JSON Schema files from the persisted Pydantic contracts."""
import json
from pathlib import Path
from pydantic import TypeAdapter
from content_pipeline.schemas import (
    AcceptedRecord, Draft, FailureRecord, Plan, ResearchRecord,
    ReviewRecord, Summary, ValidationRecord,
)

OUT = Path(__file__).resolve().parent.parent / "schemas"
OUT.mkdir(exist_ok=True)
contracts = {
    "resolved_plan": Plan,
    "research_log": list[ResearchRecord],
    "draft": Draft,
    "validation_report": list[ValidationRecord],
    "review_report": list[ReviewRecord],
    "accepted_content": list[AcceptedRecord],
    "failures": list[FailureRecord],
    "summary": Summary,
}
for name, contract in contracts.items():
    schema = TypeAdapter(contract).json_schema()
    (OUT / f"{name}.schema.json").write_text(json.dumps(schema, indent=2, sort_keys=True) + "\n")
