from __future__ import annotations

import operator
import time
from pathlib import Path
from typing import Annotated, TypedDict, Any, Optional
from langgraph.graph import StateGraph, START, END
from langgraph.types import Send
from .config import ROOT
from .agents import ResearchAgent, ReviewerAgent, VisualAgent, WriterAgent, EvidenceFirstWriterAgent
from .schemas import BrandRules, Claim, Draft, KnowledgeBase, Plan, Registry, Review, Slot, SlotResult, Vulnerability
from .schemas import AtomicClaim, SemanticReport, SentenceRelationRecord, SemanticVerdict, SupportingSpan
from .skills import EvidenceLookup
from .validation import validate_draft, validate_brand_and_platform, validate_piece_deterministic
from .claim_extraction import extract_claims, extract_sentence_relations
from .provenance import evidence_errors
from .relation_integrity import verify_sentence_relation
from .semantic_verification import SemanticVerifier, error_report
from .proposition_catalog import load_catalog, PropositionCatalog
from .content_planning import (
    build_evidence_first_plan,
    check_evidence_sufficiency,
    EvidenceFirstPlan,
    build_marketing_evidence_plan,
    build_external_technical_plan,
)
from .conformance import verify_plan_conformance, ConformanceReport
from .business_policy import load_business_policy, BusinessPolicy
from .source_authority import TechnicalSourceStrategy, MarketingSourceStrategy, SourceAuthorityContext
from .research import ResearchService, load_sources_config
from .marketing_planner import (
    MarketingSlotPlanner,
    validate_weekly_marketing_results,
    normalize_commercial_service,
    map_service_to_research_category,
    OFFICIAL_COMMERCIAL_SERVICES,
    COMMERCIAL_TO_RESEARCH_TAXONOMY,
)


class PieceState(TypedDict, total=False):
    slot: Slot
    index: int
    topic: Vulnerability
    topic_id: str
    plan_v2: EvidenceFirstPlan
    source_context: Any
    marketing_meta: Any
    writing_quality_report: Any
    fetched_urls: list[str]
    resource_brief: Any
    evidence_items: list[Any]
    research_service: Any
    conformance_report: ConformanceReport
    business_policy: BusinessPolicy
    draft: Draft
    validation: list[str]
    review: Review
    attempt: int
    drafts: list[Draft]
    validations: list[list[str]]
    reviews: list[Review]
    prompt_tokens: int | None
    completion_tokens: int | None
    usage_measurements_complete: bool
    result: SlotResult
    error: str
    claims: list[AtomicClaim]
    extraction_errors: list[str]
    provenance_errors: list[str]
    semantic_report: SemanticReport
    atomic_claims: list[list[AtomicClaim]]
    semantic_reports: list[SemanticReport]
    verification_latencies_seconds: list[float]
    sentence_relations: list[list[SentenceRelationRecord]]


class WeekState(TypedDict, total=False):
    plan: Plan
    results: Annotated[list[SlotResult], operator.add]


def add_usage(state: PieceState, usage: dict) -> dict:
    prompt = usage.get("input_tokens")
    completion = usage.get("output_tokens")
    return {
        "prompt_tokens": (state.get("prompt_tokens") or 0) + prompt if prompt is not None else state.get("prompt_tokens"),
        "completion_tokens": (state.get("completion_tokens") or 0) + completion if completion is not None else state.get("completion_tokens"),
        "usage_measurements_complete": state.get("usage_measurements_complete", True) and usage.get("usage_complete", True) and prompt is not None and completion is not None,
    }


def build_legacy_piece_graph(model, lookup: EvidenceLookup, registry: Registry, brand_text: str, brand_rules: BrandRules):
    research_agent = ResearchAgent(lookup)
    reviewer_agent = ReviewerAgent(model, lookup, brand_text)
    visual_agent = VisualAgent()
    semantic_verifier = SemanticVerifier(model)

    def research(state: PieceState):
        try:
            return {"topic": research_agent.run(state["slot"], state["index"])}
        except Exception as exc:
            return {"error": f"Research failed: {type(exc).__name__}: {exc}"}

    async def write(state: PieceState):
        slot = state["slot"]
        spec = registry.types[slot.type]
        writer = WriterAgent(model, spec, brand_text)
        feedback = None
        if state.get("review"):
            feedback = state["review"].corrections + state["review"].reasons
        try:
            draft, usage = await writer.run(slot, state["topic"], feedback)
            return {"draft": draft, "attempt": state.get("attempt", 0) + 1,
                    "drafts": state.get("drafts", []) + [draft], **add_usage(state, usage)}
        except Exception as exc:
            return {"error": f"Writer failed: {type(exc).__name__}: {exc}"}

    def extract(state: PieceState):
        claims, errors = extract_claims(state["draft"], state["topic"].evidence)
        relations = extract_sentence_relations(state["draft"], state["topic"].evidence)
        return {"claims": claims, "extraction_errors": errors,
                "atomic_claims": state.get("atomic_claims", []) + [claims],
                "sentence_relations": state.get("sentence_relations", []) + [relations]}

    def provenance(state: PieceState):
        errors = [error for item in state["topic"].evidence for error in evidence_errors(item)]
        return {"provenance_errors": errors,
            **({"error": "Source provenance failed: " + "; ".join(errors)} if errors else {})}

    async def semantic(state: PieceState):
        current_relations = state.get("sentence_relations", [[]])[-1] if state.get("sentence_relations") else []
        if state["extraction_errors"] or state["provenance_errors"] or not state["claims"]:
            report = error_report(state["claims"], "; ".join(state["extraction_errors"] + state["provenance_errors"]) or "No atomic claims")
            usage, latency = None, 0.0
            updated_relations = current_relations
        else:
            report, usage, latency = await semantic_verifier.run(state["claims"], state["topic"].evidence, relations=current_relations)
            updated_relations = report.sentence_relations if report.sentence_relations else current_relations
        verification_errors = [v.reason for v in report.verdicts if v.verdict == "VERIFICATION_ERROR"]
        # Draft extraction errors remain content feedback; model/source failures
        # are slot failures and do not consume a content revision attempt.
        failure = verification_errors if not state["extraction_errors"] else []
        stored_sentence_relations = list(state.get("sentence_relations", []))
        if stored_sentence_relations:
            stored_sentence_relations[-1] = updated_relations
        else:
            stored_sentence_relations = [updated_relations]
        return {"semantic_report": report,
                "semantic_reports": state.get("semantic_reports", []) + [report],
                "sentence_relations": stored_sentence_relations,
                "verification_latencies_seconds": state.get("verification_latencies_seconds", []) + [latency],
                **({"error": "Semantic verifier failed: " + "; ".join(failure)} if failure else {}),
                **(add_usage(state, usage) if usage is not None else {})}

    async def evaluate(state: PieceState):
        topic = state["topic"]
        evidence = topic.evidence
        spec = registry.types[state["slot"].type]
        semantic_errors = [f"Atomic claim {v.claim_id}: {v.verdict}: {v.relation_error or v.reason}"
            for v in state["semantic_report"].verdicts if v.verdict != "SUPPORTED" or not v.relation_integrity_passed]
        relation_errors = []
        final_verdicts = state["semantic_report"].verdicts
        expected_relations = extract_sentence_relations(state["draft"], evidence)
        verified_relations = state.get("sentence_relations", [[]])[-1] if state.get("sentence_relations") else []
        verified_by_id = {r.id: r for r in verified_relations}
        if len(expected_relations) != len(verified_relations):
            relation_errors.append(f"Sentence relation count mismatch: expected {len(expected_relations)}, verified {len(verified_relations)}")
        for rel in expected_relations:
            sentence_claims = [c for c in state["claims"] if c.sentence == rel.sentence]
            sentence_spans = [span.quote for v in final_verdicts if v.claim_id in {c.id for c in sentence_claims} for span in v.supporting_spans]
            rel_assessment = verify_sentence_relation(rel, sentence_spans)
            if not rel_assessment.passed:
                relation_errors.append(f"Sentence relation {rel.id} ({rel.connector}): deterministic gate: {rel_assessment.reason}")
            rec = verified_by_id.get(rel.id)
            if not rec or rec.sentence != rel.sentence:
                relation_errors.append(f"Sentence relation {rel.id} ({rel.connector}): missing verified relation record")
            elif rec.semantic_verdict != "SUPPORTED":
                relation_errors.append(f"Sentence relation {rel.id} ({rel.connector}): model verdict {rec.semantic_verdict or 'MISSING'}: {rec.justification or 'No justification'}")
        errors = validate_draft(state["draft"], spec, brand_rules, evidence, lookup) + state["extraction_errors"] + state["provenance_errors"] + semantic_errors + relation_errors
        try:
            review, usage = await reviewer_agent.run(state["draft"], evidence, errors, state["semantic_report"])
            return {"validation": errors, "review": review,
                    "validations": state.get("validations", []) + [errors],
                    "reviews": state.get("reviews", []) + [review], **add_usage(state, usage)}
        except Exception as exc:
            return {"validation": errors, "validations": state.get("validations", []) + [errors],
                    "error": f"Reviewer failed: {type(exc).__name__}: {exc}"}

    def route(state: PieceState) -> str:
        verdicts = state["semantic_report"].verdicts
        semantic_pass = len(verdicts) == len(state["claims"]) and bool(verdicts) and all(
            v.verdict == "SUPPORTED" and v.relation_integrity_passed and v.relationship_verdict == "ENTAILED"
            for v in verdicts)
        expected_relations = extract_sentence_relations(state["draft"], state["topic"].evidence)
        verified_relations = state.get("sentence_relations", [[]])[-1] if state.get("sentence_relations") else []
        verified_by_id = {r.id: r for r in verified_relations}
        relation_pass = (
            len(expected_relations) == len(verified_relations)
            and all(
                r.id in verified_by_id
                and verified_by_id[r.id].sentence == r.sentence
                and verified_by_id[r.id].semantic_verdict == "SUPPORTED"
                and verify_sentence_relation(
                    r,
                    [span.quote for v in verdicts if v.claim_id in {c.id for c in state["claims"] if c.sentence == r.sentence} for span in v.supporting_spans]
                ).passed
                for r in expected_relations
            )
        )
        if state["review"].approved and not state["validation"] and semantic_pass and relation_pass and not state["provenance_errors"]:
            return "visual"
        return "write" if state["attempt"] < 2 else "drop"

    def route_or_fail(state: PieceState, next_node: str) -> str:
        return "fail" if state.get("error") else next_node

    def fail(state: PieceState):
        topic = state.get("topic")
        return {"result": SlotResult(slot=state["slot"], status="failed",
            topic=topic.name if topic else None,
            source_ids=[e.id for e in topic.evidence] if topic else [],
            evidence=topic.evidence if topic else [],
            drafts=state.get("drafts", []), validations=state.get("validations", []),
            reviews=state.get("reviews", []), reason=state["error"],
            prompt_tokens=state.get("prompt_tokens"), completion_tokens=state.get("completion_tokens"), usage_measurements_complete=False,
            atomic_claims=state.get("atomic_claims", []),
            sentence_relations=state.get("sentence_relations", []),
            semantic_reports=state.get("semantic_reports", []),
            verification_latencies_seconds=state.get("verification_latencies_seconds", []),
            provenance_errors=state.get("provenance_errors", []))}

    def visual(state: PieceState):
        topic = state["topic"]
        slot = state["slot"]
        try:
            specification = visual_agent.run(slot, topic.name, state["draft"], state["claims"], topic.evidence, state["semantic_report"])
        except Exception as exc:
            return {"error": f"Visual Agent failed: {type(exc).__name__}: {exc}"}
        return {"result": SlotResult(slot=slot, status="accepted", topic=topic.name,
            source_ids=[e.id for e in topic.evidence], evidence=topic.evidence,
            drafts=state["drafts"], validations=state["validations"], reviews=state["reviews"],
            visual_spec=specification,
            prompt_tokens=state.get("prompt_tokens"), completion_tokens=state.get("completion_tokens"), usage_measurements_complete=state.get("usage_measurements_complete", True),
            atomic_claims=state.get("atomic_claims", []),
            sentence_relations=state.get("sentence_relations", []),
            semantic_reports=state.get("semantic_reports", []),
            verification_latencies_seconds=state.get("verification_latencies_seconds", []),
            provenance_errors=state.get("provenance_errors", []))}

    def drop(state: PieceState):
        topic = state["topic"]
        reasons = state["review"].reasons + state["validation"]
        return {"result": SlotResult(slot=state["slot"], status="dropped", topic=topic.name,
            source_ids=[e.id for e in topic.evidence], evidence=topic.evidence,
            drafts=state["drafts"], validations=state["validations"], reviews=state["reviews"],
            reason="; ".join(dict.fromkeys(reasons)),
            prompt_tokens=state.get("prompt_tokens"), completion_tokens=state.get("completion_tokens"), usage_measurements_complete=state.get("usage_measurements_complete", True),
            atomic_claims=state.get("atomic_claims", []),
            sentence_relations=state.get("sentence_relations", []),
            semantic_reports=state.get("semantic_reports", []),
            verification_latencies_seconds=state.get("verification_latencies_seconds", []),
            provenance_errors=state.get("provenance_errors", []))}

    graph = StateGraph(PieceState)
    for name, fn in (("research", research), ("write", write), ("extract", extract), ("provenance", provenance), ("semantic", semantic), ("evaluate", evaluate), ("visual", visual), ("drop", drop), ("fail", fail)):
        graph.add_node(name, fn)
    graph.add_edge(START, "research")
    graph.add_conditional_edges("research", lambda s: route_or_fail(s, "write"), {"write": "write", "fail": "fail"})
    graph.add_conditional_edges("write", lambda s: route_or_fail(s, "extract"), {"extract": "extract", "fail": "fail"})
    graph.add_edge("extract", "provenance")
    graph.add_conditional_edges("provenance", lambda s: route_or_fail(s, "semantic"), {"semantic": "semantic", "fail": "fail"})
    graph.add_conditional_edges("semantic", lambda s: route_or_fail(s, "evaluate"), {"evaluate": "evaluate", "fail": "fail"})
    graph.add_conditional_edges("evaluate", lambda s: route_or_fail(s, route(s) if not s.get("error") else "fail"), {"visual": "visual", "write": "write", "drop": "drop", "fail": "fail"})
    graph.add_conditional_edges("visual", lambda s: route_or_fail(s, "done"), {"done": END, "fail": "fail"})
    graph.add_edge("drop", END)
    graph.add_edge("fail", END)
    return graph.compile()


def build_v2_piece_graph(
    model,
    lookup: EvidenceLookup,
    registry: Registry,
    brand_text: str,
    brand_rules: BrandRules,
    mode: str | None = None,
    catalog: PropositionCatalog | None = None,
    business_policy: BusinessPolicy | None = None,
    authorization_mode: str = "pilot_evaluation",
    research_service: ResearchService | None = None,
):
    import os
    selected_mode = mode or os.getenv("SANADSQUAD_MODE", "evidence_first_v2")

    if catalog is None:
        catalog = load_catalog(ROOT / "knowledge" / "evidence_first_v2" / "catalog.json")
    if business_policy is None:
        business_policy = load_business_policy(ROOT / "knowledge" / "evidence_first_v2" / "policies" / "security_audit_firm.json")

    res_service = research_service or ResearchService()
    prop_map = {p.id: p for p in catalog.propositions}
    witness_map = catalog.evidence_witnesses

    writer_agents = {
        c_type: EvidenceFirstWriterAgent(
            model,
            content_type=c_type,
            role_instruction_file=spec.instruction_file,
        )
        for c_type, spec in registry.types.items()
    }
    reviewer_agent = ReviewerAgent(model, lookup, brand_text)
    visual_agent = VisualAgent()

    def research(state: PieceState):
        slot = state["slot"]
        slot_type = slot.type

        # 1. Marketing research pathway
        if slot_type == "marketing-post":
            use_marketing_research = (
                selected_mode in ["v3_marketing_research", "v3"]
                or state.get("marketing_meta") is not None
                or state.get("research_mode") in ["fixture", "live"]
                or getattr(slot, "source_strategy", None) == "web_research"
                or getattr(slot, "service_line", None) is not None
                or (slot.focus and (slot.focus in OFFICIAL_COMMERCIAL_SERVICES or slot.focus in COMMERCIAL_TO_RESEARCH_TAXONOMY))
            )
            if use_marketing_research:
                meta = state.get("marketing_meta")
                raw_service = getattr(slot, "service_line", None)
                if not raw_service and meta:
                    raw_service = getattr(meta, "service_line", None) or (meta.get("service_line") if isinstance(meta, dict) else None)
                if not raw_service:
                    raw_service = slot.focus

                service_line = map_service_to_research_category(raw_service) if raw_service else "web3-security"

                is_vuln_exception = bool(state.get("is_vulnerability_class_exception", False))
                supp_kb = None
                if is_vuln_exception and slot.focus:
                    try:
                        supp_kb = [lookup.select(slot.focus, state.get("index", 0))]
                    except Exception:
                        supp_kb = None

                r_mode = state.get("research_mode")
                ev_list, source_ids, err = res_service.conduct_marketing_research(
                    slot_id=slot.id,
                    service_line=service_line,
                    topic_focus=slot.focus,
                    is_vulnerability_class_exception=is_vuln_exception,
                    supplemental_kb_vulnerabilities=supp_kb,
                    research_mode=r_mode,
                )
                if err:
                    return {"error": f"INSUFFICIENT_EVIDENCE: {err}"}

                topic = Vulnerability(
                    id=f"MKT_{service_line.upper().replace('-', '_')}_{slot.id}",
                    name=f"Marketing Security Brief: {service_line.title()}",
                    severity="medium",
                    category=f"service:{service_line}",
                    description=f"Marketing research for {service_line}",
                    root_cause=f"External research findings for {service_line}",
                    evidence=ev_list,
                )
                fetched_urls = [e.url for e in ev_list if e.url]
                return {
                    "topic": topic,
                    "topic_id": topic.id,
                    "fetched_urls": fetched_urls,
                    "evidence_items": ev_list,
                }

        # 2. Tech-thread Strategy 2 (External Technical Resource)
        if slot_type == "tech-thread":
            is_external_tech = (
                state.get("tech_strategy") == "external"
                or (slot.focus and slot.focus.startswith("http"))
            )
            if is_external_tech:
                url = slot.focus if (slot.focus and slot.focus.startswith("http")) else "https://ethereum.org/developers/docs/smart-contracts/formal-verification/"
                r_mode = state.get("research_mode")
                ev_list, brief, err = res_service.conduct_technical_external_research(slot.id, url, research_mode=r_mode)
                if err:
                    return {"error": f"RESEARCH_FAILED: {err}"}

                topic = Vulnerability(
                    id=f"TECH_EXT_{slot.id}",
                    name=brief.title if brief else "External Technical Report",
                    severity="high",
                    category="external_technical",
                    description=brief.summary_brief if brief else "External technical brief",
                    root_cause="External technical post-mortem analysis",
                    evidence=ev_list,
                )
                return {
                    "topic": topic,
                    "topic_id": topic.id,
                    "resource_brief": brief,
                    "fetched_urls": [brief.url] if brief else [],
                    "evidence_items": ev_list,
                }

        # 3. Default Strategy 1: Knowledge Base (KB)
        try:
            topic = lookup.select(state["slot"].focus, state["index"])
            topic_id = topic.id
            preflight = check_evidence_sufficiency(topic_id, state["slot"].type, catalog)
            if not preflight.is_sufficient:
                return {
                    "topic": topic,
                    "topic_id": topic_id,
                    "error": f"INSUFFICIENT_EVIDENCE: {preflight.reason}",
                }
            return {"topic": topic, "topic_id": topic_id}
        except Exception as exc:
            return {"error": f"Research failed: {type(exc).__name__}: {exc}"}

    def plan(state: PieceState):
        try:
            mode = state.get("authorization_mode") or authorization_mode
            slot = state["slot"]
            # Marketing research plan
            ev_list = state.get("evidence_items") or (state.get("topic").evidence if state.get("topic") else None)
            if ev_list and slot.type == "marketing-post":
                meta = state.get("marketing_meta")
                raw_service = getattr(slot, "service_line", None)
                if not raw_service and meta:
                    raw_service = getattr(meta, "service_line", None) or (meta.get("service_line") if isinstance(meta, dict) else None)
                if not raw_service:
                    raw_service = slot.focus
                service_line = normalize_commercial_service(raw_service) if raw_service else "blockchain-security-audits"
                fmt_spec = None
                has_cta = False
                if meta:
                    fmt_val = getattr(meta, "selected_format", None) or (meta.get("selected_format") if isinstance(meta, dict) else None)
                    has_cta = bool(getattr(meta, "has_cta", False) if hasattr(meta, "has_cta") else (meta.get("has_cta", False) if isinstance(meta, dict) else False))
                    if fmt_val:
                        from .marketing_format import FORMAT_SPECS
                        fmt_spec = FORMAT_SPECS.get(fmt_val)

                from .contact_config import load_company_contact
                contact_cfg = load_company_contact()

                p = build_marketing_evidence_plan(
                    slot_id=slot.id,
                    service_line=service_line,
                    evidence_items=ev_list,
                    format_spec=fmt_spec,
                    has_cta=has_cta,
                    contact_config=contact_cfg,
                    policy=business_policy,
                    authorization_mode=mode,
                )
                return {"plan_v2": p}

            # External technical resource plan
            if state.get("resource_brief") and slot.type == "tech-thread":
                p = build_external_technical_plan(
                    slot_id=slot.id,
                    resource_brief=state["resource_brief"],
                    evidence_items=state.get("evidence_items", []),
                    policy=business_policy,
                    authorization_mode=mode,
                )
                return {"plan_v2": p}

            # Standard KB catalog plan
            p = build_evidence_first_plan(
                state["slot"].id,
                state["topic_id"],
                state["slot"].type,
                catalog,
                policy=business_policy,
                authorization_mode=mode,
            )
            ref_errors = p.validate_plan_references(
                catalog,
                active_policy=business_policy,
                authorization_mode=mode,
            )
            if ref_errors:
                return {"error": f"Plan reference validation failed: {ref_errors}"}
            return {"plan_v2": p}
        except Exception as exc:
            return {"error": f"Planning failed: {type(exc).__name__}: {exc}"}

    async def write(state: PieceState):
        p = state["plan_v2"]
        slot_type = state["slot"].type
        is_marketing = (slot_type == "marketing-post" or p.content_type == "marketing-post")
        feedback = None

        if is_marketing:
            val_errors = state.get("validation", [])
            conf = state.get("conformance_report")
            conf_errors = [r.reason for r in conf.results if not r.passed] if conf else []
            rev = state.get("review")
            rev_reasons = rev.reasons if rev else []
            all_issue_reasons = val_errors + conf_errors

            if all_issue_reasons or (rev and not rev.approved):
                from .character_budget import build_precise_marketing_feedback
                feedback = build_precise_marketing_feedback(
                    draft=state.get("draft"),
                    plan=p,
                    validation_errors=all_issue_reasons,
                    review_reasons=rev_reasons,
                )
        else:
            if state.get("conformance_report") and not state["conformance_report"].all_conforming:
                feedback = []
                exact_count = len(p.units)
                had_count_mismatch = (len(state["draft"].tweets) != exact_count)
                if had_count_mismatch:
                    feedback.append({
                        "unit_id": "COUNT_MISMATCH",
                        "tweet_index": -1,
                        "failing_text": f"Generated {len(state['draft'].tweets)} tweets",
                        "verdict": "FORMAT_VIOLATION",
                        "reasons": [f"Expected exactly {exact_count} tweet(s), got {len(state['draft'].tweets)}."],
                        "feedback": f"CRITICAL: The tweets list MUST contain EXACTLY {exact_count} string(s).",
                    })
                for idx, r in enumerate(state["conformance_report"].results):
                    if had_count_mismatch and "Plan unit count mismatch" in r.reason:
                        continue
                    if not r.passed:
                        feedback.append({
                            "unit_id": r.unit_id,
                            "tweet_index": idx,
                            "failing_text": r.tweet_text,
                            "verdict": r.verdict,
                            "reasons": [r.reason],
                            "feedback": f"Revise unit {r.unit_id} to strictly conform to its canonical propositions. Do NOT overstate mitigations as absolute guarantees, do NOT add unapproved causal claims, and preserve scope.",
                        })
            if state.get("validation"):
                if feedback is None:
                    feedback = []
                for err in state["validation"]:
                    feedback.append({
                        "unit_id": "VALIDATION_ERROR",
                        "tweet_index": 0,
                        "failing_text": state["draft"].tweets[0] if state.get("draft") and state["draft"].tweets else "",
                        "verdict": "VALIDATION_FAILURE",
                        "reasons": [err],
                        "feedback": f"Format/Brand/Action violation: {err}. Please correct this in the revised draft.",
                    })
        try:
            prev_tweets = state["draft"].tweets if state.get("draft") else None
            current_writer = writer_agents.get(slot_type) or EvidenceFirstWriterAgent(model, content_type=slot_type)
            draft, usage = await current_writer.run(p, catalog, targeted_feedback=feedback, previous_tweets=prev_tweets)
            # Bind draft claims deterministically to the plan unit's approved evidence IDs
            evidence_by_id = {e.id: e for e in state["topic"].evidence}
            claims = []
            for idx, tweet in enumerate(draft.tweets):
                unit_idx = min(idx, len(p.units) - 1) if p.units else 0
                u = p.units[unit_idx]
                u_ev_ids = []
                for pid in u.proposition_ids:
                    if pid in prop_map:
                        for s_ref in prop_map[pid].evidence_span_ids:
                            ev_id = s_ref.split("#")[0]
                            if ev_id in evidence_by_id:
                                u_ev_ids.append(ev_id)
                if not u_ev_ids and getattr(u, "source_evidence_ids", None):
                    u_ev_ids = [eid for eid in u.source_evidence_ids if eid in evidence_by_id]
                if not u_ev_ids and state["topic"].evidence:
                    u_ev_ids = [state["topic"].evidence[0].id]
                claims.append(Claim(text=tweet, evidence_ids=sorted(list(set(u_ev_ids)))))
            draft.claims = claims

            return {
                "draft": draft,
                "attempt": state.get("attempt", 0) + 1,
                "drafts": state.get("drafts", []) + [draft],
                **add_usage(state, usage),
            }
        except Exception as exc:
            return {"error": f"Writer failed: {type(exc).__name__}: {exc}"}

    def provenance(state: PieceState):
        errors = [error for item in state["topic"].evidence for error in evidence_errors(item)]
        return {
            "provenance_errors": errors,
            **({"error": "Source provenance failed: " + "; ".join(errors)} if errors else {}),
        }

    async def conformance(state: PieceState):
        p = state["plan_v2"]
        draft = state["draft"]
        started = time.monotonic()
        try:
            conf_report = await verify_plan_conformance(p, draft.tweets, catalog, model)
            latency = round(time.monotonic() - started, 3)

            # Build AtomicClaim and SemanticReport for downstream export & Reviewer compatibility
            atomic_claims: list[AtomicClaim] = []
            verdicts = []
            prop_map = {pr.id: pr for pr in catalog.propositions}
            witness_map = catalog.evidence_witnesses
            evidence_by_id = {e.id: e for e in state["topic"].evidence}

            for idx, u in enumerate(p.units):
                tweet_text = draft.tweets[idx] if idx < len(draft.tweets) else ""
                unit_res = conf_report.results[idx] if idx < len(conf_report.results) else None

                cand_ev_ids = []
                for pid in u.proposition_ids:
                    if pid in prop_map:
                        for span_ref in prop_map[pid].evidence_span_ids:
                            ev_id = span_ref.split("#")[0]
                            if ev_id in evidence_by_id:
                                cand_ev_ids.append(ev_id)
                if not cand_ev_ids:
                    cand_ev_ids = [e.id for e in state["topic"].evidence]
                cand_ev_ids = sorted(list(set(cand_ev_ids)))

                prop_desc = (
                    prop_map[u.proposition_ids[0]].canonical_text
                    if u.proposition_ids and u.proposition_ids[0] in prop_map
                    else tweet_text
                )
                claim = AtomicClaim(
                    id=f"{state['slot'].id}_claim_{idx+1}",
                    tweet_index=idx,
                    start=0,
                    end=max(1, len(tweet_text)),
                    span=tweet_text or "unit",
                    proposition=prop_desc or "proposition",
                    sentence=tweet_text or "sentence",
                    qualifiers=u.required_qualifiers,
                    candidate_evidence_ids=cand_ev_ids,
                )
                atomic_claims.append(claim)

                if unit_res and unit_res.passed:
                    spans = []
                    span_ids = []
                    for pid in u.proposition_ids:
                        if pid in prop_map:
                            for span_ref in prop_map[pid].evidence_span_ids:
                                parts = span_ref.split("#")
                                ev_id = parts[0]
                                span_idx = int(parts[1]) if len(parts) > 1 else 0
                                if ev_id in witness_map and ev_id in evidence_by_id:
                                    w = witness_map[ev_id]
                                    quote = w.spans[span_idx] if span_idx < len(w.spans) else w.source_quote
                                    spans.append(SupportingSpan(evidence_id=ev_id, quote=quote))
                                    span_ids.append(span_ref)
                    if not spans and state["topic"].evidence:
                        e0 = state["topic"].evidence[0]
                        spans.append(SupportingSpan(evidence_id=e0.id, quote=e0.source_quote or ""))
                        span_ids.append(f"{e0.id}#0")

                    verdicts.append(SemanticVerdict(
                        claim_id=claim.id,
                        verdict="SUPPORTED",
                        evidence_ids=cand_ev_ids,
                        reason=unit_res.reason,
                        supporting_spans=spans,
                        supporting_span_ids=span_ids,
                        proposed_supporting_spans=spans,
                        relationship_verdict="ENTAILED",
                        relation_integrity_passed=True,
                        claim_relations=["DESCRIPTIVE_FACT"],
                        evidence_relation="DIRECT_DESCRIPTIVE_SUPPORT",
                    ))
                else:
                    v_raw = unit_res.verdict if unit_res else "VERIFICATION_ERROR"
                    if v_raw == "CONTRADICTS_PLAN":
                        mapped_v = "CONTRADICTED"
                    elif v_raw == "INSUFFICIENT_EVIDENCE":
                        mapped_v = "INSUFFICIENT_EVIDENCE"
                    elif v_raw == "ABSTAIN":
                        mapped_v = "AMBIGUOUS"
                    else:
                        mapped_v = "VERIFICATION_ERROR"
                    fail_reason = unit_res.reason if unit_res else "Unit conformance evaluation missing"
                    verdicts.append(SemanticVerdict(
                        claim_id=claim.id,
                        verdict=mapped_v,
                        evidence_ids=cand_ev_ids,
                        reason=fail_reason,
                        supporting_spans=[],
                        supporting_span_ids=[],
                        proposed_supporting_spans=[],
                        relationship_verdict="NOT_ENTAILED",
                        relation_integrity_passed=False,
                        claim_relations=["OTHER"],
                        evidence_relation="INSUFFICIENT_RELATION",
                    ))

            semantic_rep = SemanticReport(verdicts=verdicts, sentence_relations=[])
            return {
                "conformance_report": conf_report,
                "claims": atomic_claims,
                "semantic_report": semantic_rep,
                "atomic_claims": state.get("atomic_claims", []) + [atomic_claims],
                "semantic_reports": state.get("semantic_reports", []) + [semantic_rep],
                "verification_latencies_seconds": state.get("verification_latencies_seconds", []) + [latency],
            }
        except Exception as exc:
            return {"error": f"Conformance verification failed: {type(exc).__name__}: {exc}"}

    async def evaluate(state: PieceState):
        conf_report = state.get("conformance_report")
        conf_errors = []
        if conf_report and not conf_report.all_conforming:
            conf_errors.append(f"Plan conformance failed: {conf_report.failure_summary}")

        policy_ok, policy_violations = business_policy.check_hard_policy_compliance(
            topic_id=state["topic_id"],
            content_type=state["slot"].type,
            used_source_ids=[e.id for e in state["topic"].evidence],
            tweet_texts=state["draft"].tweets,
        )

        spec = registry.types.get(state["slot"].type)
        allowed_urls = state.get("fetched_urls", [])
        meta = state.get("marketing_meta")
        fmt_name = None
        has_cta = False
        if meta:
            fmt_name = meta.selected_format.value if hasattr(meta, "selected_format") else (meta.get("format") if isinstance(meta, dict) else None)
            has_cta = bool(getattr(meta, "has_cta", False) if hasattr(meta, "has_cta") else (meta.get("has_cta", False) if isinstance(meta, dict) else False))

        from .contact_config import load_company_contact
        contact_cfg = load_company_contact()

        passed, det_errors, writing_report = validate_piece_deterministic(
            tweets=state["draft"].tweets,
            brand=brand_rules,
            spec=spec,
            allowed_run_links=allowed_urls,
            marketing_format=fmt_name,
            contact_config=contact_cfg,
            allow_cta=has_cta,
            content_type=state["slot"].type,
            enforce_review_invitation=(selected_mode == "legacy"),
            service_line=getattr(state["slot"], "service_line", None),
            evidence=getattr(state["topic"], "evidence", None),
        )

        all_errors = conf_errors + policy_violations + det_errors + state.get("provenance_errors", [])

        try:
            review, usage = await reviewer_agent.run(
                state["draft"],
                state["topic"].evidence,
                all_errors,
                state["semantic_report"],
            )

            # Enforce QualityThresholds from business_policy
            qt = business_policy.quality_thresholds
            threshold_errors = []
            if review.factual_support < qt.min_factual_support:
                threshold_errors.append(f"Quality threshold failed: factual_support {review.factual_support} < {qt.min_factual_support}")
            if review.technical_correctness < qt.min_technical_correctness:
                threshold_errors.append(f"Quality threshold failed: technical_correctness {review.technical_correctness} < {qt.min_technical_correctness}")
            if review.brand_voice < qt.min_brand_voice:
                threshold_errors.append(f"Quality threshold failed: brand_voice {review.brand_voice} < {qt.min_brand_voice}")
            if review.clarity < qt.min_clarity:
                threshold_errors.append(f"Quality threshold failed: clarity {review.clarity} < {qt.min_clarity}")
            if review.platform_format < qt.min_platform_format:
                threshold_errors.append(f"Quality threshold failed: platform_format {review.platform_format} < {qt.min_platform_format}")
            if review.usefulness < qt.min_usefulness:
                threshold_errors.append(f"Quality threshold failed: usefulness {review.usefulness} < {qt.min_usefulness}")

            # Hard deterministic quality violations immediately veto approval
            if det_errors or threshold_errors:
                review = review.model_copy(update={"approved": False, "reasons": review.reasons + det_errors + threshold_errors})
                all_errors = all_errors + threshold_errors

            return {
                "validation": all_errors,
                "review": review,
                "validations": state.get("validations", []) + [all_errors],
                "reviews": state.get("reviews", []) + [review],
                "writing_quality_report": writing_report.model_dump() if writing_report else None,
                **add_usage(state, usage),
            }
        except Exception as exc:
            return {
                "validation": all_errors,
                "validations": state.get("validations", []) + [all_errors],
                "error": f"Reviewer failed: {type(exc).__name__}: {exc}",
            }

    def route(state: PieceState) -> str:
        if state.get("error"):
            return "fail"
        conf = state.get("conformance_report")
        conf_passed = bool(conf and conf.all_conforming)
        review_passed = bool(state.get("review") and state["review"].approved)
        validation_passed = bool(state.get("validation") is not None and len(state["validation"]) == 0)
        prov_passed = not state.get("provenance_errors")

        if conf_passed and review_passed and validation_passed and prov_passed:
            return "visual"
        if state.get("attempt", 0) < 2:
            return "write"
        return "drop"

    def visual(state: PieceState):
        topic = state["topic"]
        slot = state["slot"]
        try:
            spec = visual_agent.run(slot, topic.name, state["draft"], state["claims"], topic.evidence, state["semantic_report"])
        except Exception as exc:
            return {"error": f"Visual Agent failed: {type(exc).__name__}: {exc}"}

        req_human = business_policy.human_review_requirements.require_human_approval_for_ship
        approval_rec = state.get("human_approval_record")
        is_approved = bool(state.get("human_approved", False) or approval_rec is not None)
        pub_status = "APPROVED_FOR_EXPORT" if (not req_human or (is_approved and approval_rec is not None)) else "READY_FOR_HUMAN_REVIEW"
        mode = state.get("authorization_mode") or authorization_mode
        meta = state.get("marketing_meta")
        has_cta = False
        if meta:
            has_cta = bool(getattr(meta, "has_cta", False) if hasattr(meta, "has_cta") else (meta.get("has_cta", False) if isinstance(meta, dict) else False))
        slot_obj = slot.model_copy(update={"has_cta": has_cta}) if hasattr(slot, "model_copy") else slot

        return {
            "result": SlotResult(
                slot=slot_obj,
                has_cta=has_cta,
                status="accepted",
                topic=topic.name,
                source_ids=[e.id for e in topic.evidence],
                evidence=topic.evidence,
                drafts=state["drafts"],
                validations=state["validations"],
                reviews=state["reviews"],
                visual_spec=spec,
                prompt_tokens=state.get("prompt_tokens"),
                completion_tokens=state.get("completion_tokens"),
                usage_measurements_complete=state.get("usage_measurements_complete", True),
                atomic_claims=state.get("atomic_claims", []),
                sentence_relations=state.get("sentence_relations", []),
                semantic_reports=state.get("semantic_reports", []),
                verification_latencies_seconds=state.get("verification_latencies_seconds", []),
                provenance_errors=state.get("provenance_errors", []),
                conformance_report=state["conformance_report"].model_dump() if state.get("conformance_report") else None,
                evidence_plan=state["plan_v2"].model_dump() if state.get("plan_v2") else None,
                human_approval_required=req_human,
                human_approved=is_approved,
                human_approval_witness=state.get("human_approval_witness"),
                human_approval_record=approval_rec,
                authorization_mode=mode,
                publication_status=pub_status,
                business_policy_version=business_policy.policy_version,
                pipeline_mode="evidence_first_v2",
                fetched_urls=state.get("fetched_urls", []),
                writing_quality_report=state.get("writing_quality_report"),
                source_strategy=getattr(state.get("plan_v2"), "source_strategy", None),
            )
        }

    def drop(state: PieceState):
        topic = state.get("topic")
        reasons = (state["review"].reasons if state.get("review") else []) + state.get("validation", [])
        return {
            "result": SlotResult(
                slot=state["slot"],
                status="dropped",
                topic=topic.name if topic else None,
                source_ids=[e.id for e in topic.evidence] if topic else [],
                evidence=topic.evidence if topic else [],
                drafts=state.get("drafts", []),
                validations=state.get("validations", []),
                reviews=state.get("reviews", []),
                reason="; ".join(dict.fromkeys(reasons)) or "Dropped after 2 attempts",
                prompt_tokens=state.get("prompt_tokens"),
                completion_tokens=state.get("completion_tokens"),
                usage_measurements_complete=state.get("usage_measurements_complete", True),
                atomic_claims=state.get("atomic_claims", []),
                sentence_relations=state.get("sentence_relations", []),
                semantic_reports=state.get("semantic_reports", []),
                verification_latencies_seconds=state.get("verification_latencies_seconds", []),
                provenance_errors=state.get("provenance_errors", []),
                conformance_report=state["conformance_report"].model_dump() if state.get("conformance_report") else None,
                evidence_plan=state["plan_v2"].model_dump() if state.get("plan_v2") else None,
                human_approval_required=business_policy.human_review_requirements.require_human_approval_for_ship,
                human_approved=bool(state.get("human_approved", False)),
                publication_status="DROPPED",
                business_policy_version=business_policy.policy_version,
                pipeline_mode="evidence_first_v2",
            )
        }

    def fail(state: PieceState):
        topic = state.get("topic")
        return {
            "result": SlotResult(
                slot=state["slot"],
                status="failed",
                topic=topic.name if topic else None,
                source_ids=[e.id for e in topic.evidence] if topic else [],
                evidence=topic.evidence if topic else [],
                drafts=state.get("drafts", []),
                validations=state.get("validations", []),
                reviews=state.get("reviews", []),
                reason=state.get("error", "Unknown execution failure"),
                prompt_tokens=state.get("prompt_tokens"),
                completion_tokens=state.get("completion_tokens"),
                usage_measurements_complete=False,
                atomic_claims=state.get("atomic_claims", []),
                sentence_relations=state.get("sentence_relations", []),
                semantic_reports=state.get("semantic_reports", []),
                verification_latencies_seconds=state.get("verification_latencies_seconds", []),
                provenance_errors=state.get("provenance_errors", []),
                pipeline_mode="evidence_first_v2",
            )
        }

    graph = StateGraph(PieceState)
    for name, fn in (
        ("research", research),
        ("plan", plan),
        ("write", write),
        ("provenance", provenance),
        ("conformance", conformance),
        ("evaluate", evaluate),
        ("visual", visual),
        ("drop", drop),
        ("fail", fail),
    ):
        graph.add_node(name, fn)

    graph.add_edge(START, "research")
    graph.add_conditional_edges("research", lambda s: "fail" if s.get("error") else "plan", {"plan": "plan", "fail": "fail"})
    graph.add_conditional_edges("plan", lambda s: "fail" if s.get("error") else "write", {"write": "write", "fail": "fail"})
    graph.add_conditional_edges("write", lambda s: "fail" if s.get("error") else "provenance", {"provenance": "provenance", "fail": "fail"})
    graph.add_conditional_edges("provenance", lambda s: "fail" if s.get("error") else "conformance", {"conformance": "conformance", "fail": "fail"})
    graph.add_conditional_edges("conformance", lambda s: "fail" if s.get("error") else "evaluate", {"evaluate": "evaluate", "fail": "fail"})
    graph.add_conditional_edges("evaluate", route, {"visual": "visual", "write": "write", "drop": "drop", "fail": "fail"})
    graph.add_edge("visual", END)
    graph.add_edge("drop", END)
    graph.add_edge("fail", END)
    return graph.compile()


def build_piece_graph(
    model,
    lookup: EvidenceLookup,
    registry: Registry,
    brand_text: str,
    brand_rules: BrandRules,
    mode: str | None = None,
    catalog: PropositionCatalog | None = None,
    business_policy: BusinessPolicy | None = None,
    authorization_mode: str = "pilot_evaluation",
    research_service: ResearchService | None = None,
):
    import os
    selected_mode = mode or os.getenv("SANADSQUAD_MODE", "legacy")
    if selected_mode == "legacy":
        return build_legacy_piece_graph(model, lookup, registry, brand_text, brand_rules)
    return build_v2_piece_graph(
        model,
        lookup,
        registry,
        brand_text,
        brand_rules,
        catalog=catalog,
        business_policy=business_policy,
        authorization_mode=authorization_mode,
        research_service=research_service,
    )


def build_week_graph(
    model,
    kb: KnowledgeBase,
    registry: Registry,
    brand_text: str,
    brand_rules: BrandRules,
    mode: str | None = None,
    catalog: PropositionCatalog | None = None,
    business_policy: BusinessPolicy | None = None,
    authorization_mode: str = "pilot_evaluation",
    research_service: ResearchService | None = None,
):
    import os
    selected_mode = mode or os.getenv("SANADSQUAD_MODE", "legacy")
    lookup = EvidenceLookup(kb)
    res_service = research_service or ResearchService()
    if selected_mode == "legacy":
        piece_graph = build_piece_graph(model, lookup, registry, brand_text, brand_rules)
    else:
        piece_graph = build_piece_graph(
            model,
            lookup,
            registry,
            brand_text,
            brand_rules,
            mode=selected_mode,
            catalog=catalog,
            business_policy=business_policy,
            authorization_mode=authorization_mode,
            research_service=res_service,
        )

    def dispatch(state: WeekState):
        mode_val = state.get("authorization_mode") or authorization_mode
        marketing_plan = None
        has_marketing = any(s.type == "marketing-post" for s in state["plan"].slots)
        if has_marketing and (selected_mode in ["v3", "evidence_first_v3"] or state.get("research_mode") in ["fixture", "live"]):
            try:
                marketing_plan = MarketingSlotPlanner.plan_weekly_slots(state["plan"].slots)
            except Exception:
                marketing_plan = None

        tasks = []
        for index, slot in enumerate(state["plan"].slots):
            meta = None
            if marketing_plan and slot.type == "marketing-post":
                meta = next((m for m in marketing_plan.slots if m.slot_id == slot.id), None)
            tasks.append(Send("worker", {
                "slot": slot,
                "index": index,
                "authorization_mode": mode_val,
                "marketing_meta": meta,
                "research_mode": state.get("research_mode"),
            }))
        return tasks

    async def worker(state: PieceState):
        try:
            done = await piece_graph.ainvoke(state, config={"recursion_limit": 22})
            result = done["result"]
        except Exception as exc:
            result = SlotResult(
                slot=state["slot"],
                status="failed",
                reason=f"{type(exc).__name__}: {exc}",
                pipeline_mode=selected_mode,
            )
        return {"results": [result]}

    graph = StateGraph(WeekState)
    graph.add_node("worker", worker)
    graph.add_conditional_edges(START, dispatch, ["worker"])
    graph.add_edge("worker", END)
    return graph.compile(), lookup

