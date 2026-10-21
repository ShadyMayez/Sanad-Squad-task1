"""Evidence-first content planning and sufficiency preflight.

Constructs structured EvidenceFirstPlan specifications directly from
verified propositions and typed relations in the catalog before natural language generation.
"""
from __future__ import annotations

import hashlib
from typing import Literal, Any
from pydantic import BaseModel, Field

from .proposition_catalog import PropositionCatalog, VerifiedProposition, TypedRelation

RealizationMode = Literal["MODE_A_STRUCTURED", "MODE_B_NATURAL", "MODE_C_CREATIVE"]

UnitRole = Literal[
    "HOOK",
    "DEFINITION",
    "MECHANISM",
    "CONSEQUENCE",
    "RECOMMENDATION",
    "MITIGATION",
    "SUMMARY"
]


class ContentUnit(BaseModel):
    id: str
    role: UnitRole
    proposition_ids: list[str] = Field(default_factory=list)
    relation_ids: list[str] = Field(default_factory=list)
    required_qualifiers: list[str] = Field(default_factory=list)
    realization_mode: RealizationMode = "MODE_B_NATURAL"
    max_chars: int = 280
    guidance: str = ""
    source_evidence_ids: list[str] = Field(default_factory=list)
    mandatory_url: str | None = None


class EvidenceFirstPlan(BaseModel):
    slot_id: str
    topic_id: str
    content_type: str
    source_strategy: str = "catalog"  # "catalog", "web_research", "external_technical"
    catalog_version: str = "2.0.0"
    policy_id: str = "security_audit_firm"
    policy_version: str = "1.0.0"
    policy_hash: str | None = None
    authorization_mode: str = "pilot_evaluation"  # "pilot_evaluation" or "publication_eligible"
    units: list[ContentUnit]
    evidence_items: list[Any] = Field(default_factory=list)
    character_budget: dict[str, Any] | None = None
    mandatory_url: str | None = None
    replan_notes: list[str] = Field(default_factory=list)
    plan_hash: str | None = None

    def compute_plan_hash(self) -> str:
        payload = self.model_dump_json(exclude={"plan_hash"})
        return hashlib.sha256(payload.encode("utf-8")).hexdigest()

    def validate_plan_references(
        self,
        catalog: PropositionCatalog,
        active_policy: Any | None = None,
        active_policy_version: str | None = None,
        authorization_mode: str | None = None,
        evaluation_mode: bool | None = None,
    ) -> list[str]:
        errors: list[str] = []

        # Handle runtime research plans (marketing web research and external technical research)
        if self.source_strategy in {"web_research", "external_technical"}:
            if self.content_type == "marketing-post" and len(self.units) != 1:
                errors.append(f"Marketing plan must contain exactly 1 unit, got {len(self.units)}")
            elif self.content_type == "tech-thread" and not (5 <= len(self.units) <= 10):
                errors.append(f"Technical plan must contain 5-10 units, got {len(self.units)}")
            valid_ev_ids = {e.id if hasattr(e, "id") else e.get("id") for e in self.evidence_items}
            for u in self.units:
                for eid in u.source_evidence_ids:
                    if eid not in valid_ev_ids:
                        errors.append(f"Unit {u.id} references unknown evidence ID '{eid}'")
            return errors

        # 1. Catalog version authority
        if self.catalog_version != catalog.catalog_version:
            errors.append(
                f"Plan catalog_version {self.catalog_version!r} does not match catalog version {catalog.catalog_version!r}"
            )

        # 2. Active policy authority
        expected_policy_version = None
        expected_policy_id = None
        if active_policy is not None:
            expected_policy_version = getattr(active_policy, "policy_version", None)
            expected_policy_id = getattr(active_policy, "policy_id", getattr(active_policy, "business_id", None))
            if hasattr(active_policy, "compute_hash") and self.policy_hash:
                active_hash = active_policy.compute_hash()
                if self.policy_hash != active_hash:
                    errors.append(f"Plan policy_hash {self.policy_hash[:12]}... does not match active policy hash {active_hash[:12]}...")
        elif active_policy_version is not None:
            expected_policy_version = active_policy_version
        else:
            # Baseline policy version
            expected_policy_version = "1.0.0"

        if expected_policy_version is not None and self.policy_version != expected_policy_version:
            errors.append(
                f"Plan policy_version {self.policy_version!r} does not match active policy version {expected_policy_version!r}"
            )
        if expected_policy_id is not None and self.policy_id != expected_policy_id:
            errors.append(
                f"Plan policy_id {self.policy_id!r} does not match active policy id {expected_policy_id!r}"
            )

        # 3. Authorization mode & status permissions
        mode = authorization_mode or self.authorization_mode
        if evaluation_mode is not None:
            is_eval = evaluation_mode
        else:
            is_eval = (mode == "pilot_evaluation")

        allowed_statuses = {"APPROVED", "REVIEWED_FOR_PILOT"} if is_eval else {"APPROVED"}

        prop_map = {p.id: p for p in catalog.propositions}
        rel_map = {r.id: r for r in catalog.relations}

        # Approved topic bridges (e.g. SWC-105 includes OZ-OWNABLE; SCWE-028 includes OWASP-SC03)
        allowed_topics_for_plan = {self.topic_id}
        if self.topic_id == "SWC-105":
            allowed_topics_for_plan.add("OZ-OWNABLE")
        if self.topic_id == "SCWE-028":
            allowed_topics_for_plan.add("OWASP-SC03")

        all_plan_props = {pid for u in self.units for pid in u.proposition_ids}

        # 4. Check propositions and units
        for u in self.units:
            for pid in u.proposition_ids:
                if pid not in prop_map:
                    errors.append(f"Unit {u.id} references non-existent proposition: {pid}")
                else:
                    p = prop_map[pid]
                    if p.topic_id not in allowed_topics_for_plan:
                        errors.append(
                            f"Unit {u.id} proposition {pid} belongs to topic {p.topic_id!r}, "
                            f"expected plan topic {self.topic_id!r}"
                        )
                    if p.status not in allowed_statuses:
                        errors.append(
                            f"Unit {u.id} proposition {pid} status {p.status!r} not in allowed statuses {allowed_statuses}"
                        )

            # 5. Check relations
            for rid in u.relation_ids:
                if rid not in rel_map:
                    errors.append(f"Unit {u.id} references non-existent relation: {rid}")
                else:
                    rel = rel_map[rid]
                    if rel.source_id not in all_plan_props or rel.target_id not in all_plan_props:
                        errors.append(
                            f"Unit {u.id} references relation {rid} whose endpoints "
                            f"({rel.source_id}, {rel.target_id}) are not both present in the plan"
                        )
                    if rel.source_id not in u.proposition_ids and rel.target_id not in u.proposition_ids:
                        errors.append(
                            f"Unit {u.id} references relation {rid} but contains neither "
                            f"source {rel.source_id} nor target {rel.target_id}"
                        )
                    if rel.status not in allowed_statuses:
                        errors.append(
                            f"Unit {u.id} relation {rid} status {rel.status!r} not in allowed statuses {allowed_statuses}"
                        )

        return errors


class PreflightResult(BaseModel):
    is_sufficient: bool
    available_propositions: int
    available_relations: int
    reason: str


def check_evidence_sufficiency(
    topic_id: str,
    content_type: str,
    catalog: PropositionCatalog,
    min_tech_thread_props: int = 4,
    min_marketing_props: int = 2,
) -> PreflightResult:
    """Assess whether a topic has adequate distinct factual material before invoking Writer."""
    props = catalog.get_propositions_for_topic(topic_id)
    rels = catalog.get_relations_for_topic(topic_id)

    kinds = {p.kind for p in props}
    prop_count = len(props)

    if content_type == "tech-thread":
        if prop_count < min_tech_thread_props:
            return PreflightResult(
                is_sufficient=False,
                available_propositions=prop_count,
                available_relations=len(rels),
                reason=f"Insufficient distinct propositions for 5-7 tweet technical thread: found {prop_count}, required at least {min_tech_thread_props}."
            )
        # Require both mechanism/fact and recommendation/mitigation
        has_mechanisms = any(k in {"MECHANISM", "CONSEQUENCE", "FACT"} for k in kinds)
        has_mitigations = any(k in {"RECOMMENDATION", "LIMITATION"} for k in kinds)
        if not (has_mechanisms and has_mitigations):
            return PreflightResult(
                is_sufficient=False,
                available_propositions=prop_count,
                available_relations=len(rels),
                reason="Insufficient structural diversity: must have both causal/vulnerability mechanisms and mitigation recommendations."
            )
    else:  # marketing_post
        if prop_count < min_marketing_props:
            return PreflightResult(
                is_sufficient=False,
                available_propositions=prop_count,
                available_relations=len(rels),
                reason=f"Insufficient distinct propositions for marketing post: found {prop_count}, required at least {min_marketing_props}."
            )

    return PreflightResult(
        is_sufficient=True,
        available_propositions=prop_count,
        available_relations=len(rels),
        reason=f"Evidence sufficient for {content_type} ({prop_count} propositions, {len(rels)} relations)."
    )


def build_evidence_first_plan(
    slot_id: str,
    topic_id: str,
    content_type: str,
    catalog: PropositionCatalog,
    policy: Any | None = None,
    authorization_mode: str = "pilot_evaluation",
) -> EvidenceFirstPlan:
    """Construct an EvidenceFirstPlan mapping verified propositions into ordered content units."""
    props = catalog.get_propositions_for_topic(topic_id)
    rels = catalog.get_relations_for_topic(topic_id)
    prop_by_id = {p.id: p for p in props}
    rel_by_id = {r.id: r for r in rels}

    units: list[ContentUnit] = []

    if content_type == "marketing-post":
        # Marketing posts combine a hazard mechanism with a recommended review action
        mech_props = [p for p in props if p.kind in {"MECHANISM", "CONSEQUENCE", "FACT"}]
        rec_props = [p for p in props if p.kind == "RECOMMENDATION"]
        action_rels = [r for r in rels if r.relation_type in {"ACTION_RATIONALE", "MITIGATES"}]

        selected_props = []
        selected_rels = []
        qualifiers = []

        if mech_props and rec_props:
            m = mech_props[0]
            r = rec_props[0]
            selected_props.extend([m.id, r.id])
            if "solidity_version" in m.applicability:
                qualifiers.append(m.applicability["solidity_version"])

            # If there is a consequence proposition bridging the mechanism to the recommendation, include it
            conseq = next((p for p in mech_props if p.kind == "CONSEQUENCE" and p.id != m.id), None)
            if conseq and conseq.id not in selected_props:
                selected_props.append(conseq.id)
                if "solidity_version" in conseq.applicability and conseq.applicability["solidity_version"] not in qualifiers:
                    qualifiers.append(conseq.applicability["solidity_version"])

            # Select all approved relations connecting the selected propositions
            selected_rels = [
                rel.id for rel in rels
                if rel.source_id in selected_props and rel.target_id in selected_props
            ]
        elif props:
            selected_props = [p.id for p in props[:2]]

        if topic_id == "SWC-104":
            guidance = (
                "Write EXACTLY ONE single tweet under 280 characters. "
                "Pair the low-level call return hazard with an actionable review invitation to the reader. "
                "Scope checking return values strictly to LOW-LEVEL calls (methods like .call()). "
                "Do NOT claim this applies to 'all external calls'. "
                "Example pattern: 'Unchecked low-level calls can fail while execution continues, causing unexpected behavior. Review low-level call sites and check their return values to handle failures correctly.'"
            )
        elif topic_id == "SWC-113":
            guidance = (
                "Write EXACTLY ONE single tweet under 280 characters. "
                "Pair the denial-of-service hazard from failed calls with an actionable recommendation to isolate recipient-initiated calls. "
                "State the purpose accurately: to minimize damage from failures or reduce DoS impact so failed calls do not block other operations. "
                "Do NOT assert that isolation prevents execution from continuing on failure (that is an unchecked return value concept), and do NOT assert fund draining. "
                "Example pattern: 'Failed external calls can cause denial of service. To reduce their impact, isolate external calls in separate, recipient-initiated transactions instead of batching them together.'"
            )
        elif topic_id == "SWC-105":
            guidance = (
                "Write EXACTLY ONE single tweet under 280 characters. "
                "Pair the unprotected withdrawal hazard with an actionable access control recommendation. "
                "Example pattern: 'Missing access controls allow malicious actors to withdraw Ether from contract accounts. Implement access controls so only authorized parties can initiate withdrawals to reduce this risk.'"
            )
        else:
            guidance = (
                "Write EXACTLY ONE single tweet under 280 characters. "
                "You MUST include a clear, actionable security recommendation or review invitation to the reader. "
                "Strictly preserve approved outcomes and scope from assigned propositions. "
                "Never invent guarantees (use 'to reduce this risk' or 'to mitigate this risk' rather than absolute prevention guarantees like 'to prevent these outcomes'), universal scope expansions (such as 'all external calls'), or unlicensed instrumental outcomes (such as 'prevents execution from continuing on failure')."
            )

        units.append(ContentUnit(
            id=f"{slot_id}_u1",
            role="RECOMMENDATION",
            proposition_ids=selected_props,
            relation_ids=selected_rels,
            required_qualifiers=qualifiers,
            realization_mode="MODE_B_NATURAL",
            max_chars=280,
            guidance=guidance,
        ))

    else:
        # Technical thread: 5 to 6 ordered units
        # Unit 1: Hook & Core Hazard
        # Unit 2: Detailed Mechanism & Precondition
        # Unit 3: Undesirable Interaction / Consequence
        # Unit 4: Architecture Mitigation (CEI, Isolation, TWAP, etc.)
        # Unit 5: Tooling / Implementation Guard (ReentrancyGuard, Ownable, etc.)
        # Unit 6: Summary / Security Takeaway
        mech_props = [p for p in props if p.kind in {"MECHANISM", "FACT", "DEFINITION"}]
        conseq_props = [p for p in props if p.kind == "CONSEQUENCE"]
        rec_props = [p for p in props if p.kind == "RECOMMENDATION"]

        unit_idx = 1
        # U1: Hook / Overview
        if mech_props:
            p0 = mech_props[0]
            quals = [p0.applicability["solidity_version"]] if "solidity_version" in p0.applicability else []
            units.append(ContentUnit(
                id=f"{slot_id}_u{unit_idx}",
                role="HOOK",
                proposition_ids=[p0.id],
                required_qualifiers=quals,
                realization_mode="MODE_B_NATURAL",
                max_chars=280,
                guidance="Introduce the vulnerability concept accurately without adding unevidenced characterizations like 'the core mechanism' or 'the defining risk'."
            ))
            unit_idx += 1

        # U2: Execution Mechanism
        if len(mech_props) > 1:
            p1 = mech_props[1]
            quals = [p1.applicability["solidity_version"]] if "solidity_version" in p1.applicability else []
            enables_rel = next((r.id for r in rels if r.relation_type == "ENABLES" and (r.source_id == p1.id or r.target_id == p1.id)), None)

            # If there is no separate consequence proposition, allocate the third mechanism proposition to U3
            if not conseq_props and len(mech_props) > 2:
                unit_props = [p1.id]
                rel_ids_u2 = []
            else:
                unit_props = [p1.id]
                rel_ids_u2 = [enables_rel] if enables_rel else []
                if enables_rel:
                    rel_obj = rel_by_id[enables_rel]
                    other_id = rel_obj.target_id if rel_obj.source_id == p1.id else rel_obj.source_id
                    if other_id in prop_by_id and other_id not in unit_props:
                        unit_props.append(other_id)
                    for ep_id in (rel_obj.source_id, rel_obj.target_id):
                        if ep_id in prop_by_id and "solidity_version" in prop_by_id[ep_id].applicability:
                            v_qual = prop_by_id[ep_id].applicability["solidity_version"]
                            if v_qual not in quals:
                                quals.append(v_qual)

            guidance_parts = ["Explain the technical execution path clearly based strictly on the assigned proposition."]
            if quals:
                guidance_parts.append(f"State applicable version boundary ({', '.join(quals)}).")
            has_sometimes = any("sometimes" in prop_by_id[pid].canonical_text.lower() for pid in unit_props if pid in prop_by_id)
            if has_sometimes:
                guidance_parts.append("Preserve possibility modality: state that bugs are sometimes caused; do not escalate to often, typically, or always.")

            units.append(ContentUnit(
                id=f"{slot_id}_u{unit_idx}",
                role="MECHANISM",
                proposition_ids=unit_props,
                relation_ids=rel_ids_u2,
                required_qualifiers=quals,
                realization_mode="MODE_B_NATURAL",
                max_chars=280,
                guidance=" ".join(guidance_parts)
            ))
            unit_idx += 1

        # U3: Consequence / Risk or Specific Trigger Mechanism
        if conseq_props:
            c0 = conseq_props[0]
            lead_rel = next((r.id for r in rels if r.relation_type == "CAN_LEAD_TO" and r.target_id == c0.id), None)
            units.append(ContentUnit(
                id=f"{slot_id}_u{unit_idx}",
                role="CONSEQUENCE",
                proposition_ids=[c0.id],
                relation_ids=[lead_rel] if lead_rel else [],
                realization_mode="MODE_B_NATURAL",
                max_chars=280,
                guidance="Describe the potential adverse impact (e.g. unauthorized actions or loss of funds) strictly adhering to the approved proposition. Do NOT add unapproved severity adjectives like 'significant' or 'complete subversion'."
            ))
            unit_idx += 1
        elif len(mech_props) > 2:
            p2 = mech_props[2]
            quals_p2 = [p2.applicability["solidity_version"]] if "solidity_version" in p2.applicability else []
            lead_rel2 = next((r.id for r in rels if r.relation_type in {"CAN_LEAD_TO", "ENABLES"} and (r.source_id == p2.id or r.target_id == p2.id)), None)
            guidance_parts2 = ["Explain the specific trigger or compiler condition based strictly on the assigned proposition."]
            if quals_p2:
                guidance_parts2.append(f"State applicable version boundary ({', '.join(quals_p2)}).")
            units.append(ContentUnit(
                id=f"{slot_id}_u{unit_idx}",
                role="MECHANISM",
                proposition_ids=[p2.id],
                relation_ids=[lead_rel2] if lead_rel2 else [],
                required_qualifiers=quals_p2,
                realization_mode="MODE_B_NATURAL",
                max_chars=280,
                guidance=" ".join(guidance_parts2)
            ))
            unit_idx += 1

        # U4: Primary Mitigation
        if rec_props:
            r0 = rec_props[0]
            mit_rel = next((r.id for r in rels if r.relation_type == "MITIGATES" and r.source_id == r0.id), None)
            guidance = (
                "Explain recommended defensive patterns (e.g. state-updating sequence or access controls). "
                "Use complete, natural, grammatically correct English: ensure access controls allow only authorized parties to initiate withdrawals, according to contract requirements. "
                "Never write ungrammatical blends like 'trigger only when authorized parties or as specified'. "
                "Do NOT claim this defense is 'the primary defense' or 'most important' unless explicitly specified."
            )
            units.append(ContentUnit(
                id=f"{slot_id}_u{unit_idx}",
                role="MITIGATION",
                proposition_ids=[r0.id],
                relation_ids=[mit_rel] if mit_rel else [],
                realization_mode="MODE_B_NATURAL",
                max_chars=280,
                guidance=guidance,
            ))
            unit_idx += 1

        # U5: Secondary Defense / Implementation Guard
        if len(rec_props) > 1:
            r1 = rec_props[1]
            mit_rel2 = next((r.id for r in rels if r.relation_type == "MITIGATES" and r.source_id == r1.id), None)
            units.append(ContentUnit(
                id=f"{slot_id}_u{unit_idx}",
                role="RECOMMENDATION",
                proposition_ids=[r1.id],
                relation_ids=[mit_rel2] if mit_rel2 else [],
                realization_mode="MODE_B_NATURAL",
                max_chars=280,
                guidance="Explain complementary protections (e.g. locks or modules)."
            ))
            unit_idx += 1

        # U6: Actionable Summary
        if len(units) < 5 or (len(rec_props) > 2 and len(units) < 6):
            summary_prop = rec_props[2] if len(rec_props) > 2 else (conseq_props[0] if conseq_props else props[0])
            action_rel = next((r.id for r in rels if r.relation_type == "ACTION_RATIONALE"), None)
            units.append(ContentUnit(
                id=f"{slot_id}_u{unit_idx}",
                role="SUMMARY",
                proposition_ids=[summary_prop.id],
                relation_ids=[action_rel] if action_rel else [],
                realization_mode="MODE_B_NATURAL",
                max_chars=280,
                guidance="Synthesize the audit takeaway and review advice."
            ))

    pol_ver = getattr(policy, "policy_version", "1.0.0") if policy else "1.0.0"
    pol_id = getattr(policy, "policy_id", getattr(policy, "business_id", "security_audit_firm")) if policy else "security_audit_firm"
    pol_hash = policy.compute_hash() if policy and hasattr(policy, "compute_hash") else None

    plan = EvidenceFirstPlan(
        slot_id=slot_id,
        topic_id=topic_id,
        content_type=content_type,
        catalog_version=catalog.catalog_version,
        policy_id=pol_id,
        policy_version=pol_ver,
        policy_hash=pol_hash,
        authorization_mode=authorization_mode,
        units=units,
    )
    plan.plan_hash = plan.compute_plan_hash()
    return plan


def build_marketing_evidence_plan(
    slot_id: str,
    service_line: str,
    marketing_format: str | None = None,
    evidence: list[Any] | None = None,
    evidence_items: list[Any] | None = None,
    format_spec: Any | None = None,
    has_cta: bool = False,
    contact_config: Any | None = None,
    guidance: str = "",
    policy: Any = None,
    authorization_mode: str = "pilot_evaluation",
) -> EvidenceFirstPlan:
    """Build an EvidenceFirstPlan for a marketing-post grounded in retrieved runtime evidence."""
    ev_list = evidence if evidence is not None else (evidence_items or [])
    fmt_str = marketing_format
    if not fmt_str and format_spec is not None:
        if hasattr(format_spec, "format_name"):
            fn = format_spec.format_name
            fmt_str = fn.value if hasattr(fn, "value") else str(fn)
        elif hasattr(format_spec, "format"):
            fmt_str = format_spec.format.value if hasattr(format_spec.format, "value") else str(format_spec.format)
        elif hasattr(format_spec, "name"):
            fmt_str = format_spec.name
        else:
            fmt_str = str(format_spec)
    fmt_str = fmt_str or "short-tip"

    ev_ids = [str(getattr(e, "id", None) or (e.get("id") or e.get("source_id") if isinstance(e, dict) else str(e))) for e in ev_list]
    first_ev = ev_list[0] if ev_list else None
    excerpt = getattr(first_ev, "excerpt", "") if first_ev else ""
    ev_url = getattr(first_ev, "url", "") if first_ev else ""

    # Pre-calculate approved CTA if operational
    approved_cta_str = None
    if has_cta and contact_config and hasattr(contact_config, "is_operational") and contact_config.is_operational():
        from .contact_config import build_contextual_cta
        approved_cta_str = build_contextual_cta(service_line, contact_config)

    # Character Budgeting and Replanning (Pre-generation)
    from .character_budget import replan_marketing_slot_for_budget
    final_fmt, final_url, budget, replan_notes = replan_marketing_slot_for_budget(
        service_line=service_line,
        format_name=fmt_str,
        evidence_items=ev_list,
        approved_cta=approved_cta_str,
        safety_margin=20,
    )

    if budget.approved_cta:
        cta_instruction = (
            f"Include this exact company-approved contact CTA at the end of the tweet: '{budget.approved_cta}'. "
            f"The body copy must leave room so the entire tweet including CTA is strictly within 280 characters."
        )
    elif has_cta:
        cta_instruction = (
            "CTA eligibility is reserved for this slot, but company contact details are not yet approved by project owner. "
            "Do NOT include any email, phone, or unapproved commercial CTA (e.g. frank@sanadsquad.com). Focus strictly on educational observation."
        )
    else:
        cta_instruction = "Do NOT include commercial CTAs, email addresses, or phone numbers (e.g. frank@sanadsquad.com); focus purely on educational observation."

    format_specific_guidance = ""
    if final_fmt == "news-reaction":
        format_specific_guidance = (
            f"NEWS REACTION FORMAT:\n"
            f"1. Name the specific advisory or news event identified in the evidence.\n"
            f"2. Provide one clear security takeaway for engineering teams.\n"
            f"3. MANDATORY URL: You MUST include the exact source link: '{final_url}'.\n"
        )
    elif final_fmt == "learning-resource":
        format_specific_guidance = (
            f"LEARNING RESOURCE FORMAT (Strictly 1–2 concise sentences):\n"
            f"1. State the core specification mechanic in ONE compact sentence (under 120 characters).\n"
            f"2. Explain SanadSquad's official service alignment concisely.\n"
            f"3. MANDATORY URL: You MUST include the exact source link preceded by 'Review the spec:': 'Review the spec: {final_url}'.\n"
            f"4. Attribution Rule: The URL must belong to the exact publisher/organization cited in the tweet.\n"
            f"5. COMPACT PATTERN: '<Spec/Org> defines <mechanic>. SanadSquad builds <service feature>. Review the spec: {final_url}'\n"
            f"Note: If discussing x402, distinguish HTTP 402 signaling from optional facilitator verification and settlement.\n"
        )
    elif final_fmt == "differentiation":
        format_specific_guidance = (
            "DIFFERENTIATION FORMAT:\n"
            "1. Highlight the gap between contract-only audits and connected off-chain/agentic infrastructure risks.\n"
            "2. State SanadSquad's specialized scope without claiming to secure the entire connected stack.\n"
            "3. Strictly NO links for this format.\n"
        )
    else:
        format_specific_guidance = (
            "SHORT TIP FORMAT:\n"
            "1. Deliver one sharp, practical security observation grounded in the evidence.\n"
            "2. Strictly NO links for this format.\n"
        )

    service_specific_guidance = ""
    sl_clean = service_line.lower().strip()
    if "tool" in sl_clean or "agentic-security" in sl_clean:
        service_specific_guidance = (
            "SERVICE RELEVANCE (Agentic security tooling):\n"
            "- Meaningfully explain SanadSquad's official agentic security tooling: custom security detectors, automated PR reviewers, or real-time monitoring agents.\n"
            "- If citing the OWASP Agent Control Standard (ACS), the mandatory URL MUST be 'https://genai.owasp.org/resource/agent-control-standard-acs/'. Never cite Simon Willison's blog as an OWASP standard.\n"
            "- If citing Simon Willison, attribute it directly as his personal research blog. Never refer to it as 'the spec' or an OWASP standard.\n"
            "- Do NOT claim tool execution boundaries universally 'prevent prompt injection' (they restrict unauthorized actions and mitigate exploit blast radius).\n"
        )
    elif "consulting" in sl_clean:
        solana_note = ""
        if "solana" in excerpt.lower():
            solana_note = "- For Solana upgrade authority, explain that the keyholder centralization risk requires pre-deployment architecture review and multi-sig governance design; do NOT describe it as enabling 'unauthorized' changes or bypassing all verification.\n"
        service_specific_guidance = (
            "SERVICE RELEVANCE (Security consulting):\n"
            "- Meaningfully connect observations to SanadSquad's official security consulting service: early architecture design review before code is written, pre-implementation threat modeling, governance design, or ongoing development review.\n"
            f"{solana_note}"
        )
    elif "pentest" in sl_clean or "penetration" in sl_clean:
        service_specific_guidance = (
            "SERVICE RELEVANCE (Penetration testing):\n"
            "- Focus on the realistic off-chain attack surface: dApp backend APIs, RPC gateways, relayer infrastructure, and CI/CD pipelines.\n"
            "- Preserve the correct BOLA explanation (object-level authorization failure vs authentication/login) and explain SanadSquad's testing scope concisely in under 240 characters.\n"
        )
    elif "audit" in sl_clean or "blockchain" in sl_clean or "web3" in sl_clean:
        if "4626" in excerpt.lower() or "vault" in excerpt.lower():
            service_specific_guidance = (
                "SERVICE RELEVANCE (Blockchain security audits):\n"
                "- State the ERC-4626 empty vault inflation risk and SanadSquad's invariant accounting review concisely in 1–2 short sentences (target under 230 characters total).\n"
                "- Connect vault share pricing and rounding defenses to smart contract audits, accounting review, and invariant analysis.\n"
                "- Do NOT claim every ERC-4626 vault is vulnerable or that mitigations eliminate all risk.\n"
            )
        else:
            service_specific_guidance = (
                "SERVICE RELEVANCE (Blockchain security audits):\n"
                "- Clarify that verified builds establish source-to-deployment correspondence (bytecode matches Git commit) but NOT application security or freedom from logic flaws.\n"
                "- An upgrade alters the deployed executable and calls for verification of the new version and continuous invariant audits; do NOT imply that upgrades automatically bypass all verification.\n"
                "- Audits review point-in-time logic and known vulnerability patterns; do NOT claim audits prove code correctness.\n"
            )
    elif "payment" in sl_clean:
        service_specific_guidance = (
            "SERVICE RELEVANCE (Agentic payments):\n"
            "- Distinguish HTTP 402 payment signaling from optional facilitator-based verification and settlement.\n"
            "- Do NOT imply that all x402 deployments require a third-party facilitator; direct peer-to-peer settlement is supported. Canonical upstream spec: https://github.com/x402-foundation/x402.\n"
            "- Represent payment agent architecture, tool authorization limits, or replay protection.\n"
        )

    # -------------------------------------------------------------------------
    # Structured Editorial Brief Integration (B01–B10)
    # -------------------------------------------------------------------------
    brief_id = "B01"
    brief_data = {
        "audience": "Protocol engineering teams",
        "technical_problem": "Addressing critical protocol and infrastructure risks before exploitation.",
        "editorial_angle": "Grounding in verified specification mechanics and practical security review.",
    }

    if "audit" in sl_clean or "blockchain" in sl_clean or "web3" in sl_clean:
        if "4626" in excerpt.lower() or "vault" in excerpt.lower():
            brief_id = "B03"
            brief_data = {
                "audience": "DeFi vault engineers",
                "technical_problem": "An empty vault can expose share-price inflation attacks; what defenses are needed?",
                "editorial_angle": "ERC-4626 vault share price manipulation and virtual offset decimal mitigation tradeoffs.",
            }
        elif final_fmt in {"differentiation", "service-overview"} or "proxy" in excerpt.lower() or "deploy" in excerpt.lower():
            brief_id = "B02"
            brief_data = {
                "audience": "Protocol governance leads",
                "technical_problem": "Who can replace code after an audit? Upgrade authority is a control surface.",
                "editorial_angle": "Audit scope must cover both active logic and upgrade authority keys stored in ProgramData or proxy admin accounts.",
            }
        else:
            brief_id = "B01"
            brief_data = {
                "audience": "Solana teams",
                "technical_problem": "A verified build answers source identity, not whether logic has vulnerabilities.",
                "editorial_angle": "Bytecode correspondence vs application security: verified builds match Git commits, but audits check logic flaws and invariant preservation.",
            }
    elif "pentest" in sl_clean or "penetration" in sl_clean:
        if final_fmt in {"differentiation", "service-overview"} or "0x11-t10" in (final_url or "") or "function" in excerpt.lower():
            brief_id = "B05"
            brief_data = {
                "audience": "API and security leads",
                "technical_problem": "BOLA, broken login, and function-level authorization are different tests.",
                "editorial_angle": "Penetration testing connects off-chain dApp backend APIs, RPC gateways, and relayer infrastructure.",
            }
        else:
            brief_id = "B04"
            brief_data = {
                "audience": "Web3 app engineers",
                "technical_problem": "An authenticated user is not automatically authorized to read another user's object.",
                "editorial_angle": "Broken Object Level Authorization (BOLA) distinguishes resource-level permissions from user login authentication.",
            }
    elif "tool" in sl_clean or "agentic-security" in sl_clean:
        if final_fmt in {"differentiation", "service-overview"} or "code-scanning" in (final_url or "") or "pr" in excerpt.lower():
            brief_id = "B07"
            brief_data = {
                "audience": "Protocol CI maintainers",
                "technical_problem": "PR-level alerts can make security findings available before merge; tailor checks to protocol invariants.",
                "editorial_angle": "SanadSquad builds tailored security detectors, automated PR reviewers, and monitoring agents to detect flaws before merge.",
            }
        else:
            brief_id = "B06"
            brief_data = {
                "audience": "Agent platform owners",
                "technical_problem": "Runtime policy hooks and action visibility matter when AI is allowed to operate tools.",
                "editorial_angle": "OWASP Agent Control Standard defines execution boundaries outside LLM context to restrict unauthorized tool actions.",
            }
    elif "payment" in sl_clean:
        if final_fmt == "news-reaction" or "mpp" in (final_url or "").lower():
            brief_id = "B09"
            brief_data = {
                "audience": "Payment integrators",
                "technical_problem": "MPP's June 2026 x402 support makes authorization and verification design a better comparison than protocol tribalism.",
                "editorial_angle": "mppx unified SDK interface supports both MPP EVM charges and compatible x402 flows with per-agent authorization limits.",
            }
        else:
            brief_id = "B08"
            brief_data = {
                "audience": "Agent/API payment builders",
                "technical_problem": "x402 facilitators simplify verification and settlement but are optional.",
                "editorial_angle": "x402 uses HTTP 402 signaling; resource servers can settle directly peer-to-peer or delegate to optional facilitators.",
            }
    elif "consulting" in sl_clean:
        brief_id = "B10"
        brief_data = {
            "audience": "Protocol founders",
            "technical_problem": "Which design decisions must be reviewed before implementation? Privileged upgrades and requirements are early decisions.",
            "editorial_angle": "Pre-deployment architecture reviews, threat modeling, and governance design before code is written.",
        }

    editorial_brief_instruction = (
        f"EDITORIAL BRIEF ({brief_id}):\n"
        f"- Target Audience: {brief_data['audience']}\n"
        f"- Core Technical Problem: {brief_data['technical_problem']}\n"
        f"- Strategic Editorial Angle: {brief_data['editorial_angle']}\n"
    )

    # Concise single-point evidence framing to avoid token bloat and cognitive overload
    conciseness_guidance = (
        "TARGET LENGTH & CONCISENESS:\n"
        "- Aim for 200–245 characters total for the complete post (including link and CTA if present).\n"
        "- Keep prose to 1–2 crisp, substantive sentences.\n"
        "- Do NOT exceed 250 characters on your first draft so the post safely passes within the 280-character ceiling without revisions.\n"
    )

    unit_guidance = (
        f"Format: {final_fmt}. Service line: {service_line}.\n"
        f"{editorial_brief_instruction}\n"
        f"{format_specific_guidance}\n"
        f"{service_specific_guidance}\n"
        f"{conciseness_guidance}\n"
        f"PRIORITIZED EVIDENCE FACT: '{excerpt}'\n"
        f"Epistemic boundaries: Differentiate verified facts from analytical interpretation. "
        f"Do NOT claim SanadSquad audited the protocol unless stated in the evidence.\n"
        f"CTA Policy: {cta_instruction}\n\n"
        f"{budget.budget_instruction()}\n"
        f"{guidance}"
    )

    unit = ContentUnit(
        id=f"{slot_id}_u1",
        role="HOOK",
        max_chars=280,
        guidance=unit_guidance,
        source_evidence_ids=ev_ids,
        mandatory_url=final_url,
    )

    pol_id = getattr(policy, "policy_id", "sanadsquad_marketing_rules") if policy else "sanadsquad_marketing_rules"
    pol_ver = getattr(policy, "policy_version", "1.0.0") if policy else "1.0.0"

    plan = EvidenceFirstPlan(
        slot_id=slot_id,
        topic_id=f"MKTG-{service_line.upper().replace('-', '_')}",
        content_type="marketing-post",
        source_strategy="web_research",
        policy_id=pol_id,
        policy_version=pol_ver,
        authorization_mode=authorization_mode,
        units=[unit],
        evidence_items=ev_list,
        character_budget=budget.model_dump(),
        mandatory_url=final_url,
        replan_notes=replan_notes,
    )
    plan.plan_hash = plan.compute_plan_hash()
    return plan


def build_external_technical_plan(
    slot_id: str,
    resource_brief: Any,
    evidence: list[Any],
) -> EvidenceFirstPlan:
    """Build an EvidenceFirstPlan for a technical thread grounded in an external technical resource."""
    ev_ids = [e.id if hasattr(e, "id") else e.get("id") for e in evidence]
    url = getattr(resource_brief, "url", "") if resource_brief else ""
    summary = getattr(resource_brief, "summary_brief", "") if resource_brief else ""

    units = [
        ContentUnit(id=f"{slot_id}_u1", role="HOOK", max_chars=280, guidance=f"Technical incident hook from {url}: {summary[:100]}", source_evidence_ids=ev_ids),
        ContentUnit(id=f"{slot_id}_u2", role="MECHANISM", max_chars=280, guidance="Explain the core technical breakdown or execution vulnerability.", source_evidence_ids=ev_ids),
        ContentUnit(id=f"{slot_id}_u3", role="CONSEQUENCE", max_chars=280, guidance="Detail the operational impact and exploit consequence.", source_evidence_ids=ev_ids),
        ContentUnit(id=f"{slot_id}_u4", role="RECOMMENDATION", max_chars=280, guidance="Provide defensive mitigation and engineering review safeguards.", source_evidence_ids=ev_ids),
        ContentUnit(id=f"{slot_id}_u5", role="SUMMARY", max_chars=280, guidance=f"Provide the practitioner takeaway and cite the verified resource link: {url}", source_evidence_ids=ev_ids),
    ]

    plan = EvidenceFirstPlan(
        slot_id=slot_id,
        topic_id="TECH-EXT-INCIDENT",
        content_type="tech-thread",
        source_strategy="external_technical",
        policy_id="security_audit_firm",
        policy_version="1.0.0",
        units=units,
        evidence_items=evidence,
    )
    plan.plan_hash = plan.compute_plan_hash()
    return plan
