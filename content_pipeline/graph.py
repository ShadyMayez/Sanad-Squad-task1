from __future__ import annotations

import operator
from typing import Annotated, TypedDict
from langgraph.graph import StateGraph, START, END
from langgraph.types import Send
from .agents import ResearchAgent, ReviewerAgent, VisualAgent, WriterAgent
from .schemas import BrandRules, Draft, KnowledgeBase, Plan, Registry, Review, Slot, SlotResult, Vulnerability
from .skills import EvidenceLookup
from .validation import validate_draft
from .claim_extraction import extract_claims
from .provenance import evidence_errors
from .semantic_verification import SemanticVerifier, error_report
from .schemas import AtomicClaim, SemanticReport


class PieceState(TypedDict, total=False):
    slot: Slot
    index: int
    topic: Vulnerability
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


def build_piece_graph(model, lookup: EvidenceLookup, registry: Registry, brand_text: str, brand_rules: BrandRules):
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
        return {"claims": claims, "extraction_errors": errors,
                "atomic_claims": state.get("atomic_claims", []) + [claims]}

    def provenance(state: PieceState):
        errors = [error for item in state["topic"].evidence for error in evidence_errors(item)]
        return {"provenance_errors": errors,
            **({"error": "Source provenance failed: " + "; ".join(errors)} if errors else {})}

    async def semantic(state: PieceState):
        if state["extraction_errors"] or state["provenance_errors"] or not state["claims"]:
            report = error_report(state["claims"], "; ".join(state["extraction_errors"] + state["provenance_errors"]) or "No atomic claims")
            usage, latency = {}, 0.0
        else:
            report, usage, latency = await semantic_verifier.run(state["claims"], state["topic"].evidence)
        verification_errors = [v.reason for v in report.verdicts if v.verdict == "VERIFICATION_ERROR"]
        # Draft extraction errors remain content feedback; model/source failures
        # are slot failures and do not consume a content revision attempt.
        failure = verification_errors if not state["extraction_errors"] else []
        return {"semantic_report": report,
                "semantic_reports": state.get("semantic_reports", []) + [report],
                "verification_latencies_seconds": state.get("verification_latencies_seconds", []) + [latency],
                **({"error": "Semantic verifier failed: " + "; ".join(failure)} if failure else {}),
                **add_usage(state, usage)}

    async def evaluate(state: PieceState):
        topic = state["topic"]
        evidence = topic.evidence
        spec = registry.types[state["slot"].type]
        semantic_errors = [f"Atomic claim {v.claim_id}: {v.verdict}: {v.reason}" for v in state["semantic_report"].verdicts if v.verdict != "SUPPORTED"]
        errors = validate_draft(state["draft"], spec, brand_rules, evidence, lookup) + state["extraction_errors"] + state["provenance_errors"] + semantic_errors
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
        semantic_pass = len(verdicts) == len(state["claims"]) and bool(verdicts) and all(v.verdict == "SUPPORTED" for v in verdicts)
        if state["review"].approved and not state["validation"] and semantic_pass and not state["provenance_errors"]:
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
            atomic_claims=state.get("atomic_claims", []), semantic_reports=state.get("semantic_reports", []),
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
            atomic_claims=state.get("atomic_claims", []), semantic_reports=state.get("semantic_reports", []),
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
            atomic_claims=state.get("atomic_claims", []), semantic_reports=state.get("semantic_reports", []),
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


def build_week_graph(model, kb: KnowledgeBase, registry: Registry, brand_text: str, brand_rules: BrandRules):
    lookup = EvidenceLookup(kb)
    piece_graph = build_piece_graph(model, lookup, registry, brand_text, brand_rules)

    def dispatch(state: WeekState):
        return [Send("worker", {"slot": slot, "index": index}) for index, slot in enumerate(state["plan"].slots)]

    async def worker(state: PieceState):
        try:
            done = await piece_graph.ainvoke(state, config={"recursion_limit": 22})
            result = done["result"]
        except Exception as exc:
            result = SlotResult(slot=state["slot"], status="failed", reason=f"{type(exc).__name__}: {exc}")
        return {"results": [result]}

    graph = StateGraph(WeekState)
    graph.add_node("worker", worker)
    graph.add_conditional_edges(START, dispatch, ["worker"])
    graph.add_edge("worker", END)
    return graph.compile(), lookup

