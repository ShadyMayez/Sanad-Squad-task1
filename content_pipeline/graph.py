from __future__ import annotations

import operator
from typing import Annotated, TypedDict
from langgraph.graph import StateGraph, START, END
from langgraph.types import Send
from .agents import ResearchAgent, ReviewerAgent, VisualAgent, WriterAgent
from .schemas import BrandRules, Draft, KnowledgeBase, Plan, Registry, Review, Slot, SlotResult, Vulnerability
from .skills import EvidenceLookup
from .validation import validate_draft


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
    result: SlotResult
    error: str


class WeekState(TypedDict, total=False):
    plan: Plan
    results: Annotated[list[SlotResult], operator.add]


def add_usage(state: PieceState, usage: dict) -> dict:
    prompt = usage.get("input_tokens")
    completion = usage.get("output_tokens")
    return {
        "prompt_tokens": (state.get("prompt_tokens") or 0) + prompt if prompt is not None else state.get("prompt_tokens"),
        "completion_tokens": (state.get("completion_tokens") or 0) + completion if completion is not None else state.get("completion_tokens"),
    }


def build_piece_graph(model, lookup: EvidenceLookup, registry: Registry, brand_text: str, brand_rules: BrandRules):
    research_agent = ResearchAgent(lookup)
    reviewer_agent = ReviewerAgent(model, lookup, brand_text)
    visual_agent = VisualAgent()

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

    async def evaluate(state: PieceState):
        topic = state["topic"]
        evidence = topic.evidence
        spec = registry.types[state["slot"].type]
        errors = validate_draft(state["draft"], spec, brand_rules, evidence, lookup)
        try:
            review, usage = await reviewer_agent.run(state["draft"], evidence, errors)
            return {"validation": errors, "review": review,
                    "validations": state.get("validations", []) + [errors],
                    "reviews": state.get("reviews", []) + [review], **add_usage(state, usage)}
        except Exception as exc:
            return {"validation": errors, "validations": state.get("validations", []) + [errors],
                    "error": f"Reviewer failed: {type(exc).__name__}: {exc}"}

    def route(state: PieceState) -> str:
        if state["review"].approved and not state["validation"]:
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
            prompt_tokens=state.get("prompt_tokens"), completion_tokens=state.get("completion_tokens"))}

    def visual(state: PieceState):
        topic = state["topic"]
        slot = state["slot"]
        return {"result": SlotResult(slot=slot, status="accepted", topic=topic.name,
            source_ids=[e.id for e in topic.evidence], evidence=topic.evidence,
            drafts=state["drafts"], validations=state["validations"], reviews=state["reviews"],
            visual_spec=visual_agent.run(slot, topic.name),
            prompt_tokens=state.get("prompt_tokens"), completion_tokens=state.get("completion_tokens"))}

    def drop(state: PieceState):
        topic = state["topic"]
        reasons = state["review"].reasons + state["validation"]
        return {"result": SlotResult(slot=state["slot"], status="dropped", topic=topic.name,
            source_ids=[e.id for e in topic.evidence], evidence=topic.evidence,
            drafts=state["drafts"], validations=state["validations"], reviews=state["reviews"],
            reason="; ".join(dict.fromkeys(reasons)),
            prompt_tokens=state.get("prompt_tokens"), completion_tokens=state.get("completion_tokens"))}

    graph = StateGraph(PieceState)
    for name, fn in (("research", research), ("write", write), ("evaluate", evaluate), ("visual", visual), ("drop", drop), ("fail", fail)):
        graph.add_node(name, fn)
    graph.add_edge(START, "research")
    graph.add_conditional_edges("research", lambda s: route_or_fail(s, "write"), {"write": "write", "fail": "fail"})
    graph.add_conditional_edges("write", lambda s: route_or_fail(s, "evaluate"), {"evaluate": "evaluate", "fail": "fail"})
    graph.add_conditional_edges("evaluate", lambda s: route_or_fail(s, route(s) if not s.get("error") else "fail"), {"visual": "visual", "write": "write", "drop": "drop", "fail": "fail"})
    graph.add_edge("visual", END)
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
            done = await piece_graph.ainvoke(state, config={"recursion_limit": 14})
            result = done["result"]
        except Exception as exc:
            result = SlotResult(slot=state["slot"], status="failed", reason=f"{type(exc).__name__}: {exc}")
        return {"results": [result]}

    graph = StateGraph(WeekState)
    graph.add_node("worker", worker)
    graph.add_conditional_edges(START, dispatch, ["worker"])
    graph.add_edge("worker", END)
    return graph.compile(), lookup

