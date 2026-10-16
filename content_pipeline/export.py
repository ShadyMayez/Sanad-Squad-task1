from __future__ import annotations

import csv
import json
from pathlib import Path
from .schemas import AcceptedRecord, ClaimsRecord, EvidenceProvenanceRecord, FailureRecord, GroundingSummary, Plan, ResearchRecord, ReviewRecord, SemanticRecord, SlotResult, Summary, ValidationRecord
from .text_spans import source_span_options
from .provenance import context_errors


def dump_json(path: Path, value):
    path.write_text(json.dumps(value, indent=2, ensure_ascii=False) + "\n")


def export_run(output: Path, plan: Plan, results: list[SlotResult], elapsed: float, model_name: str, peak_active: int) -> dict:
    if output.exists():
        raise FileExistsError(f"Output already exists: {output}")
    by_id = {r.slot.id: r for r in results}
    ordered = [by_id[s.id] for s in plan.slots]
    for r in ordered:
        if r.status != "accepted":
            continue
        final_claims = r.atomic_claims[-1] if r.atomic_claims else []
        final_verdicts = r.semantic_reports[-1].verdicts if r.semantic_reports else []
        source_quotes = {e.id: e.source_quote or "" for e in r.evidence}
        evidence_by_id = {e.id: e for e in r.evidence}
        allowed_spans = {f"{e.id}#{index}": (e.id, span)
            for e in r.evidence for index, span in enumerate(source_span_options(e.source_quote or ""))}
        claim_by_id = {c.id: c for c in final_claims}
        grounded = (len(claim_by_id) == len(final_claims)
            and {v.claim_id for v in final_verdicts} == set(claim_by_id)
            and all(v.verdict == "SUPPORTED" and v.supporting_spans and v.supporting_span_ids
                and len(v.supporting_spans) == len(v.supporting_span_ids)
                and all(span.evidence_id in claim_by_id[v.claim_id].candidate_evidence_ids
                    and span.quote in source_quotes.get(span.evidence_id, "")
                    for span in v.supporting_spans)
                and all(allowed_spans.get(option_id) == (span.evidence_id, span.quote)
                    for option_id, span in zip(v.supporting_span_ids, v.supporting_spans))
                and (not v.context_windows or all(w.evidence_id in evidence_by_id
                    and not context_errors(w, evidence_by_id[w.evidence_id]) for w in v.context_windows))
                and (not v.context_windows or all(any(w.evidence_id == span.evidence_id and span.quote in w.text
                    for w in v.context_windows) for span in v.supporting_spans))
                and (not v.context_windows or (v.initial_pass is not None and v.initial_pass.verdict == "SUPPORTED"
                    and v.skeptical_pass is not None and v.skeptical_pass.verdict == "SUPPORTED"
                    and v.proposed_supporting_spans == v.supporting_spans))
                for v in final_verdicts))
        if (not r.drafts or not r.reviews or not r.reviews[-1].approved or not r.validations or r.validations[-1]
                or not final_claims or len(final_claims) != len(final_verdicts)
                or not grounded
                or r.provenance_errors or not r.visual_spec or not r.visual_spec.strip()):
            raise ValueError(f"Accepted slot {r.slot.id} failed final grounding/approval/export gate")
    output.mkdir(parents=True)
    (output / "drafts").mkdir()
    (output / "visual_specs").mkdir()
    dump_json(output / "resolved_plan.json", plan.model_dump())
    dump_json(output / "research_log.json", [ResearchRecord.model_validate({"slot_id": r.slot.id, "topic": r.topic, "source_ids": r.source_ids,
        "evidence": [e.model_dump() for e in r.evidence], "status": r.status,
        "reason": r.reason}).model_dump() for r in ordered])
    for r in ordered:
        for attempt, draft in enumerate(r.drafts, 1):
            dump_json(output / "drafts" / f"{r.slot.id}-attempt-{attempt}.json", draft.model_dump())
    dump_json(output / "validation_report.json", [ValidationRecord(slot_id=r.slot.id, attempts=r.validations).model_dump() for r in ordered])
    dump_json(output / "review_report.json", [ReviewRecord(slot_id=r.slot.id, attempts=r.reviews).model_dump() for r in ordered])
    dump_json(output / "claims.json", [ClaimsRecord(slot_id=r.slot.id, attempts=r.atomic_claims).model_dump() for r in ordered])
    dump_json(output / "evidence_provenance.json", [EvidenceProvenanceRecord(slot_id=r.slot.id, errors=r.provenance_errors,
        evidence=r.evidence).model_dump() for r in ordered])
    dump_json(output / "semantic_verification.json", [SemanticRecord(slot_id=r.slot.id, attempts=r.semantic_reports,
        latencies_seconds=r.verification_latencies_seconds).model_dump() for r in ordered])
    verdicts = [v for r in ordered for report in r.semantic_reports for v in report.verdicts]
    dump_json(output / "grounding_summary.json", GroundingSummary(slots=len(ordered), atomic_claims_evaluated=len(verdicts),
        verdict_counts={label: sum(v.verdict == label for v in verdicts) for label in
            ("SUPPORTED", "CONTRADICTED", "INSUFFICIENT_EVIDENCE", "AMBIGUOUS", "VERIFICATION_ERROR")},
        verification_latency_seconds=round(sum(sum(r.verification_latencies_seconds) for r in ordered), 3),
        accepted_claims=sum(len(r.atomic_claims[-1]) for r in ordered if r.status == "accepted")).model_dump())
    accepted = []
    for r in ordered:
        if r.status != "accepted":
            continue
        spec_path = f"visual_specs/{r.slot.id}.md"
        (output / spec_path).write_text(r.visual_spec or "")
        accepted.append(AcceptedRecord.model_validate({**r.model_dump(), "image_spec_reference": f"spec:{spec_path}"}).model_dump(exclude={"visual_spec"}))
    dump_json(output / "accepted_content.json", accepted)
    failures = [FailureRecord(slot_id=r.slot.id, status=r.status, reason=r.reason).model_dump() for r in ordered if r.status != "accepted"]
    dump_json(output / "failures.json", failures)
    with (output / "posts.csv").open("w", newline="") as file:
        writer = csv.writer(file)
        writer.writerow(["Post Text", "Image"])
        for r in ordered:
            if r.status != "accepted":
                continue
            tweets = r.drafts[-1].tweets
            text = "\n\n".join(f"{i}/{len(tweets)} {tweet}" for i, tweet in enumerate(tweets, 1)) if len(tweets) > 1 else tweets[0]
            writer.writerow([text, f"spec:visual_specs/{r.slot.id}.md"])
    prompt_values = [r.prompt_tokens for r in ordered]
    completion_values = [r.completion_tokens for r in ordered]
    summary = {
        "model": model_name,
        "planned": len(plan.slots),
        "shipped": sum(r.status == "accepted" for r in ordered),
        "dropped": sum(r.status == "dropped" for r in ordered),
        "failed": sum(r.status == "failed" for r in ordered),
        "reasons": failures,
        "elapsed_seconds": round(elapsed, 3),
        "prompt_tokens_recorded": sum(x for x in prompt_values if x is not None) if any(x is not None for x in prompt_values) else None,
        "completion_tokens_recorded": sum(x for x in completion_values if x is not None) if any(x is not None for x in completion_values) else None,
        "usage_complete": all(r.prompt_tokens is not None and r.completion_tokens is not None and r.usage_measurements_complete for r in ordered),
        "peak_simultaneous_ollama_calls": peak_active,
        "external_model_api_charges_usd": 0.0,
        "local_inference_cost": "Electricity and hardware excluded; not measured",
    }
    summary = Summary.model_validate(summary).model_dump()
    dump_json(output / "summary.json", summary)
    return summary

