"""Evidence-first content planning and sufficiency preflight.

Constructs structured EvidenceFirstPlan specifications directly from
verified propositions and typed relations in the catalog before natural language generation.
"""
from __future__ import annotations

import hashlib
from typing import Literal
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


class EvidenceFirstPlan(BaseModel):
    slot_id: str
    topic_id: str
    content_type: str
    catalog_version: str = "2.0.0"
    policy_id: str = "security_audit_firm"
    policy_version: str = "1.0.0"
    policy_hash: str | None = None
    authorization_mode: str = "pilot_evaluation"  # "pilot_evaluation" or "publication_eligible"
    units: list[ContentUnit]
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
                "Example pattern: 'Missing access controls allow malicious actors to withdraw Ether from contract accounts. Implement access controls so withdrawals trigger only when authorized to prevent this risk.'"
            )
        else:
            guidance = (
                "Write EXACTLY ONE single tweet under 280 characters. "
                "You MUST include a clear, actionable security recommendation or review invitation to the reader. "
                "Strictly preserve approved outcomes and scope from assigned propositions. "
                "Never invent guarantees, universal scope expansions (such as 'all external calls'), or unlicensed instrumental outcomes (such as 'prevents execution from continuing on failure')."
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
            units.append(ContentUnit(
                id=f"{slot_id}_u{unit_idx}",
                role="MITIGATION",
                proposition_ids=[r0.id],
                relation_ids=[mit_rel] if mit_rel else [],
                realization_mode="MODE_B_NATURAL",
                max_chars=280,
                guidance="Explain recommended defensive patterns (e.g. state-updating sequence or access controls). Use clean, grammatically valid English (e.g. 'Implement controls so withdrawals can only be triggered...' or 'Implementing access controls ensures that withdrawals trigger only according to specifications...'). Do NOT claim this defense is 'the primary defense' or 'most important' unless explicitly specified."
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

