from __future__ import annotations

import csv
import json
from pathlib import Path
from .schemas import AcceptedRecord, ClaimsRecord, EvidenceProvenanceRecord, FailureRecord, GroundingSummary, ModelSemanticDecision, Plan, ResearchRecord, ReviewRecord, SemanticRecord, SlotResult, Summary, ValidationRecord
from .text_spans import source_span_options
from .provenance import context_errors
from .relation_integrity import assess_positive, verify_sentence_relation
from .claim_extraction import extract_sentence_relations


def relation_recheck(verdict, claim, sentence_spans: list[str] | None = None) -> bool:
    """Reapply the deterministic relation veto at the last acceptance boundary."""
    if not verdict.skeptical_pass:
        return False
    try:
        decision = ModelSemanticDecision(verdict="SUPPORTED", support_option_ids=verdict.supporting_span_ids,
            reason=verdict.skeptical_pass.reason, claim_relations=verdict.skeptical_pass.claim_relations,
            evidence_relation=verdict.skeptical_pass.evidence_relation,
            relationship_verdict=verdict.skeptical_pass.relationship_verdict,
            contradiction_detected=verdict.skeptical_pass.contradiction_detected,
            uncertainty_detected=verdict.skeptical_pass.uncertainty_detected)
        spans = [span.quote for span in verdict.supporting_spans]
        if not assess_positive(decision, claim, spans).passed:
            return False
        if claim.sentence_relation:
            eval_spans = sentence_spans if sentence_spans is not None else spans
            if not verify_sentence_relation(claim.sentence_relation, eval_spans).passed:
                return False
            if not claim.sentence_relation.semantic_verdict or claim.sentence_relation.semantic_verdict != "SUPPORTED":
                return False
        return True
    except (ValueError, TypeError):
        return False


def dump_json(path: Path, value):
    path.write_text(json.dumps(value, indent=2, ensure_ascii=False) + "\n")


def export_run(output: Path, plan: Plan, results: list[SlotResult], elapsed: float, model_name: str, peak_active: int, mode: str = "evidence_first_v2") -> dict:
    if output.exists():
        raise FileExistsError(f"Output already exists: {output}")
    by_id = {r.slot.id: r for r in results}
    ordered = [by_id[s.id] for s in plan.slots]
    for r in ordered:
        if r.status != "accepted":
            continue
        if r.pipeline_mode == "evidence_first_v2":
            if r.conformance_report is None:
                raise ValueError(f"Accepted V2 slot {r.slot.id} missing mandatory ConformanceReport")
            if not r.conformance_report.get("all_conforming"):
                raise ValueError(f"Accepted V2 slot {r.slot.id} ConformanceReport has all_conforming=False")
            if not r.drafts:
                raise ValueError(f"Accepted V2 slot {r.slot.id} has no drafts")
            final_draft = r.drafts[-1]
            results = r.conformance_report.get("results", [])
            if len(results) != len(final_draft.tweets):
                raise ValueError(
                    f"Accepted V2 slot {r.slot.id} ConformanceReport unit count ({len(results)}) "
                    f"!= final draft tweet count ({len(final_draft.tweets)})"
                )
            for unit_res, tweet in zip(results, final_draft.tweets):
                if unit_res.get("verdict") != "CONFORMS" or not unit_res.get("passed"):
                    raise ValueError(
                        f"Accepted V2 slot {r.slot.id} unit {unit_res.get('unit_id')} "
                        f"verdict is {unit_res.get('verdict')} (passed={unit_res.get('passed')}), expected CONFORMS"
                    )
                if unit_res.get("tweet_text") != tweet:
                    raise ValueError(
                        f"Accepted V2 slot {r.slot.id} unit {unit_res.get('unit_id')} tweet text mismatch with final draft: "
                        f"{unit_res.get('tweet_text')!r} != {tweet!r}"
                    )
            plan_dict = getattr(r, "evidence_plan", None)
            if plan_dict is None:
                raise ValueError(f"Accepted V2 slot {r.slot.id} missing mandatory evidence_plan binding")
            if len(plan_dict.get("units", [])) != len(final_draft.tweets):
                raise ValueError(
                    f"Accepted V2 slot {r.slot.id} evidence_plan units count ({len(plan_dict.get('units', []))}) "
                    f"!= final draft tweet count ({len(final_draft.tweets)})"
                )
            # Reconstruct and strictly validate plan authority at export
            from .content_planning import EvidenceFirstPlan
            from .proposition_catalog import load_catalog
            plan_obj = EvidenceFirstPlan.model_validate(plan_dict)
            cat = load_catalog()
            plan_errors = plan_obj.validate_plan_references(
                catalog=cat,
                active_policy_version=r.business_policy_version or "1.0.0",
                authorization_mode=getattr(r, "authorization_mode", "pilot_evaluation"),
            )
            if plan_errors:
                raise ValueError(f"Accepted V2 slot {r.slot.id} evidence_plan authority validation failed: {plan_errors}")

            from .validation import validate_brand_and_platform
            from .config import load_brand, load_registry
            _, brand_rules = load_brand()
            registry = load_registry()
            spec = registry.types.get(r.slot.type)
            bp_errors = validate_brand_and_platform(final_draft.tweets, brand_rules, spec)
            if bp_errors:
                raise ValueError(f"Accepted V2 slot {r.slot.id} failed deterministic brand/platform gate: {bp_errors}")

            review_ok = bool(r.reviews and r.reviews[-1].approved)
            validation_ok = bool(r.validations and not r.validations[-1])
            prov_ok = not r.provenance_errors
            spec_ok = bool(r.visual_spec and r.visual_spec.strip())
            if not (review_ok and validation_ok and prov_ok and spec_ok):
                raise ValueError(f"Accepted slot {r.slot.id} failed final grounding/approval/export gate")
            continue
        final_claims = r.atomic_claims[-1] if r.atomic_claims else []
        final_verdicts = r.semantic_reports[-1].verdicts if r.semantic_reports else []
        source_quotes = {e.id: e.source_quote or "" for e in r.evidence}
        evidence_by_id = {e.id: e for e in r.evidence}
        allowed_spans = {f"{e.id}#{index}": (e.id, span)
            for e in r.evidence for index, span in enumerate(source_span_options(e.source_quote or ""))}
        claim_by_id = {c.id: c for c in final_claims}
        relations = extract_sentence_relations(r.drafts[-1], r.evidence)
        sentence_relations_valid = True
        recorded_rels = r.sentence_relations[-1] if r.sentence_relations else []
        recorded_by_id = {rec.id: rec for rec in recorded_rels}
        if len(relations) != len(recorded_by_id):
            sentence_relations_valid = False
        for rel in relations:
            rec = recorded_by_id.get(rel.id)
            if not rec or rec.sentence != rel.sentence or rec.semantic_verdict != "SUPPORTED":
                sentence_relations_valid = False
                break
            matching_claims = [c for c in final_claims if c.sentence == rel.sentence]
            matching_ids = {c.id for c in matching_claims}
            rel_spans = [span.quote for v in final_verdicts if v.claim_id in matching_ids for span in v.supporting_spans]
            rel_assessment = verify_sentence_relation(rel, rel_spans)
            if not rel_assessment.passed:
                sentence_relations_valid = False
                break
            if not sentence_relations_valid:
                break
        claim_sentence_spans = {
            c.id: [span.quote for v in final_verdicts if v.claim_id in {other.id for other in final_claims if other.sentence == c.sentence} for span in v.supporting_spans]
            for c in final_claims
        }
        grounded = (len(claim_by_id) == len(final_claims)
            and {v.claim_id for v in final_verdicts} == set(claim_by_id)
            and sentence_relations_valid
            and all(v.verdict == "SUPPORTED" and v.relation_integrity_passed
                and v.relationship_verdict == "ENTAILED" and v.claim_relations
                and v.evidence_relation in {"DIRECT_DESCRIPTIVE_SUPPORT", "DIRECT_CAUSAL_SUPPORT",
                    "DIRECT_RECOMMENDATION", "DIRECT_EFFECTIVENESS_SUPPORT", "CONTEXTUAL_SUPPORT"}
                and relation_recheck(v, claim_by_id[v.claim_id], claim_sentence_spans.get(v.claim_id))
                and v.supporting_spans and v.supporting_span_ids
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
    dump_json(output / "semantic_verification.json", [SemanticRecord(schema_version="2.0", slot_id=r.slot.id, attempts=r.semantic_reports,
        latencies_seconds=r.verification_latencies_seconds).model_dump() for r in ordered])
    verdicts = [v for r in ordered for report in r.semantic_reports for v in report.verdicts]
    dump_json(output / "grounding_summary.json", GroundingSummary(slots=len(ordered), atomic_claims_evaluated=len(verdicts),
        verdict_counts={label: sum(v.verdict == label for v in verdicts) for label in
            ("SUPPORTED", "CONTRADICTED", "INSUFFICIENT_EVIDENCE", "AMBIGUOUS", "VERIFICATION_ERROR")},
        verification_latency_seconds=round(sum(sum(r.verification_latencies_seconds) for r in ordered), 3),
        accepted_claims=sum(len(r.atomic_claims[-1]) for r in ordered if r.status == "accepted" and r.atomic_claims)).model_dump())
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

    # Human review gating before posts.csv shipment
    shipped_slots = []
    ready_review_slots = []
    for r in ordered:
        if r.status != "accepted":
            continue
        req_human = getattr(r, "human_approval_required", False)
        is_approved = getattr(r, "human_approved", False)
        approval_rec = getattr(r, "human_approval_record", None)

        if req_human:
            # When human approval is required by policy, an authenticated HumanApprovalRecord is mandatory
            if not is_approved or approval_rec is None:
                ready_review_slots.append(r)
                continue
            # Validate the approval record against draft text and policy
            draft_text = "\n\n".join(r.drafts[-1].tweets) if r.drafts else ""
            expected_pol_id = approval_rec.policy_id
            expected_pol_ver = r.business_policy_version or approval_rec.policy_version
            valid, reason = approval_rec.verify(draft_text, expected_pol_id, expected_pol_ver)
            if not valid:
                raise ValueError(f"Slot {r.slot.id} has invalid human approval record: {reason}")
            shipped_slots.append(r)
        else:
            shipped_slots.append(r)

    ready_review_records = [
        AcceptedRecord.model_validate({**r.model_dump(), "image_spec_reference": f"spec:visual_specs/{r.slot.id}.md"}).model_dump(exclude={"visual_spec"})
        for r in ready_review_slots
    ]
    dump_json(output / "ready_for_human_review.json", ready_review_records)

    with (output / "posts.csv").open("w", newline="") as file:
        writer = csv.writer(file)
        writer.writerow(["Post Text", "Image"])
        for r in shipped_slots:
            tweets = r.drafts[-1].tweets
            text = "\n\n".join(f"{i}/{len(tweets)} {tweet}" for i, tweet in enumerate(tweets, 1)) if len(tweets) > 1 else tweets[0]
            writer.writerow([text, f"spec:visual_specs/{r.slot.id}.md"])
    prompt_values = [r.prompt_tokens for r in ordered]
    completion_values = [r.completion_tokens for r in ordered]
    summary = {
        "model": model_name,
        "planned": len(plan.slots),
        "shipped": len(shipped_slots),
        "ready_for_human_review": len(ready_review_slots),
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
        "pipeline_mode": mode,
    }
    summary = Summary.model_validate(summary).model_dump()
    dump_json(output / "summary.json", summary)
    return summary

