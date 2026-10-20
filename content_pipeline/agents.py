from __future__ import annotations

import json
from pathlib import Path
from langchain_core.messages import HumanMessage, SystemMessage
from .config import ROOT
from .llm import LocalModel
from .schemas import AtomicClaim, Draft, Evidence, MarketingDraft, Review, SemanticReport, Slot, TechThreadDraft, Vulnerability, WriterConfig
from .skills import EvidenceLookup


def instruction(relative: str) -> str:
    path = ROOT / relative
    return path.read_text()


def evidence_task_records(evidence: list[Evidence]) -> list[dict]:
    """Expose pinned authority to LLMs without legacy editorial summaries."""
    return [{"id": e.id, "url": e.url, "source_title": e.source_title,
        "source_type": e.source_type, "snapshot_sha256": e.snapshot_sha256,
        "source_quote": e.source_quote, "scope": e.scope} for e in evidence]


from .relation_integrity import DIRECT_CAUSAL, NORMATIVE_EVIDENCE, source_span_relation_hints


def build_evidence_plan(topic: Vulnerability, is_thread: bool) -> dict:
    """Construct an internal evidence plan mapping verified source points to content points."""
    plan_steps = []
    for ev in topic.evidence:
        quote = ev.source_quote or ""
        roles = source_span_relation_hints(quote)
        is_remediation = "RECOMMENDATION" in roles or NORMATIVE_EVIDENCE.search(quote) is not None
        has_causal = "CAUSAL_DESCRIPTION" in roles or DIRECT_CAUSAL.search(quote) is not None

        step = {
            "evidence_id": ev.id,
            "source_title": ev.source_title,
            "roles": roles,
            "allowed_relations": ["DIRECT_RECOMMENDATION", "CONTEXTUAL_SUPPORT"] if is_remediation else (
                ["DIRECT_CAUSAL_SUPPORT", "DIRECT_DESCRIPTIVE_SUPPORT", "CONTEXTUAL_SUPPORT"] if has_causal else
                ["DIRECT_DESCRIPTIVE_SUPPORT", "CONTEXTUAL_SUPPORT"]
            ),
            "prohibited_inferences": [
                "Do not invert remediation into root-cause claims without causal evidence",
                "Do not claim universal 100% prevention or absolute safety guarantees",
                "Do not invent unverified statistics, company clients, or external hacks",
            ]
        }
        plan_steps.append(step)

    if is_thread:
        return {
            "format": "technical_thread",
            "target_tweets": "5 to 6 ordered tweets forming a progression: hazard -> mechanism -> state risk -> consequence -> mitigation -> takeaway",
            "available_evidence_points": plan_steps,
            "instruction": "Each tweet must teach one distinct point grounded in available_evidence_points. Do not invent filler."
        }
    else:
        return {
            "format": "marketing_post",
            "pattern": "Action (Review...) -> grounded technical concern -> practical significance",
            "available_evidence_points": plan_steps,
            "instruction": "Write exactly one sentence as one tweet under 280 characters. Connect the review action to a grounded technical concern from the evidence."
        }


class ResearchAgent:
    def __init__(self, lookup: EvidenceLookup):
        self.lookup = lookup

    def run(self, slot: Slot, index: int) -> Vulnerability:
        return self.lookup.select(slot.focus, index)


class WriterAgent:
    def __init__(self, model: LocalModel, config: WriterConfig, brand_text: str):
        self.model = model
        self.config = config
        self.brand_text = brand_text

    async def run(self, slot: Slot, topic: Vulnerability, feedback: list[str] | None = None) -> tuple[Draft, dict]:
        guidance = instruction(self.config.instruction_file)
        evidence = evidence_task_records(topic.evidence)
        is_thread = self.config.max_tweets > 1
        plan = build_evidence_plan(topic, is_thread)
        task = {"slot": slot.model_dump(), "topic": topic.name,
            "brand_rules": self.brand_text, "evidence": evidence,
            "evidence_plan": plan,
            "revision_feedback": feedback or [], "task": "Create a Draft following the evidence_plan; source_quote is the primary factual authority. Every public sentence needs an exact-text claim mapping with supplied evidence IDs."}
        return await self.model.structured([SystemMessage(content=guidance), HumanMessage(content=json.dumps(task, ensure_ascii=False))], Draft)


class ReviewerAgent:
    def __init__(self, model: LocalModel, lookup: EvidenceLookup, brand_text: str):
        self.model = model
        self.lookup = lookup
        self.brand_text = brand_text

    async def run(self, draft: Draft, evidence: list[Evidence], errors: list[str], semantic: SemanticReport | None = None) -> tuple[Review, dict]:
        # The same evidence skill that Research uses validates the cited IDs here.
        missing = self.lookup.verify_ids(evidence, [id for claim in draft.claims for id in claim.evidence_ids])
        rubric = instruction("instructions/reviewer-rubric.md")
        semantic_brief = ({"verdicts": [{"claim_id": item.claim_id, "verdict": item.verdict,
            "supporting_spans": [span.model_dump() for span in item.supporting_spans],
            "context_windows": [window.model_dump() for window in item.context_windows],
            "initial_verdict": item.initial_pass.verdict if item.initial_pass else None,
            "skeptical_verdict": item.skeptical_pass.verdict if item.skeptical_pass else None,
            "claim_relations": item.claim_relations, "evidence_relation": item.evidence_relation,
            "relationship_verdict": item.relationship_verdict,
            "relation_integrity_passed": item.relation_integrity_passed,
            "relation_error": item.relation_error,
            **({"reason": item.reason} if item.verdict != "SUPPORTED" else {})}
            for item in semantic.verdicts]} if semantic else None)
        task = {"brand_voice_guidance": self.brand_text.split("```json", 1)[0].strip(),
            "evidence": evidence_task_records(evidence),
            "draft": draft.model_dump(), "deterministic_errors": errors + ([f"Unknown evidence IDs: {missing}"] if missing else []),
            "tweet_count": len(draft.tweets), "tweet_character_counts": [len(tweet) for tweet in draft.tweets],
            "tweet_array_semantics": "Each draft.tweets element is one independent rendered tweet; numbering is added only during CSV export.",
            "rendering_contract": {"one_array_item_is_one_tweet": True,
                "exporter_adds_thread_numbering": True, "numbering_inside_tweet_text_required": False,
                "line_breaks_inside_tweet_text_required": False},
            "semantic_report": semantic_brief,
            "task": "Score only the current draft. Return a concise Review. A rejection needs a current-draft defect and matching low score or mandatory gate; never override a hard or atomic gate."}
        usage_total: dict = {}
        for review_attempt in range(2):
            review, usage = await self.model.structured([SystemMessage(content=rubric), HumanMessage(content=json.dumps(task, ensure_ascii=False))], Review)
            for key in ("input_tokens", "output_tokens"):
                if usage.get(key) is not None:
                    usage_total[key] = usage_total.get(key, 0) + usage[key]
                else:
                    usage_total["usage_complete"] = False
            low_raw = [name for name, minimum in (("factual_support", 4), ("technical_correctness", 4), ("brand_voice", 3), ("clarity", 3), ("platform_format", 3), ("usefulness", 3)) if getattr(review, name) < minimum]
            all_atomic_supported = bool(semantic and semantic.verdicts and all(v.verdict == "SUPPORTED" for v in semantic.verdicts))
            if not review.approved and not low_raw and not errors and not missing and all_atomic_supported:
                if review_attempt:
                    raise ValueError("Reviewer returned approval=false with passing scores and no failed mandatory gate after one consistency retry")
                task["review_consistency_feedback"] = ("Previous Review had approved=false with every score at or above threshold and no failed mandatory gate. Each draft.tweets array element is already a separate X post; the exporter adds 1/N numbering. Missing line breaks or numbering inside an element cannot be a format defect. Reassess only this draft: approve if no specific defect exists, or lower the affected score and cite the exact current-draft text that causes it. Do not repeat speculative self-dialogue.")
                continue
            break
        by_id = {e.id: e.source_quote or "" for e in evidence}
        # Atomic semantic verification already checks every public clause against
        # pinned source spans. A Reviewer may omit its redundant quote fields; do
        # not turn that formatting omission into a factual rejection when the
        # independent semantic pass is complete. Reviewer scores and its own
        # adverse judgment still veto approval below.
        semantic_complete = bool(semantic and semantic.verdicts and
            all(item.verdict == "SUPPORTED" and item.supporting_spans for item in semantic.verdicts))
        support_errors = []
        for claim in draft.claims:
            assessments = [item for item in review.claim_support if item.claim_text == claim.text]
            valid = any(item.supported and item.evidence_id in claim.evidence_ids and
                len(item.evidence_quote.strip()) >= 12 and
                item.evidence_quote.casefold() in by_id.get(item.evidence_id, "").casefold()
                for item in assessments)
            if (assessments or not semantic_complete) and not valid:
                support_errors.append(f"No verified supporting excerpt for claim: {claim.text}")
        if support_errors:
            review.approved = False
            review.reasons = list(dict.fromkeys(review.reasons + support_errors))
        low_scores = [name for name, minimum in (("factual_support", 4), ("technical_correctness", 4), ("brand_voice", 3), ("clarity", 3), ("platform_format", 3), ("usefulness", 3)) if getattr(review, name) < minimum]
        semantic_errors = [f"Atomic claim {v.claim_id}: {v.verdict}: {v.reason}" for v in semantic.verdicts if v.verdict != "SUPPORTED"] if semantic else []
        if errors or missing or low_scores or semantic_errors:
            review.approved = False
            review.reasons = list(dict.fromkeys(review.reasons + errors + semantic_errors + ([f"Unknown evidence IDs: {missing}"] if missing else []) + ([f"Scores below rubric threshold: {low_scores}"] if low_scores else [])))
        if not review.approved and not review.reasons:
            review.reasons = ["Reviewer rejected the draft without a specific reason"]
        return review, usage_total


class VisualAgent:
    def run(self, slot: Slot, topic: str, draft: Draft, claims: list[AtomicClaim], evidence: list[Evidence], semantic: SemanticReport) -> str:
        if not draft.tweets or not claims or not evidence:
            raise ValueError("Visual specification requires accepted text, verified claims, and evidence")
        if len(semantic.verdicts) != len(claims) or any(v.verdict != "SUPPORTED" for v in semantic.verdicts):
            raise ValueError("Visual specification requires supported final atomic claims")
        guide = instruction("instructions/visual-agent.md")
        public_text = " ".join(draft.tweets)
        lower = public_text.casefold()
        if "reentr" in topic.casefold() and ("callback" in lower or "calls back" in lower or "reenter" in lower):
            diagram = "Calling contract → external contract → possible call back before the first invocation finishes; show state changes before the external call only when named in the accepted text."
            labels = "Calling contract; external contract; call back; first invocation."
        elif "withdraw" in topic.casefold() and ("authoriz" in lower or "access" in lower):
            diagram = "A withdrawal request crossing an authorization boundary before the transfer path; show allowed versus unauthorized caller routes."
            labels = "Caller; authorization check; withdrawal path."
        elif "oracle" in topic.casefold() and ("price" in lower or "oracle" in lower):
            diagram = "Price source feeding a contract decision through a validation boundary; add multiple feeds or TWAP only if named in the accepted text."
            labels = "Price source; validation boundary; contract decision."
        elif "call return" in topic.casefold() and "return" in lower:
            diagram = "A low-level call yielding a return value, followed by an explicit check of that value; do not imply an unstated return type."
            labels = "Low-level call; return value; check."
        elif "failed call" in topic.casefold() and ("own transaction" in lower or "separate transaction" in lower):
            diagram = "Separate recipient-initiated transaction lanes for individual external calls; depict the separation only, without an unstated failure outcome."
            labels = "External call; recipient; individual transaction."
        elif "failed call" in topic.casefold() and "fail" in lower:
            diagram = "A shared operation with one external dependency that can fail and block progress."
            labels = "Operation; external dependency; failure path."
        else:
            diagram = "Neutral contract review checkpoint; do not depict a specific exploit sequence unsupported by the accepted text."
            labels = "Researched risk; review checkpoint."
        takeaway = draft.tweets[-1].strip()
        references = ", ".join(sorted({id for verdict in semantic.verdicts for id in verdict.evidence_ids}))
        return (f"# Visual specification: {slot.id}\n\n"
            f"Status: written specification, not rendered media.\nContent type: {slot.type}.\nMain subject: {topic}.\n"
            f"Communication objective: reinforce the accepted takeaway: {takeaway}\n"
            f"Verified claim references: {references}.\n"
            f"Technical diagram: {diagram}\nLabels: {labels}\n"
            "Layout and composition: 16:9 landscape; headline upper left, diagram central, takeaway lower right, generous whitespace.\n"
            "Visual hierarchy: topic title, evidence-supported interaction, concise review action.\n"
            "Brand and typography: deep navy background, teal accents, white high-contrast labels, restrained sans-serif type.\n"
            f"Design policy (editable):\n{guide}\n")


class EvidenceFirstWriterAgent:
    def __init__(
        self,
        model: LocalModel,
        content_type: str | None = None,
        role_instruction_file: str | None = None,
        instruction_text: str | None = None,
    ):
        self.model = model
        self.content_type = content_type
        self.role_instruction_file = role_instruction_file
        self._instruction_text = instruction_text

    @property
    def system_prompt(self) -> str:
        if self._instruction_text is not None:
            return self._instruction_text
        base_rules = instruction("instructions/evidence-first-writer.md")
        role_file = self.role_instruction_file
        if not role_file and self.content_type:
            if self.content_type == "tech-thread":
                role_file = "instructions/tech-thread.md"
            elif self.content_type == "marketing-post":
                role_file = "instructions/marketing-post.md"
        if role_file:
            role_text = instruction(role_file)
            return f"{role_text}\n\n---\n\n{base_rules}"
        return base_rules

    async def run(
        self,
        plan,
        catalog,
        targeted_feedback: list[dict] | None = None,
        previous_tweets: list[str] | None = None,
    ) -> tuple[Draft, dict]:
        prop_map = {p.id: p for p in catalog.propositions} if catalog and hasattr(catalog, "propositions") else {}
        rel_map = {r.id: r for r in catalog.relations} if catalog and hasattr(catalog, "relations") else {}
        is_marketing = (plan.content_type == "marketing-post")
        exact_count = 1 if is_marketing else len(plan.units)
        draft_schema = (
            MarketingDraft
            if is_marketing
            else (TechThreadDraft if plan.content_type == "tech-thread" else Draft)
        )

        if is_marketing:
            count_inst = (
                "CRITICAL: The 'tweets' array in your output MUST contain EXACTLY 1 string (strictly under 250 characters total, platform limit is 280). "
                "Multiple sentences inside this single tweet are permitted. "
                "Do NOT produce multiple tweets or separate array items. Keep the text concise (aim for 180-230 characters) so it never exceeds the platform character limit."
            )
        else:
            count_inst = (
                f"CRITICAL: The 'tweets' array in your output MUST contain EXACTLY {exact_count} strings "
                "(one tweet corresponding to each planned unit, strictly 5 to 10 tweets total)."
            )

        evidence_payload = []
        if hasattr(plan, "evidence_items") and plan.evidence_items:
            for ev in plan.evidence_items:
                evidence_payload.append({
                    "id": getattr(ev, "id", str(ev)),
                    "url": getattr(ev, "url", ""),
                    "excerpt": getattr(ev, "excerpt", getattr(ev, "source_quote", "")),
                })

        plan_prompt_payload = {
            "slot_id": plan.slot_id,
            "topic_id": plan.topic_id,
            "content_type": plan.content_type,
            "exact_required_tweet_count": exact_count,
            "count_instruction": count_inst,
            "verified_evidence": evidence_payload,
            "units": [
                {
                    "unit_id": u.id,
                    "role": u.role,
                    "required_qualifiers": u.required_qualifiers,
                    "guidance": u.guidance,
                    "canonical_propositions": [prop_map[pid].canonical_text for pid in u.proposition_ids if pid in prop_map],
                    "approved_relations": [
                        f"{rel_map[rid].source_id} --({rel_map[rid].relation_type})--> {rel_map[rid].target_id}"
                        for rid in u.relation_ids if rid in rel_map
                    ],
                }
                for u in plan.units
            ],
        }

        if targeted_feedback:
            is_marketing_count_violation = is_marketing and any(
                fb.get("verdict") == "FORMAT_VIOLATION" or "COUNT_MISMATCH" in str(fb.get("unit_id", ""))
                for fb in targeted_feedback
            )
            count_in_draft = len(previous_tweets) if previous_tweets else 2
            if is_marketing_count_violation:
                revision_instruction = (
                    f"Marketing posts must contain exactly one tweet. Your draft contained {count_in_draft}. "
                    "Rewrite the content as one coherent, source-grounded tweet within the platform character limit. "
                    "Preserve only approved propositions and relations."
                )
            else:
                revision_instruction = (
                    f"The previous draft had {len(targeted_feedback)} issue(s). "
                    f"You MUST produce exactly {exact_count} tweet(s) total in the `tweets` list. "
                    "Fix the failing units according to the feedback below, while keeping conforming units stable."
                )
            prompt_content = {
                "mode": "REVISION",
                "instructions": revision_instruction,
                "plan": plan_prompt_payload,
                "previous_tweets": previous_tweets or [],
                "targeted_feedback": targeted_feedback,
            }
        else:
            prompt_content = plan_prompt_payload

        draft, usage = await self.model.structured(
            [
                SystemMessage(content=self.system_prompt),
                HumanMessage(content=json.dumps(prompt_content, ensure_ascii=False)),
            ],
            draft_schema,
        )
        if not isinstance(draft, Draft):
            draft = draft_schema.model_validate(draft)
        return draft, usage

