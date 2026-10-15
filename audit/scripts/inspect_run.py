"""Independent read-only checks for a SanadSquad run folder."""
from __future__ import annotations

import csv
import hashlib
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from content_pipeline.config import load_brand, load_kb, load_registry  # noqa: E402
from content_pipeline.schemas import (  # noqa: E402
    AcceptedRecord, Draft, FailureRecord, Plan, ResearchRecord, ReviewRecord,
    Summary, ValidationRecord,
)
from content_pipeline.skills import EvidenceLookup  # noqa: E402
from content_pipeline.validation import validate_draft  # noqa: E402


def read(path: Path):
    return json.loads(path.read_text())


def inspect(folder: Path) -> dict:
    required = ["resolved_plan.json", "research_log.json", "validation_report.json",
                "review_report.json", "accepted_content.json", "failures.json",
                "summary.json", "posts.csv"]
    missing = [name for name in required if not (folder / name).is_file()]
    if missing:
        raise AssertionError(f"Missing artifacts: {missing}")

    plan = Plan.model_validate(read(folder / "resolved_plan.json"))
    research = [ResearchRecord.model_validate(x) for x in read(folder / "research_log.json")]
    validation = [ValidationRecord.model_validate(x) for x in read(folder / "validation_report.json")]
    reviews = [ReviewRecord.model_validate(x) for x in read(folder / "review_report.json")]
    accepted = [AcceptedRecord.model_validate(x) for x in read(folder / "accepted_content.json")]
    failures = [FailureRecord.model_validate(x) for x in read(folder / "failures.json")]
    summary = Summary.model_validate(read(folder / "summary.json"))
    brand_text, brand = load_brand()
    kb = load_kb()
    registry = load_registry()
    lookup = EvidenceLookup(kb)
    assert brand_text and summary.planned == len(plan.slots)
    assert summary.shipped == len(accepted)
    assert summary.dropped + summary.failed == len(failures)
    ids = [slot.id for slot in plan.slots]
    assert [r.slot_id for r in research] == ids
    assert [r.slot_id for r in validation] == ids
    assert [r.slot_id for r in reviews] == ids
    assert [r.slot.id for r in accepted] == [id for id in ids if id in {a.slot.id for a in accepted}]

    with (folder / "posts.csv").open(newline="") as file:
        rows = list(csv.reader(file))
    assert rows[0] == ["Post Text", "Image"] and len(rows) == len(accepted) + 1

    slots = []
    for slot in plan.slots:
        rr = research[ids.index(slot.id)]
        vr = validation[ids.index(slot.id)]
        rev = reviews[ids.index(slot.id)]
        ar = next((x for x in accepted if x.slot.id == slot.id), None)
        draft_paths = sorted((folder / "drafts").glob(f"{slot.id}-attempt-*.json"))
        drafts = [Draft.model_validate(read(path)) for path in draft_paths]
        assert len(drafts) <= 2
        assert len(vr.attempts) == len(rev.attempts)
        assert len(vr.attempts) <= len(drafts)
        assert all(item.id in {e.id for v in kb.vulnerabilities for e in v.evidence} for item in rr.evidence)
        if ar:
            assert len(drafts) == len(rev.attempts) == len(ar.drafts)
            assert not vr.attempts[-1] and rev.attempts[-1].approved
            assert ar.drafts[-1] == drafts[-1]
            assert not validate_draft(drafts[-1], registry.types[slot.type], brand, ar.evidence, lookup)
            assert (folder / ar.image_spec_reference.removeprefix("spec:")).is_file()
            row = rows[1 + accepted.index(ar)]
            assert row[1] == ar.image_spec_reference
            if len(drafts[-1].tweets) > 1:
                assert row[0].startswith(f"1/{len(drafts[-1].tweets)} ")
                assert f"\n\n{len(drafts[-1].tweets)}/{len(drafts[-1].tweets)} " in row[0]
            else:
                assert row[0] == drafts[-1].tweets[0]
            status = "accepted"
        else:
            assert slot.id in {x.slot_id for x in failures}
            status = next(x.status for x in failures if x.slot_id == slot.id)
            assert not (folder / "visual_specs" / f"{slot.id}.md").exists()
        slots.append({"id": slot.id, "type": slot.type, "focus": slot.focus,
                      "topic": rr.topic, "source_ids": rr.source_ids,
                      "status": status, "draft_count": len(drafts),
                      "content_revisions": max(0, len(drafts) - 1),
                      "review_count": len(rev.attempts),
                      "final_review_approved": rev.attempts[-1].approved if rev.attempts else None,
                      "visual_spec": bool(ar), "tweet_count": len(drafts[-1].tweets) if drafts else 0,
                      "duration_seconds": None})
    tokens_prompt = sum(x.prompt_tokens or 0 for x in accepted)
    tokens_completion = sum(x.completion_tokens or 0 for x in accepted)
    if not failures:
        assert summary.prompt_tokens_recorded == tokens_prompt
        assert summary.completion_tokens_recorded == tokens_completion
    return {"folder": str(folder), "summary": summary.model_dump(), "slots": slots,
            "csv_rows": len(rows) - 1,
            "artifact_sha256": {p.name: hashlib.sha256(p.read_bytes()).hexdigest() for p in (folder / "summary.json", folder / "posts.csv", folder / "accepted_content.json")}}


if __name__ == "__main__":
    print(json.dumps(inspect(Path(sys.argv[1])), indent=2))
