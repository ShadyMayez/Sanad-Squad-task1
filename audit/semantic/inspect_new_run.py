"""Read-only inspection of a completed semantic-gated run."""
from __future__ import annotations

import argparse
import csv
import json
from collections import Counter
from pathlib import Path
from pydantic import TypeAdapter

from content_pipeline.provenance import context_errors, evidence_errors
from content_pipeline.text_spans import source_span_options
from content_pipeline.schemas import (AcceptedRecord, ClaimsRecord, Evidence, EvidenceContext,
    EvidenceProvenanceRecord, FailureRecord, GroundingSummary, Plan,
    ResearchRecord, ReviewRecord, SemanticRecord, Summary, ValidationRecord)


def inspect(folder: Path) -> dict:
    def data(name: str):
        return json.loads((folder / name).read_text())

    contracts = {"resolved_plan.json": Plan, "research_log.json": list[ResearchRecord],
        "claims.json": list[ClaimsRecord], "evidence_provenance.json": list[EvidenceProvenanceRecord],
        "semantic_verification.json": list[SemanticRecord], "grounding_summary.json": GroundingSummary,
        "review_report.json": list[ReviewRecord], "validation_report.json": list[ValidationRecord],
        "accepted_content.json": list[AcceptedRecord], "failures.json": list[FailureRecord],
        "summary.json": Summary}
    for name, contract in contracts.items():
        TypeAdapter(contract).validate_python(data(name))
    plan = data("resolved_plan.json")["slots"]
    research = data("research_log.json")
    claims = data("claims.json")
    semantic = data("semantic_verification.json")
    review = data("review_report.json")
    validation = data("validation_report.json")
    accepted = data("accepted_content.json")
    failures = data("failures.json")
    summary = data("summary.json")
    with (folder / "posts.csv").open(newline="") as file:
        csv_rows = list(csv.reader(file))
    assert csv_rows[0] == ["Post Text", "Image"]
    by_id = {row["slot_id"]: row for row in research}
    claims_by = {row["slot_id"]: row for row in claims}
    semantic_by = {row["slot_id"]: row for row in semantic}
    review_by = {row["slot_id"]: row for row in review}
    validation_by = {row["slot_id"]: row for row in validation}
    accepted_by = {row["slot"]["id"]: row for row in accepted}
    slots = []
    for slot in plan:
        id = slot["id"]
        row = by_id[id]
        evidence = [Evidence.model_validate(e) for e in row["evidence"]]
        provenance = [error for item in evidence for error in evidence_errors(item)]
        attempts = semantic_by[id]["attempts"]
        final_claims = claims_by[id]["attempts"][-1] if claims_by[id]["attempts"] else []
        final_verdicts = attempts[-1]["verdicts"] if attempts else []
        assert len(final_claims) == len(final_verdicts) if attempts else True
        evidence_by_id = {e.id: e for e in evidence}
        for attempt in attempts:
            for verdict in attempt["verdicts"]:
                for window in verdict.get("context_windows", []):
                    assert window["evidence_id"] in evidence_by_id
                    assert not context_errors(EvidenceContext.model_validate(window), evidence_by_id[window["evidence_id"]])
        statuses = Counter(v["verdict"] for attempt in attempts for v in attempt["verdicts"])
        is_accepted = id in accepted_by
        if is_accepted:
            assert not provenance and final_claims
            assert {c["id"] for c in final_claims} == {v["claim_id"] for v in final_verdicts}
            claim_by = {c["id"]: c for c in final_claims}
            quotes = {e.id: e.source_quote or "" for e in evidence}
            allowed = {f"{e.id}#{index}": (e.id, span)
                for e in evidence for index, span in enumerate(source_span_options(e.source_quote or ""))}
            assert all(v["verdict"] == "SUPPORTED" and v["supporting_spans"] and v["supporting_span_ids"]
                and len(v["supporting_spans"]) == len(v["supporting_span_ids"])
                and all(span["evidence_id"] in claim_by[v["claim_id"]]["candidate_evidence_ids"]
                    and span["quote"] in quotes.get(span["evidence_id"], "")
                    for span in v["supporting_spans"])
                and all(allowed.get(option_id) == (span["evidence_id"], span["quote"])
                    for option_id, span in zip(v["supporting_span_ids"], v["supporting_spans"]))
                for v in final_verdicts)
            assert not validation_by[id]["attempts"][-1]
            assert review_by[id]["attempts"][-1]["approved"]
            assert len(accepted_by[id]["drafts"][-1]["tweets"]) in (range(5, 11) if slot["type"] == "tech-thread" else (1,))
            spec = accepted_by[id]["image_spec_reference"]
            assert spec.startswith("spec:visual_specs/") and (folder / spec[5:]).is_file()
            assert any(csv_row[1] == spec for csv_row in csv_rows[1:])
        slots.append({"id": id, "type": slot["type"], "topic": row["topic"], "status": row["status"],
            "source_ids": row["source_ids"], "provenance_errors": provenance,
            "draft_count": len(claims_by[id]["attempts"]), "review_count": len(review_by[id]["attempts"]),
            "final_atomic_claims": len(final_claims), "verdict_counts": dict(statuses),
            "final_verdicts": final_verdicts,
            "final_tweets": accepted_by[id]["drafts"][-1]["tweets"] if is_accepted else
                json.loads((folder / "drafts" / f"{id}-attempt-{len(claims_by[id]['attempts'])}.json").read_text())["tweets"] if claims_by[id]["attempts"] else [],
            "revisions": max(0, len(claims_by[id]["attempts"]) - 1),
            "verification_disagreements": sum(1 for attempt in attempts for verdict in attempt["verdicts"]
                if verdict.get("initial_pass") and verdict.get("skeptical_pass") and
                verdict["initial_pass"]["verdict"] != verdict["skeptical_pass"]["verdict"]),
            "context_decisions": sum(1 for attempt in attempts for verdict in attempt["verdicts"] if verdict.get("context_windows")),
            "visual_spec": accepted_by[id]["image_spec_reference"] if is_accepted else None,
            "reason": next((f["reason"] for f in failures if f["slot_id"] == id), None)})
    assert len(csv_rows) - 1 == len(accepted) == summary["shipped"]
    assert len(slots) == summary["planned"]
    assert len(failures) == summary["dropped"] + summary["failed"]
    return {"run": str(folder.resolve()), "summary": summary, "slots": slots,
        "csv_rows": len(csv_rows) - 1, "all_accepted_claims_pinned": all(not s["provenance_errors"] and all(v["verdict"] == "SUPPORTED" and v["supporting_spans"] for v in s["final_verdicts"]) for s in slots if s["status"] == "accepted")}


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("folder", type=Path)
    args = parser.parse_args()
    print(json.dumps(inspect(args.folder), indent=2))
