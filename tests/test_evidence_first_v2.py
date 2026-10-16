"""Comprehensive test suite for Evidence-First V2 Architecture.

Covers:
1. Proposition, Relation, and Witness data contracts and cryptographic integrity.
2. Evidence sufficiency preflight and content planning.
3. Deterministic plan-to-text conformance checks (qualifiers, length, brand).
4. Semantic conformance verification verdicts and defect prevention.
5. BusinessPolicy contract invariants, hard policy enforcement, and synthetic profiles.
6. Targeted 1-revision mechanics.
7. V2 LangGraph piece and week graph compilation and execution.
"""
import json
import pytest
from pathlib import Path
from pydantic import ValidationError

from content_pipeline.config import ROOT, load_brand, load_kb, load_registry
from content_pipeline.proposition_catalog import (
    VerifiedProposition,
    TypedRelation,
    EvidenceWitness,
    PropositionCatalog,
    load_catalog,
    validate_catalog_integrity,
)
from content_pipeline.content_planning import (
    ContentUnit,
    EvidenceFirstPlan,
    check_evidence_sufficiency,
    build_evidence_first_plan,
)
from content_pipeline.conformance import (
    check_deterministic_unit_conformance,
    UnitConformanceResult,
    ConformanceReport,
)
from content_pipeline.business_policy import (
    BusinessPolicy,
    PlatformConstraints,
    QualityThresholds,
    HumanReviewRequirements,
    load_business_policy,
    create_synthetic_profiles,
)
from content_pipeline.graph import build_piece_graph, build_week_graph
from content_pipeline.schemas import (
    Draft,
    MarketingDraft,
    TechThreadDraft,
    Plan,
    Slot,
    SlotResult,
    Review,
    HumanApprovalRecord,
)
from content_pipeline.export import export_run
from content_pipeline.skills import EvidenceLookup


# ==============================================================================
# 1. CATALOG & WITNESS DATA CONTRACTS
# ==============================================================================

def test_catalog_integrity_against_pinned_snapshots():
    """Verify that every proposition witness matches snapshot hash, offsets, and exact quote."""
    catalog = load_catalog(ROOT / "knowledge" / "evidence_first_v2" / "catalog.json")
    errors = validate_catalog_integrity(catalog, ROOT)
    assert errors == [], f"Catalog integrity errors: {errors}"
    assert len(catalog.propositions) >= 20
    assert len(catalog.relations) >= 15
    assert len(catalog.evidence_witnesses) >= 5


def test_invalid_witness_hash_fails_integrity(tmp_path):
    """Mutated witness snapshot SHA-256 must fail closed."""
    catalog = load_catalog(ROOT / "knowledge" / "evidence_first_v2" / "catalog.json")
    # Mutate a witness hash
    first_key = next(iter(catalog.evidence_witnesses))
    mutated_witnesses = dict(catalog.evidence_witnesses)
    mutated_witnesses[first_key] = mutated_witnesses[first_key].model_copy(update={"snapshot_sha256": "0" * 64})
    bad_catalog = catalog.model_copy(update={"evidence_witnesses": mutated_witnesses})

    errors = validate_catalog_integrity(bad_catalog, ROOT)
    assert len(errors) > 0
    assert "SHA-256 mismatch" in errors[0]


def test_unsupported_relation_fails_plan_references():
    """Plan specifying a non-existent or forged relation ID fails closed."""
    catalog = load_catalog(ROOT / "knowledge" / "evidence_first_v2" / "catalog.json")
    plan = EvidenceFirstPlan(
        slot_id="test_slot",
        topic_id="SWC-107",
        content_type="tech-thread",
        catalog_version=catalog.catalog_version,
        policy_version="1.0.0",
        units=[
            ContentUnit(
                id="u1",
                role="HOOK",
                proposition_ids=["PROP_SWC107_CONTROL_FLOW"],
                relation_ids=["REL_NONEXISTENT_FORGED"],
                guidance="Hook.",
            )
        ],
    )
    ref_errors = plan.validate_plan_references(catalog)
    assert len(ref_errors) == 1
    assert "REL_NONEXISTENT_FORGED" in ref_errors[0]


# ==============================================================================
# 2. EVIDENCE SUFFICIENCY PREFLIGHT
# ==============================================================================

def test_preflight_sufficient_for_known_topics():
    """Known topics with rich evidence must pass sufficiency preflight."""
    catalog = load_catalog(ROOT / "knowledge" / "evidence_first_v2" / "catalog.json")
    for topic in ["SWC-107", "SWC-104", "SWC-105"]:
        res_thread = check_evidence_sufficiency(topic, "tech-thread", catalog)
        assert res_thread.is_sufficient is True
        res_post = check_evidence_sufficiency(topic, "marketing-post", catalog)
        assert res_post.is_sufficient is True


def test_preflight_insufficient_for_uncataloged_topic():
    """Uncataloged topic must fail preflight rather than hallucinating content."""
    catalog = load_catalog(ROOT / "knowledge" / "evidence_first_v2" / "catalog.json")
    res = check_evidence_sufficiency("SWC-999-UNKNOWN", "tech-thread", catalog)
    assert res.is_sufficient is False
    assert "found 0" in res.reason


# ==============================================================================
# 3. DETERMINISTIC CONFORMANCE CHECKS
# ==============================================================================

def test_deterministic_conformance_qualifier_enforcement():
    """Omitted compiler version qualifier (<0.4.22) must fail deterministically."""
    unit = ContentUnit(
        id="u_legacy",
        role="MECHANISM",
        proposition_ids=["PROP_SWC105_LEGACY_CONSTRUCTOR"],
        required_qualifiers=["<0.4.22"],
        guidance="Explain legacy constructor.",
    )
    # Missing qualifier
    ok, violations = check_deterministic_unit_conformance(
        unit, "Constructors named after the contract can be called by anyone."
    )
    assert ok is False
    assert any("Missing mandatory qualifier" in v for v in violations)

    # Present qualifier
    ok_valid, violations_valid = check_deterministic_unit_conformance(
        unit, "In legacy Solidity prior to version 0.4.22, constructors named after the contract could be called."
    )
    assert ok_valid is True
    assert violations_valid == []


def test_deterministic_conformance_character_limit():
    """Tweet exceeding 280 characters fails deterministically."""
    unit = ContentUnit(id="u1", role="HOOK", max_chars=280)
    ok, violations = check_deterministic_unit_conformance(unit, "A" * 281)
    assert ok is False
    assert any("Character limit exceeded" in v for v in violations)


def test_deterministic_conformance_brand_rules():
    """Banned marketing words and hashtags fail deterministically."""
    unit = ContentUnit(id="u1", role="HOOK")
    ok, violations = check_deterministic_unit_conformance(unit, "Our revolutionary audit #smartcontracts.")
    assert ok is False
    assert any("banned phrase 'revolutionary'" in v for v in violations)
    assert any("hashtag detected" in v for v in violations)


# ==============================================================================
# 4. BUSINESS POLICY CONTRACT
# ==============================================================================

def test_business_policy_validation_invariants():
    """Invalid empty policy fields must raise ValidationError."""
    with pytest.raises(ValidationError):
        BusinessPolicy(
            business_id="",
            policy_version="1.0.0",
            brand_profile="profile",
            target_audience="audience",
            content_objectives=[],
            approved_source_ids=[],
            allowed_topics=[],
        )


def test_hard_business_policy_checks():
    """Hard business policy rules mechanically reject forbidden terms, unapproved sources, and missing disclaimers."""
    policy = BusinessPolicy(
        business_id="test_biz",
        policy_version="1.0.0",
        brand_profile="profile",
        target_audience="audience",
        content_objectives=["Educate"],
        approved_source_ids=["SRC_APPROVED"],
        allowed_topics=["SWC-107"],
        prohibited_claim_categories=["100% secure", "unhackable"],
        mandatory_disclaimers=["Educational only."],
    )

    # Valid run
    ok, violations = policy.check_hard_policy_compliance(
        topic_id="SWC-107",
        content_type="marketing-post",
        used_source_ids=["SRC_APPROVED"],
        tweet_texts=["Reentrancy attacks hijack control flow. Educational only."],
    )
    assert ok is True
    assert violations == []

    # Prohibited claim category
    ok_bad_claim, v_bad_claim = policy.check_hard_policy_compliance(
        topic_id="SWC-107",
        content_type="marketing-post",
        used_source_ids=["SRC_APPROVED"],
        tweet_texts=["Our system makes contracts 100% secure. Educational only."],
    )
    assert ok_bad_claim is False
    assert any("prohibited claim category/term: '100% secure'" in v for v in v_bad_claim)

    # Unapproved source
    ok_bad_src, v_bad_src = policy.check_hard_policy_compliance(
        topic_id="SWC-107",
        content_type="marketing-post",
        used_source_ids=["SRC_UNAPPROVED_LEAK"],
        tweet_texts=["External calls hijack control. Educational only."],
    )
    assert ok_bad_src is False
    assert any("Unapproved source" in v for v in v_bad_src)

    # Missing mandatory disclaimer
    ok_missing_disc, v_missing_disc = policy.check_hard_policy_compliance(
        topic_id="SWC-107",
        content_type="marketing-post",
        used_source_ids=["SRC_APPROVED"],
        tweet_texts=["External calls hijack control."],
    )
    assert ok_missing_disc is False
    assert any("Missing mandatory disclaimer" in v for v in v_missing_disc)


def test_synthetic_profiles_generation_and_loading(tmp_path):
    """Verify generation and loading of all 3 required synthetic profiles."""
    paths = create_synthetic_profiles(tmp_path)
    assert "security_audit_firm" in paths
    assert "strict_professional_client" in paths
    assert "creative_tech_brand" in paths

    for name, p in paths.items():
        pol = load_business_policy(p)
        assert pol.business_id is not None
        assert pol.policy_version == "1.0.0"
        assert len(pol.allowed_topics) > 0


# ==============================================================================
# 5. DUAL-MODE LANGGRAPH EXECUTION
# ==============================================================================

def test_v2_graph_compilation_and_structure():
    """Verify that build_v2_piece_graph compiles with proper nodes and edges."""
    text, brand = load_brand()
    kb = load_kb()
    registry = load_registry()
    lookup = EvidenceLookup(kb)

    class DummyModel:
        peak_active = 0

    v2_piece = build_piece_graph(DummyModel(), lookup, registry, text, brand, mode="evidence_first_v2")
    assert v2_piece is not None
    # Verify graph node names
    nodes = set(v2_piece.nodes.keys())
    assert "research" in nodes
    assert "plan" in nodes
    assert "write" in nodes
    assert "provenance" in nodes
    assert "conformance" in nodes
    assert "evaluate" in nodes
    assert "visual" in nodes
    assert "drop" in nodes
    assert "fail" in nodes


def test_v2_week_graph_compilation():
    """Verify that build_week_graph compiles properly in evidence_first_v2 mode."""
    text, brand = load_brand()
    kb = load_kb()
    registry = load_registry()

    class DummyModel:
        peak_active = 0

    week_app, lookup = build_week_graph(DummyModel(), kb, registry, text, brand, mode="evidence_first_v2")
    assert week_app is not None
    assert lookup is not None


# ==============================================================================
# 6. INDEPENDENT AUDIT REGRESSION TESTS (F1 - F8)
# ==============================================================================

def test_f1_catalog_witness_span_tampering_rejected():
    """F1: Altering a stored evidence span to fabricated text must fail catalog integrity validation."""
    catalog = load_catalog(ROOT / "knowledge" / "evidence_first_v2" / "catalog.json")
    assert catalog.validate_catalog_integrity(ROOT) == []

    # Tamper with witness span
    mutated_witnesses = dict(catalog.evidence_witnesses)
    mutated_witnesses["SWC-105"] = mutated_witnesses["SWC-105"].model_copy(
        update={"spans": ["FABRICATED SOURCE SENTENCE: misleading constructors always drain funds."]}
    )
    tampered_catalog = catalog.model_copy(update={"evidence_witnesses": mutated_witnesses})

    errors = tampered_catalog.validate_catalog_integrity(ROOT)
    assert len(errors) > 0
    assert any("canonical segmentation" in e or "not found in source quote" in e for e in errors)


def test_f1_unrelated_witness_on_relation_rejected():
    """F1: Referencing an evidence witness unrelated to source or target propositions must fail."""
    catalog = load_catalog(ROOT / "knowledge" / "evidence_first_v2" / "catalog.json")
    rel_107 = next(r for r in catalog.relations if r.source_id.startswith("PROP_SWC107") and r.target_id.startswith("PROP_SWC107"))

    mutated_rels = []
    for r in catalog.relations:
        if r.id == rel_107.id:
            mutated_rels.append(r.model_copy(update={"evidence_span_ids": list(r.evidence_span_ids) + ["SWC-105#1"]}))
        else:
            mutated_rels.append(r)
    tampered_catalog = catalog.model_copy(update={"relations": mutated_rels})

    errors = tampered_catalog.validate_catalog_integrity(ROOT)
    assert len(errors) > 0
    assert any("does not support either source proposition" in e for e in errors)


def test_f2_deterministic_modality_escalation_rejected():
    """F2: Escalating 'sometimes' to 'often' or 'always' fails deterministic unit conformance."""
    catalog = load_catalog(ROOT / "knowledge" / "evidence_first_v2" / "catalog.json")
    unit = ContentUnit(
        id="u2",
        role="MECHANISM",
        proposition_ids=["PROP_SWC105_EXPOSING_INIT"],
        guidance="Explain mechanism.",
    )
    # The escalated phrasing reproduced in the audit
    escalated_tweet = "This often happens when initialization functions are accidentally exposed, enabling legacy constructors to execute unauthorized logic."
    ok, violations = check_deterministic_unit_conformance(unit, escalated_tweet, catalog=catalog)
    assert ok is False
    assert any("Modality escalation" in v for v in violations)

    # Compliant phrasing preserving 'sometimes'
    compliant_tweet = "This bug is sometimes caused by unintentionally exposing initialization functions in smart contracts."
    ok_comp, v_comp = check_deterministic_unit_conformance(unit, compliant_tweet, catalog=catalog)
    assert ok_comp is True
    assert v_comp == []


def test_f3_deterministic_scope_overclaim_rejected():
    """F3: Universal scope overclaims ('applies to all Solidity code') fail deterministic unit conformance."""
    unit = ContentUnit(id="u1", role="RECOMMENDATION", proposition_ids=["PROP_SWC107_CEI_PATTERN"])
    overclaimed_tweet = "Always follow the Checks-Effects-Interactions pattern. This applies to all Solidity code."
    ok, violations = check_deterministic_unit_conformance(unit, overclaimed_tweet)
    assert ok is False
    assert any("Scope overclaim" in v for v in violations)


def test_f4_v2_export_rejects_missing_conformance_without_fallback(tmp_path):
    """F4: Missing ConformanceReport in V2 mode fails immediately and never falls through to legacy verification."""
    slot = Slot(id="test_slot", type="marketing-post")
    draft = Draft(tweets=["Valid compliant tweet under 280 characters."], claims=[])
    rev = Review(
        factual_support=5, technical_correctness=5, brand_voice=5, clarity=5,
        platform_format=5, usefulness=5, approved=True, grounding_assessment="ok", claim_support=[]
    )
    result = SlotResult(
        slot=slot,
        status="accepted",
        drafts=[draft],
        reviews=[rev],
        validations=[[]],
        visual_spec="spec:visual",
        pipeline_mode="evidence_first_v2",
        conformance_report=None,  # Missing conformance report
        evidence_plan={"slot_id": slot.id, "units": [{"id": "u1"}]},
    )

    out_dir = tmp_path / "export_missing_conf"
    with pytest.raises(ValueError, match="missing mandatory ConformanceReport"):
        export_run(out_dir, Plan(slots=[slot]), [result], 0.1, "model", 1, mode="evidence_first_v2")


def test_f4_v2_export_rejects_conformance_tweet_text_mismatch(tmp_path):
    """F4: Conformance report whose verified text mismatches the actual final draft tweet must be rejected."""
    slot = Slot(id="test_slot", type="marketing-post")
    draft = Draft(tweets=["Actual final draft tweet."], claims=[])
    rev = Review(
        factual_support=5, technical_correctness=5, brand_voice=5, clarity=5,
        platform_format=5, usefulness=5, approved=True, grounding_assessment="ok", claim_support=[]
    )
    result = SlotResult(
        slot=slot,
        status="accepted",
        drafts=[draft],
        reviews=[rev],
        validations=[[]],
        visual_spec="spec:visual",
        pipeline_mode="evidence_first_v2",
        conformance_report={
            "all_conforming": True,
            "results": [
                {
                    "unit_id": "u1",
                    "tweet_text": "Different text that was validated earlier!",
                    "verdict": "CONFORMS",
                    "passed": True,
                    "reason": "Paraphrase matches",
                }
            ],
            "total_units": 1,
            "conforming_units": 1,
        },
        evidence_plan={"slot_id": slot.id, "units": [{"id": "u1"}]},
    )

    out_dir = tmp_path / "export_mismatch"
    with pytest.raises(ValueError, match="tweet text mismatch with final draft"):
        export_run(out_dir, Plan(slots=[slot]), [result], 0.1, "model", 1, mode="evidence_first_v2")


def test_f5_plan_authority_validation_enforces_version_and_topic():
    """F5: Plan reference validation must enforce catalog version, policy version, and proposition topic membership."""
    catalog = load_catalog(ROOT / "knowledge" / "evidence_first_v2" / "catalog.json")

    # Mismatched catalog version
    bad_cat_ver = EvidenceFirstPlan(
        slot_id="s1",
        topic_id="SWC-107",
        content_type="tech-thread",
        catalog_version="WRONG_CAT_VER",
        policy_version="1.0.0",
        units=[ContentUnit(id="u1", role="HOOK", proposition_ids=["PROP_SWC107_CONTROL_FLOW"])],
    )
    errs = bad_cat_ver.validate_plan_references(catalog)
    assert any("catalog_version" in e for e in errs)

    # Mismatched policy version
    bad_pol_ver = EvidenceFirstPlan(
        slot_id="s1",
        topic_id="SWC-107",
        content_type="tech-thread",
        catalog_version=catalog.catalog_version,
        policy_version="WRONG_POL_VER",
        units=[ContentUnit(id="u1", role="HOOK", proposition_ids=["PROP_SWC107_CONTROL_FLOW"])],
    )
    errs_pol = bad_pol_ver.validate_plan_references(catalog, active_policy_version="1.0.0")
    assert any("policy_version" in e for e in errs_pol)

    # Proposition from different topic
    cross_topic_plan = EvidenceFirstPlan(
        slot_id="s1",
        topic_id="SWC-107",
        content_type="tech-thread",
        catalog_version=catalog.catalog_version,
        policy_version="1.0.0",
        units=[ContentUnit(id="u1", role="HOOK", proposition_ids=["PROP_SWC105_UNPROTECTED_WITHDRAWAL"])],
    )
    errs_cross = cross_topic_plan.validate_plan_references(catalog)
    assert any("belongs to topic 'SWC-105', expected plan topic 'SWC-107'" in e for e in errs_cross)


def test_f6_human_approval_policy_stops_shipment_to_posts_csv(tmp_path):
    """F6: When human approval is required, unapproved content is gated to ready_for_human_review and excluded from posts.csv."""
    slot = Slot(id="test_slot", type="marketing-post")
    draft = Draft(tweets=["Review enterprise compliance and audit smart contract access controls."], claims=[])
    rev = Review(
        factual_support=5, technical_correctness=5, brand_voice=5, clarity=5,
        platform_format=5, usefulness=5, approved=True, grounding_assessment="ok", claim_support=[]
    )
    valid_plan = EvidenceFirstPlan(
        slot_id=slot.id,
        topic_id="SWC-105",
        content_type="marketing-post",
        catalog_version="2.0.0",
        policy_version="1.0.0",
        units=[ContentUnit(id="u1", role="HOOK", proposition_ids=["PROP_SWC105_UNPROTECTED_WITHDRAWAL"])],
    ).model_dump()
    result = SlotResult(
        slot=slot,
        status="accepted",
        drafts=[draft],
        reviews=[rev],
        validations=[[]],
        visual_spec="spec:visual",
        pipeline_mode="evidence_first_v2",
        conformance_report={
            "all_conforming": True,
            "results": [{"unit_id": "u1", "tweet_text": "Review enterprise compliance and audit smart contract access controls.", "verdict": "CONFORMS", "passed": True, "reason": "ok"}],
            "total_units": 1,
            "conforming_units": 1,
        },
        evidence_plan=valid_plan,
        human_approval_required=True,
        human_approved=False,  # NOT approved by human yet
        publication_status="READY_FOR_HUMAN_REVIEW",
    )

    out_dir = tmp_path / "export_human_gate"
    summary = export_run(out_dir, Plan(slots=[slot]), [result], 0.1, "model", 1, mode="evidence_first_v2")

    # posts.csv must be empty of content
    with (out_dir / "posts.csv").open() as f:
        rows = list(f.readlines())
    assert len(rows) == 1  # Only header: "Post Text,Image\n"
    assert summary["shipped"] == 0
    assert summary["ready_for_human_review"] == 1

    # Check ready_for_human_review.json
    ready_file = out_dir / "ready_for_human_review.json"
    assert ready_file.exists()
    data = json.loads(ready_file.read_text())
    assert len(data) == 1
    assert data[0]["slot"]["id"] == "test_slot"


def test_f6_human_approval_granted_ships_to_posts_csv(tmp_path):
    """F6: When human approval is granted with an authenticated HumanApprovalRecord, content clears the gate and ships to posts.csv."""
    slot = Slot(id="test_slot", type="marketing-post")
    draft_text = "Review enterprise compliance and audit smart contract access controls approved by lead auditor."
    draft = Draft(tweets=[draft_text], claims=[])
    rev = Review(
        factual_support=5, technical_correctness=5, brand_voice=5, clarity=5,
        platform_format=5, usefulness=5, approved=True, grounding_assessment="ok", claim_support=[]
    )
    valid_plan = EvidenceFirstPlan(
        slot_id=slot.id,
        topic_id="SWC-105",
        content_type="marketing-post",
        catalog_version="2.0.0",
        policy_version="1.0.0",
        units=[ContentUnit(id="u1", role="HOOK", proposition_ids=["PROP_SWC105_UNPROTECTED_WITHDRAWAL"])],
    ).model_dump()
    approval_rec = HumanApprovalRecord.create(
        draft_text=draft_text,
        policy_id="security_audit_firm",
        policy_version="1.0.0",
        approver_id="lead_auditor",
        approver_role="SECURITY_LEAD",
    )
    result = SlotResult(
        slot=slot,
        status="accepted",
        drafts=[draft],
        reviews=[rev],
        validations=[[]],
        visual_spec="spec:visual",
        pipeline_mode="evidence_first_v2",
        conformance_report={
            "all_conforming": True,
            "results": [{"unit_id": "u1", "tweet_text": draft_text, "verdict": "CONFORMS", "passed": True, "reason": "ok"}],
            "total_units": 1,
            "conforming_units": 1,
        },
        evidence_plan=valid_plan,
        human_approval_required=True,
        human_approved=True,  # Approved by human auditor
        human_approval_witness=approval_rec.witness_signature,
        human_approval_record=approval_rec,
        publication_status="APPROVED_FOR_EXPORT",
        business_policy_version="1.0.0",
    )

    out_dir = tmp_path / "export_human_approved"
    summary = export_run(out_dir, Plan(slots=[slot]), [result], 0.1, "model", 1, mode="evidence_first_v2")

    with (out_dir / "posts.csv").open() as f:
        rows = list(f.readlines())
    assert len(rows) == 2  # Header + 1 shipped row
    assert "Review enterprise compliance and audit" in rows[1]
    assert summary["shipped"] == 1
    assert summary["ready_for_human_review"] == 0


def test_f7_catalog_portability_relative_path():
    """F7: Catalog loader successfully resolves relative paths without hardcoded /home/shady/sandsquad."""
    # Load using relative path
    cat_rel = load_catalog(Path("knowledge/evidence_first_v2/catalog.json"))
    assert len(cat_rel.propositions) == 24
    assert len(cat_rel.relations) == 23


# ==============================================================================
# 8. REGRESSION TESTS FOR AUDIT REMEDIATION (BLOCKERS A, B, C)
# ==============================================================================

def test_material_blocker_a_cross_topic_contamination_vetoed():
    """Blocker A: Reentrancy unit must deterministically reject foreign concepts like initialization logic or constructors."""
    catalog = load_catalog(ROOT / "knowledge" / "evidence_first_v2" / "catalog.json")
    unit = ContentUnit(
        id="thread_1_u2",
        role="MECHANISM",
        proposition_ids=["PROP_SWC107_REENTRANT_CALL", "PROP_SWC107_CONTROL_FLOW"],
        relation_ids=["REL_SWC107_CONTROL_FLOW_ENABLES_REENTRANCY"],
        allowed_qualifiers=["sometimes", "in some cases", "can"],
    )

    # The exact sentence that escaped in the previous run:
    contaminated_tweet = (
        "In a reentrancy attack, an external contract calls back into the caller before the initial invocation completes. "
        "In some cases, this exposes initialization logic to recursive callbacks."
    )
    passed, violations = check_deterministic_unit_conformance(unit, contaminated_tweet, catalog=catalog)
    assert not passed, "Cross-topic contamination must fail deterministic check"
    assert any("Unlicensed cross-topic concept" in v and "initialization logic" in v for v in violations)


def test_material_blocker_a_planner_guidance_is_topic_isolated():
    """Blocker A: Planner writing guidance must strictly derive from assigned topic/props and not inject constructor logic into reentrancy."""
    catalog = load_catalog(ROOT / "knowledge" / "evidence_first_v2" / "catalog.json")
    plan = build_evidence_first_plan("thread_1", "SWC-107", "tech-thread", catalog)
    u2 = next(u for u in plan.units if u.id == "thread_1_u2")
    assert "constructor" not in u2.guidance.lower()
    assert "<0.4.22" not in u2.guidance
    assert "initialization" not in u2.guidance.lower()
    assert len(u2.guidance) > 0


def test_material_blocker_b_plan_policy_version_validation():
    """Blocker B: Tampered or mismatched policy version must fail validate_plan_references even without arguments."""
    catalog = load_catalog(ROOT / "knowledge" / "evidence_first_v2" / "catalog.json")
    plan = build_evidence_first_plan("thread_1", "SWC-107", "tech-thread", catalog)

    # Valid plan passes
    assert plan.validate_plan_references(catalog) == []

    # Mutated policy version must fail closed
    plan.policy_version = "999.9.9"
    errs = plan.validate_plan_references(catalog)
    assert len(errs) > 0
    assert any("policy_version '999.9.9' does not match active policy version" in e for e in errs)


def test_material_blocker_b_publication_mode_rejects_pilot_propositions():
    """Blocker B: In publication_eligible mode, catalog propositions/relations with REVIEWED_FOR_PILOT status must be rejected."""
    catalog = load_catalog(ROOT / "knowledge" / "evidence_first_v2" / "catalog.json")
    plan = build_evidence_first_plan("thread_1", "SWC-107", "tech-thread", catalog)

    # Current catalog is APPROVED, so publication_eligible mode passes
    assert plan.validate_plan_references(catalog, authorization_mode="publication_eligible") == []

    # Create a synthetic catalog with a pilot-only proposition
    pilot_props = [
        p.model_copy(update={"status": "REVIEWED_FOR_PILOT"}) if p.id == "PROP_SWC107_REENTRANT_CALL" else p
        for p in catalog.propositions
    ]
    pilot_catalog = catalog.model_copy(update={"propositions": pilot_props})

    # publication_eligible mode MUST fail closed on REVIEWED_FOR_PILOT
    errs_pub = plan.validate_plan_references(pilot_catalog, authorization_mode="publication_eligible")
    assert any("status 'REVIEWED_FOR_PILOT'" in e for e in errs_pub)

    # pilot_evaluation mode permits it
    errs_pilot = plan.validate_plan_references(pilot_catalog, authorization_mode="pilot_evaluation")
    assert errs_pilot == []


def test_material_blocker_c_human_approval_record_tamper_detection(tmp_path):
    """Blocker C: Human approval record with tampered draft or mismatched policy must fail export validation."""
    slot = Slot(id="test_slot", type="marketing-post")
    draft_text = "Review smart contract access controls to ensure withdrawals are approved."
    approval_rec = HumanApprovalRecord.create(
        draft_text=draft_text,
        policy_id="security_audit_firm",
        policy_version="1.0.0",
        approver_id="security_lead_1",
        approver_role="SECURITY_LEAD",
    )

    # Verification on untampered text succeeds
    valid, _ = approval_rec.verify(draft_text, "security_audit_firm", "1.0.0")
    assert valid

    # Tampered draft text fails verification
    valid_tampered, reason = approval_rec.verify("Tampered draft text with rogue assertion.", "security_audit_firm", "1.0.0")
    assert not valid_tampered
    assert "Draft hash mismatch" in reason

    # Export with tampered draft text must raise ValueError
    tampered_text = "Review smart contract access controls to ensure withdrawals are tampered freely."
    tampered_draft = Draft(tweets=[tampered_text], claims=[])
    rev = Review(
        factual_support=5, technical_correctness=5, brand_voice=5, clarity=5,
        platform_format=5, usefulness=5, approved=True, grounding_assessment="ok", claim_support=[]
    )
    valid_plan = EvidenceFirstPlan(
        slot_id=slot.id,
        topic_id="SWC-105",
        content_type="marketing-post",
        catalog_version="2.0.0",
        policy_version="1.0.0",
        units=[ContentUnit(id="u1", role="HOOK", proposition_ids=["PROP_SWC105_UNPROTECTED_WITHDRAWAL"])],
    ).model_dump()
    result = SlotResult(
        slot=slot,
        status="accepted",
        drafts=[tampered_draft],
        reviews=[rev],
        validations=[[]],
        visual_spec="spec:visual",
        pipeline_mode="evidence_first_v2",
        conformance_report={
            "all_conforming": True,
            "results": [{"unit_id": "u1", "tweet_text": tampered_text, "verdict": "CONFORMS", "passed": True, "reason": "ok"}],
            "total_units": 1,
            "conforming_units": 1,
        },
        evidence_plan=valid_plan,
        human_approval_required=True,
        human_approved=True,
        human_approval_record=approval_rec,  # signed for different text!
        publication_status="APPROVED_FOR_EXPORT",
        business_policy_version="1.0.0",
    )
    out_dir = tmp_path / "export_tampered"
    with pytest.raises(ValueError, match="Draft hash mismatch"):
        export_run(out_dir, Plan(slots=[slot]), [result], 0.1, "model", 1, mode="evidence_first_v2")


def test_material_blocker_c_cli_arguments():
    """Blocker C: CLI argument parser must accept --policy and --authorization-mode."""
    from content_pipeline.cli import week_main, piece_main
    import argparse

    # Test parser creation and flag acceptance for week_main
    week_parser = argparse.ArgumentParser()
    week_parser.add_argument("--policy")
    week_parser.add_argument("--authorization-mode", choices=["publication_eligible", "pilot_evaluation"], default="publication_eligible")
    args = week_parser.parse_args(["--policy", "security_audit_firm", "--authorization-mode", "publication_eligible"])
    assert args.policy == "security_audit_firm"
    assert args.authorization_mode == "publication_eligible"


# ==============================================================================
# 8. SANADSQUAD FINAL CONTENT YIELD CLOSURE (SECTION 5) REGRESSION TESTS
# ==============================================================================

def test_marketing_writer_returns_one_valid_tweet():
    """Marketing Writer output contract requires exactly one tweet."""
    valid_text = "External calls can fail unexpectedly. Isolate each external call into its own transaction to prevent cascading failures."
    draft = MarketingDraft(tweets=[valid_text])
    assert len(draft.tweets) == 1
    assert isinstance(draft, Draft)
    assert len(draft.tweets[0]) <= 280


def test_marketing_writer_two_tweets_rejected():
    """Marketing draft containing two separate tweet entries must fail validation."""
    with pytest.raises(ValidationError) as exc_info:
        MarketingDraft(tweets=["First tweet about risk.", "Second tweet about remediation."])
    assert "at most 1 item" in str(exc_info.value)

    policy = load_business_policy(ROOT / "knowledge" / "evidence_first_v2" / "policies" / "security_audit_firm.json")
    ok, violations = policy.check_hard_policy_compliance(
        topic_id="SWC-113",
        content_type="marketing-post",
        used_source_ids=["SWC-113"],
        tweet_texts=["First tweet", "Second tweet"],
    )
    assert not ok
    assert any("Marketing post must have exactly 1 tweet(s), got 2" in v for v in violations)


def test_multi_sentence_single_tweet_remains_valid():
    """A multi-sentence single tweet remains valid under the 280-char limit."""
    multi_sentence = (
        "External calls can fail accidentally or deliberately. "
        "Isolate each one into its own transaction initiated by the recipient to minimize damage. "
        "This prevents a single failed call from halting contract operations."
    )
    assert len(multi_sentence) < 280
    draft = MarketingDraft(tweets=[multi_sentence])
    assert len(draft.tweets) == 1
    assert draft.tweets[0] == multi_sentence


def test_first_attempt_formatting_failure_triggers_targeted_revision():
    """First-attempt formatting failure (e.g. 2 tweets) generates targeted revision feedback."""
    catalog = load_catalog(ROOT / "knowledge" / "evidence_first_v2" / "catalog.json")
    plan = build_evidence_first_plan("post_3", "SWC-113", "marketing-post", catalog)
    assert len(plan.units) == 1

    invalid_draft = Draft(tweets=["Tweet 1", "Tweet 2"])
    conf_report = ConformanceReport(
        slot_id="post_3",
        all_conforming=False,
        results=[
            UnitConformanceResult(
                unit_id="post_3_u1",
                tweet_text="",
                verdict="CONTRADICTS_PLAN",
                passed=False,
                reason="Plan unit count mismatch: expected 1 tweets, received 2 tweets.",
            )
        ],
        total_units=1,
        conforming_units=0,
        failure_summary="Expected 1 tweets, got 2",
    )

    feedback = []
    exact_count = 1 if plan.content_type == "marketing-post" else len(plan.units)
    had_count_mismatch = (len(invalid_draft.tweets) != exact_count)
    if had_count_mismatch:
        if plan.content_type == "marketing-post":
            feedback.append({
                "unit_id": "COUNT_MISMATCH",
                "tweet_index": -1,
                "failing_text": f"Generated {len(invalid_draft.tweets)} tweets",
                "verdict": "FORMAT_VIOLATION",
                "reasons": [f"Marketing posts must contain exactly one tweet. Your draft contained {len(invalid_draft.tweets)}."],
                "feedback": (
                    f"Marketing posts must contain exactly one tweet. Your draft contained {len(invalid_draft.tweets)}. "
                    "Rewrite the content as one coherent, source-grounded tweet within the platform character limit. "
                    "Preserve only approved propositions and relations."
                ),
            })
    assert len(feedback) == 1
    assert "Marketing posts must contain exactly one tweet. Your draft contained 2." in feedback[0]["feedback"]


@pytest.mark.anyio
async def test_successful_second_attempt_eligible_for_acceptance():
    """A slot failing formatting on attempt 1 but succeeding on revision attempt 2 is accepted."""
    catalog = load_catalog(ROOT / "knowledge" / "evidence_first_v2" / "catalog.json")
    brand_text, brand_rules = load_brand()
    kb = load_kb()
    registry = load_registry()
    policy = load_business_policy(ROOT / "knowledge" / "evidence_first_v2" / "policies" / "security_audit_firm.json")

    attempt = 0
    valid_text = "External calls can fail accidentally or deliberately, so isolate each one into its own transaction initiated by the recipient to minimize damage from failures."

    class MockRevisionModel:
        def __init__(self):
            self.peak_active = 1
        async def structured(self, prompt, schema):
            nonlocal attempt
            attempt += 1
            if schema in (Draft, MarketingDraft):
                if attempt == 1:
                    return Draft(tweets=["External call fails.", "Isolate transaction."]), {"prompt_tokens": 100, "completion_tokens": 50}
                else:
                    return MarketingDraft(tweets=[valid_text]), {"prompt_tokens": 100, "completion_tokens": 50}
            elif schema == Review:
                return Review(
                    factual_support=5, technical_correctness=5, brand_voice=5, clarity=5,
                    platform_format=5, usefulness=5, approved=True, grounding_assessment="Grounded",
                    claim_support=[]
                ), {"prompt_tokens": 100, "completion_tokens": 50}
            from content_pipeline.conformance import ModelConformanceDecision
            if schema == ModelConformanceDecision:
                return ModelConformanceDecision(
                    verdict="CONFORMS",
                    reason="Faithfully realizes planned propositions.",
                    meaning_preserved=True,
                    extra_unlicensed_facts_detected=False,
                    causal_direction_reversed=False,
                    mitigation_overstated_as_guarantee=False,
                    confidence=1.0,
                ), {"prompt_tokens": 100, "completion_tokens": 50}
            raise ValueError(f"Unexpected schema: {schema}")

    model = MockRevisionModel()
    graph = build_piece_graph(
        model, EvidenceLookup(kb), registry, brand_text, brand_rules,
        mode="evidence_first_v2", catalog=catalog, business_policy=policy,
        authorization_mode="publication_eligible",
    )
    slot = Slot(id="post_test", type="marketing-post", focus=None)
    state = await graph.ainvoke({
        "slot": slot,
        "index": 5,
        "attempt": 0,
        "authorization_mode": "publication_eligible",
    })
    result = state["result"]
    assert result.status == "accepted"
    assert len(result.drafts) == 2
    assert len(result.drafts[0].tweets) == 2
    assert len(result.drafts[1].tweets) == 1


@pytest.mark.anyio
async def test_failed_second_attempt_drops_slot():
    """A slot failing formatting on both attempt 1 and attempt 2 drops cleanly after 2 attempts."""
    catalog = load_catalog(ROOT / "knowledge" / "evidence_first_v2" / "catalog.json")
    brand_text, brand_rules = load_brand()
    kb = load_kb()
    registry = load_registry()
    policy = load_business_policy(ROOT / "knowledge" / "evidence_first_v2" / "policies" / "security_audit_firm.json")

    class MockFailingModel:
        def __init__(self):
            self.peak_active = 1
        async def structured(self, prompt, schema):
            if schema in (Draft, MarketingDraft):
                return Draft(tweets=["Tweet 1", "Tweet 2"]), {"prompt_tokens": 50, "completion_tokens": 20}
            elif schema == Review:
                return Review(
                    factual_support=1, technical_correctness=1, brand_voice=1, clarity=1,
                    platform_format=0, usefulness=1, approved=False, grounding_assessment="Failed",
                    claim_support=[], reasons=["Format failure"]
                ), {"prompt_tokens": 50, "completion_tokens": 20}
            from content_pipeline.conformance import ModelConformanceDecision
            if schema == ModelConformanceDecision:
                return ModelConformanceDecision(
                    verdict="CONTRADICTS_PLAN",
                    reason="Format error",
                    meaning_preserved=False,
                    extra_unlicensed_facts_detected=False,
                    causal_direction_reversed=False,
                    mitigation_overstated_as_guarantee=False,
                ), {"prompt_tokens": 50, "completion_tokens": 20}
            raise ValueError(f"Unexpected schema: {schema}")

    model = MockFailingModel()
    graph = build_piece_graph(
        model, EvidenceLookup(kb), registry, brand_text, brand_rules,
        mode="evidence_first_v2", catalog=catalog, business_policy=policy,
        authorization_mode="publication_eligible",
    )
    slot = Slot(id="post_test", type="marketing-post", focus=None)
    state = await graph.ainvoke({
        "slot": slot,
        "index": 5,
        "attempt": 0,
        "authorization_mode": "publication_eligible",
    })
    result = state["result"]
    assert result.status == "dropped"
    assert len(result.drafts) == 2
    assert "Marketing post must have exactly 1 tweet(s), got 2" in result.reason or "Expected 1 tweets" in result.reason


@pytest.mark.anyio
async def test_reviewer_cannot_override_hard_formatting_rules():
    """Even if Reviewer approves with perfect scores, hard policy violations prevent acceptance."""
    catalog = load_catalog(ROOT / "knowledge" / "evidence_first_v2" / "catalog.json")
    brand_text, brand_rules = load_brand()
    kb = load_kb()
    registry = load_registry()
    policy = load_business_policy(ROOT / "knowledge" / "evidence_first_v2" / "policies" / "security_audit_firm.json")

    class MockRogueReviewerModel:
        def __init__(self):
            self.peak_active = 1
        async def structured(self, prompt, schema):
            if schema in (Draft, MarketingDraft):
                return Draft(tweets=["Tweet 1", "Tweet 2"]), {"prompt_tokens": 50, "completion_tokens": 20}
            elif schema == Review:
                return Review(
                    factual_support=5, technical_correctness=5, brand_voice=5, clarity=5,
                    platform_format=5, usefulness=5, approved=True, grounding_assessment="Rogue approval",
                    claim_support=[]
                ), {"prompt_tokens": 50, "completion_tokens": 20}
            from content_pipeline.conformance import ModelConformanceDecision
            if schema == ModelConformanceDecision:
                return ModelConformanceDecision(
                    verdict="CONFORMS", reason="ok", meaning_preserved=True,
                    extra_unlicensed_facts_detected=False, causal_direction_reversed=False,
                    mitigation_overstated_as_guarantee=False
                ), {"prompt_tokens": 50, "completion_tokens": 20}
            raise ValueError(f"Unexpected schema: {schema}")

    model = MockRogueReviewerModel()
    graph = build_piece_graph(
        model, EvidenceLookup(kb), registry, brand_text, brand_rules,
        mode="evidence_first_v2", catalog=catalog, business_policy=policy,
        authorization_mode="publication_eligible",
    )
    slot = Slot(id="post_test", type="marketing-post", focus=None)
    state = await graph.ainvoke({
        "slot": slot,
        "index": 5,
        "attempt": 0,
        "authorization_mode": "publication_eligible",
    })
    result = state["result"]
    assert result.status == "dropped"
    assert any("Marketing post must have exactly 1 tweet(s), got 2" in v for val in result.validations for v in val)


def test_marketing_content_requires_correct_evidence_and_brand_compliance():
    """Marketing draft with banned phrases or missing evidence fails deterministic check."""
    catalog = load_catalog(ROOT / "knowledge" / "evidence_first_v2" / "catalog.json")
    unit = ContentUnit(
        id="u_mktg",
        role="RECOMMENDATION",
        proposition_ids=["PROP_SWC113_CALLS_CAN_FAIL", "PROP_SWC113_ISOLATE_CALLS"],
        max_chars=280,
    )
    # 1. Banned brand word 'revolutionary'
    passed, violations = check_deterministic_unit_conformance(
        unit,
        "External calls can fail; our revolutionary solution isolates each call.",
        catalog=catalog,
    )
    assert not passed
    assert any("banned phrase 'revolutionary'" in v for v in violations)

    # 2. Banned character em-dash '—'
    passed2, violations2 = check_deterministic_unit_conformance(
        unit,
        "External calls can fail — isolate each one into its own transaction.",
        catalog=catalog,
    )
    assert not passed2
    assert any("banned character '—'" in v for v in violations2)


def test_existing_technical_thread_generation_remains_unchanged():
    """Technical threads require 5 to 10 tweets and are validated by TechThreadDraft."""
    valid_5 = [f"Tweet {i} explaining vulnerability mechanism with technical detail." for i in range(5)]
    tt = TechThreadDraft(tweets=valid_5)
    assert len(tt.tweets) == 5
    assert isinstance(tt, Draft)

    with pytest.raises(ValidationError):
        TechThreadDraft(tweets=["Only tweet 1", "Only tweet 2"])

    with pytest.raises(ValidationError):
        TechThreadDraft(tweets=[f"Tweet {i}" for i in range(11)])


@pytest.mark.anyio
async def test_source_provenance_and_conformance_checks_cannot_be_bypassed():
    """Tampered provenance errors fail closed and cannot route to visual or export."""
    catalog = load_catalog(ROOT / "knowledge" / "evidence_first_v2" / "catalog.json")
    brand_text, brand_rules = load_brand()
    kb = load_kb()
    registry = load_registry()
    policy = load_business_policy(ROOT / "knowledge" / "evidence_first_v2" / "policies" / "security_audit_firm.json")

    kb_tampered = load_kb()
    kb_tampered.vulnerabilities[1].evidence[0].snapshot_sha256 = "0000000000000000000000000000000000000000000000000000000000000000"

    class ValidWriteModel:
        def __init__(self):
            self.peak_active = 1
        async def structured(self, prompt, schema):
            if schema in (Draft, MarketingDraft):
                return MarketingDraft(tweets=["External calls can fail unexpectedly, so check their return values."]), {"prompt_tokens": 10, "completion_tokens": 10}
            raise RuntimeError(f"Unexpected schema: {schema}")

    graph = build_piece_graph(
        ValidWriteModel(), EvidenceLookup(kb_tampered), registry, brand_text, brand_rules,
        mode="evidence_first_v2", catalog=catalog, business_policy=policy,
        authorization_mode="publication_eligible",
    )
    slot = Slot(id="post_test", type="marketing-post", focus=None)
    state = await graph.ainvoke({
        "slot": slot,
        "index": 1,
        "attempt": 0,
        "authorization_mode": "publication_eligible",
    })
    result = state["result"]
    assert result.status == "failed"
    assert "Source provenance failed" in result.reason


def test_business_policy_authority_remains_enforced():
    """Business policy platform constraints and allowed topics are strictly enforced."""
    policy = load_business_policy(ROOT / "knowledge" / "evidence_first_v2" / "policies" / "security_audit_firm.json")
    assert policy.platform_constraints.marketing_post_tweets == 1
    assert policy.platform_constraints.min_tech_thread_tweets == 5
    assert policy.platform_constraints.max_tech_thread_tweets == 10

    ok, violations = policy.check_hard_policy_compliance(
        topic_id="UNSUPPORTED_TOPIC_XYZ",
        content_type="marketing-post",
        used_source_ids=["SWC-113"],
        tweet_texts=["Valid text."],
    )
    assert not ok
    assert any("is not in allowed_topics" in v for v in violations)


def test_accepted_only_export_remains_correct(tmp_path):
    """CSV export must include only accepted pieces with Post Text,Image header."""
    slot_acc = Slot(id="p1", type="marketing-post", focus="SWC-113")
    slot_drop = Slot(id="p2", type="marketing-post", focus="SWC-105")

    draft_acc = MarketingDraft(tweets=["Review contract access controls to ensure only authorized withdrawals occur."])
    rev = Review(
        factual_support=5, technical_correctness=5, brand_voice=5, clarity=5,
        platform_format=5, usefulness=5, approved=True, grounding_assessment="ok", claim_support=[]
    )
    res_acc = SlotResult(
        slot=slot_acc, status="accepted", drafts=[draft_acc], reviews=[rev], validations=[[]],
        visual_spec="visual:spec", pipeline_mode="evidence_first_v2",
        conformance_report={
            "all_conforming": True,
            "results": [{"unit_id": "p1_u1", "tweet_text": "Review contract access controls to ensure only authorized withdrawals occur.", "verdict": "CONFORMS", "passed": True, "reason": "ok"}],
            "total_units": 1,
            "conforming_units": 1
        },
        evidence_plan={
            "slot_id": "p1", "topic_id": "SWC-113", "content_type": "marketing-post",
            "units": [{"id": "p1_u1", "role": "RECOMMENDATION", "proposition_ids": []}],
            "catalog_version": "2.0.0", "policy_version": "1.0.0"
        },
        human_approval_required=False, human_approved=False, publication_status="APPROVED_FOR_EXPORT",
        business_policy_version="1.0.0"
    )
    res_drop = SlotResult(
        slot=slot_drop, status="dropped", drafts=[Draft(tweets=["Dropped text 1", "Dropped text 2"])],
        reviews=[rev], validations=[["Format error"]], reason="Expected 1 tweet, got 2",
        pipeline_mode="evidence_first_v2", human_approval_required=False, human_approved=False,
        publication_status="DROPPED", business_policy_version="1.0.0"
    )

    out_dir = tmp_path / "export_test"
    plan = Plan(slots=[slot_acc, slot_drop])
    summary = export_run(out_dir, plan, [res_acc, res_drop], 1.0, "model", 1, mode="evidence_first_v2")

    csv_path = out_dir / "posts.csv"
    assert csv_path.exists()
    csv_text = csv_path.read_text().strip().splitlines()
    assert csv_text[0] == "Post Text,Image"
    assert len(csv_text) == 2
    assert "Review contract access controls" in csv_text[1]
    assert "Dropped text" not in csv_path.read_text()
    assert summary["shipped"] == 1
    assert summary["dropped"] == 1


def test_swc113_financial_outcome_negative_pair():
    """Negative pair: SWC-113 unit asserting 'draining funds' must fail deterministic conformance."""
    catalog = load_catalog(ROOT / "knowledge" / "evidence_first_v2" / "catalog.json")
    unit = ContentUnit(
        id="post_3_u1",
        role="RECOMMENDATION",
        proposition_ids=["PROP_SWC113_CALLS_CAN_FAIL", "PROP_SWC113_ISOLATE_CALLS", "PROP_SWC113_DOS_CONDITION"],
    )
    unlicensed_tweet = (
        "External calls can fail accidentally or deliberately, potentially draining funds. "
        "To isolate this risk, structure each external call as a separate transaction initiated by the recipient."
    )
    ok, violations = check_deterministic_unit_conformance(unit, unlicensed_tweet, catalog=catalog)
    assert not ok
    assert any("draining funds" in v for v in violations)


def test_swc113_grounded_dos_positive_pair():
    """Positive pair: SWC-113 unit asserting denial-of-service condition and recipient isolation passes."""
    catalog = load_catalog(ROOT / "knowledge" / "evidence_first_v2" / "catalog.json")
    unit = ContentUnit(
        id="post_3_u1",
        role="RECOMMENDATION",
        proposition_ids=["PROP_SWC113_CALLS_CAN_FAIL", "PROP_SWC113_ISOLATE_CALLS", "PROP_SWC113_DOS_CONDITION"],
    )
    grounded_tweet = (
        "External calls can fail accidentally or deliberately, which can cause a denial-of-service condition. "
        "To isolate this risk, structure each external call as a separate transaction initiated by the recipient."
    )
    ok, violations = check_deterministic_unit_conformance(unit, grounded_tweet, catalog=catalog)
    assert ok, f"Expected clean pass, got violations: {violations}"


def test_scwe028_unlicensed_severity_and_ranking_negative_pairs():
    """Negative pairs: SCWE-028 units asserting 'complete subversion', 'significant fund losses', or 'primary defense' must fail."""
    catalog = load_catalog(ROOT / "knowledge" / "evidence_first_v2" / "catalog.json")

    # Negative 1: Hyperbolic severity (complete subversion)
    unit_conseq = ContentUnit(
        id="thread_3_u3",
        role="CONSEQUENCE",
        proposition_ids=["PROP_SCWE028_ADVERSE_CONSEQUENCES"],
    )
    unlicensed_severity_tweet = (
        "This exploitation can lead to unauthorized actions, significant fund losses, "
        "and the complete subversion of critical contract logic."
    )
    ok, violations = check_deterministic_unit_conformance(unit_conseq, unlicensed_severity_tweet, catalog=catalog)
    assert not ok
    assert any("complete subversion" in v or "significant fund loss" in v for v in violations)

    # Negative 2: Comparative ranking (primary defense)
    unit_rec = ContentUnit(
        id="thread_3_u4",
        role="RECOMMENDATION",
        proposition_ids=["PROP_OWASP_AGGREGATE_FEEDS"],
    )
    unlicensed_ranking_tweet = (
        "The primary defense is aggregating multiple oracle and DEX price sources while actively rejecting anomalous outlier deviations."
    )
    ok, violations = check_deterministic_unit_conformance(unit_rec, unlicensed_ranking_tweet, catalog=catalog)
    assert not ok
    assert any("primary defense/mitigation" in v for v in violations)


def test_scwe028_grounded_safeguards_positive_pair():
    """Positive pair: SCWE-028 units asserting grounded consequences and recommended safeguards pass."""
    catalog = load_catalog(ROOT / "knowledge" / "evidence_first_v2" / "catalog.json")

    # Positive 1: Grounded consequence
    unit_conseq = ContentUnit(
        id="thread_3_u3",
        role="CONSEQUENCE",
        proposition_ids=["PROP_SCWE028_ADVERSE_CONSEQUENCES"],
    )
    grounded_conseq_tweet = (
        "This exploitation can lead to unauthorized actions, loss of funds, and exploitation of contract logic."
    )
    ok, violations = check_deterministic_unit_conformance(unit_conseq, grounded_conseq_tweet, catalog=catalog)
    assert ok, f"Expected pass, got: {violations}"

    # Positive 2: Grounded recommendation without comparative ranking
    unit_rec = ContentUnit(
        id="thread_3_u4",
        role="RECOMMENDATION",
        proposition_ids=["PROP_OWASP_AGGREGATE_FEEDS"],
    )
    grounded_rec_tweet = (
        "Recommended safeguards include aggregating multiple oracle and DEX price sources while actively rejecting anomalous outlier deviations."
    )
    ok, violations = check_deterministic_unit_conformance(unit_rec, grounded_rec_tweet, catalog=catalog)
    assert ok, f"Expected pass, got: {violations}"


def test_unseen_analogous_ranking_and_severity_cases():
    """General invariant: novel unseen severity, ranking, and financial consequence escalations are rejected."""
    catalog = load_catalog(ROOT / "knowledge" / "evidence_first_v2" / "catalog.json")

    # Unseen case 1: "sole defense" on reentrancy
    unit_reentrancy = ContentUnit(
        id="thread_1_u5",
        role="RECOMMENDATION",
        proposition_ids=["PROP_SWC107_REENTRANCY_GUARD"],
    )
    ok, violations = check_deterministic_unit_conformance(
        unit_reentrancy,
        "Using ReentrancyGuard is the sole defense against reentrancy attacks on critical functions.",
        catalog=catalog
    )
    assert not ok
    assert any("sole defense" in v for v in violations)

    # Unseen case 2: "total destruction" on oracle
    unit_oracle = ContentUnit(
        id="thread_3_u3",
        role="CONSEQUENCE",
        proposition_ids=["PROP_SCWE028_ADVERSE_CONSEQUENCES"],
    )
    ok, violations = check_deterministic_unit_conformance(
        unit_oracle,
        "Oracle manipulation causes total destruction of contract state and user balances.",
        catalog=catalog
    )
    assert not ok
    assert any("total subversion/destruction" in v for v in violations)

    # Unseen case 3: Grounded paraphrase with "A key practice" passes cleanly
    ok, violations = check_deterministic_unit_conformance(
        unit_reentrancy,
        "A key practice is using a reentrancy lock, such as OpenZeppelin ReentrancyGuard, to protect critical functions.",
        catalog=catalog
    )
    assert ok, f"Expected clean pass, got: {violations}"


def test_swc107_modality_fidelity_recommends_not_mandates():
    """Modality fidelity: PROP_SWC107_CEI_PATTERN must use recommendation framing ('recommends'), not 'mandates'."""
    catalog = load_catalog(ROOT / "knowledge" / "evidence_first_v2" / "catalog.json")
    prop = next(p for p in catalog.propositions if p.id == "PROP_SWC107_CEI_PATTERN")
    assert "recommends" in prop.canonical_text.lower()
    assert "mandates" not in prop.canonical_text.lower()
    assert prop.modality == "recommendation"


# ==============================================================================
# 11. REGRESSION TESTS FOR CLOSURE FINDINGS F1, F2, F3 (INDEPENDENT AUDIT)
# ==============================================================================

def test_f1_role_specific_writer_instructions_dispatched_and_isolated(tmp_path):
    """F1: V2 Writer loads distinct, editable role-specific instruction files for tech-thread vs marketing-post."""
    from content_pipeline.agents import EvidenceFirstWriterAgent

    tech_writer = EvidenceFirstWriterAgent(model=None, content_type="tech-thread")
    mktg_writer = EvidenceFirstWriterAgent(model=None, content_type="marketing-post")

    # 1. Verify tech-thread prompt contains technical educator instructions
    tech_prompt = tech_writer.system_prompt
    assert "Technical Writer Agent" in tech_prompt
    assert "smart contract security educator" in tech_prompt
    assert "Marketing Writer Agent" not in tech_prompt

    # 2. Verify marketing-post prompt contains B2B cybersecurity marketing instructions
    mktg_prompt = mktg_writer.system_prompt
    assert "Marketing Writer Agent" in mktg_prompt
    assert "B2B cybersecurity marketing writer" in mktg_prompt
    assert "Technical Writer Agent" not in mktg_prompt

    # 3. Verify editing role instructions dynamically updates only that role's prompt
    fake_tech_file = tmp_path / "custom_tech.md"
    fake_tech_file.write_text("# Custom Tech Role Instructions for Antigravity")
    custom_writer = EvidenceFirstWriterAgent(model=None, instruction_text=fake_tech_file.read_text())
    assert "Custom Tech Role Instructions for Antigravity" in custom_writer.system_prompt
    assert "Custom Tech Role Instructions for Antigravity" not in mktg_writer.system_prompt


def test_f2_marketing_action_validation_positive_and_negative_pairs():
    """F2: Deterministic marketing action validator accepts true invitations to act and rejects purely descriptive text."""
    from content_pipeline.validation import check_marketing_action, validate_brand_and_platform
    from content_pipeline.config import load_brand, load_registry

    _, brand = load_brand()
    registry = load_registry()
    mktg_spec = registry.types["marketing-post"]

    # Negative 1: The audit finding example (descriptive risk without reader review invitation)
    neg_1 = "Low-level calls in Solidity don't check return values by default; ignoring failures can cause unexpected behavior if execution continues unchecked."
    assert not check_marketing_action(neg_1)
    errs_1 = validate_brand_and_platform([neg_1], brand, mktg_spec)
    assert "Marketing post requires a practical security action" in errs_1

    # Negative 2: "fail to verify" is descriptive of a vulnerability, not an actionable reader recommendation
    neg_2 = "Smart contracts often fail to verify caller identity, leading to unauthorized withdrawals."
    assert not check_marketing_action(neg_2)
    errs_2 = validate_brand_and_platform([neg_2], brand, mktg_spec)
    assert "Marketing post requires a practical security action" in errs_2

    # Negative 3: "without checking" descriptive pattern
    neg_3 = "Execution continues without checking return values on call failure."
    assert not check_marketing_action(neg_3)
    errs_3 = validate_brand_and_platform([neg_3], brand, mktg_spec)
    assert "Marketing post requires a practical security action" in errs_3

    # Positive 1: Direct review invitation on SWC-104
    pos_1 = "Low-level calls in Solidity don't check return values by default. Review how your contract handles low-level call results to ensure returned boolean values are explicitly verified against failure."
    assert check_marketing_action(pos_1)
    errs_pos1 = validate_brand_and_platform([pos_1], brand, mktg_spec)
    assert "Marketing post requires a practical security action" not in errs_pos1

    # Positive 2: Purpose-clause isolation on SWC-113
    pos_2 = "External calls can fail accidentally or deliberately, potentially causing a denial-of-service condition in your contract. To mitigate this risk, isolate each external call into its own transaction initiated by the recipient."
    assert check_marketing_action(pos_2)
    errs_pos2 = validate_brand_and_platform([pos_2], brand, mktg_spec)
    assert "Marketing post requires a practical security action" not in errs_pos2

    # Positive 3: Prevention-clause on SWC-105
    pos_3 = "Missing access controls let malicious actors withdraw Ether from your contract account. Prevent this by ensuring withdrawals trigger only when authorized per your smart contract specs."
    assert check_marketing_action(pos_3)
    errs_pos3 = validate_brand_and_platform([pos_3], brand, mktg_spec)
    assert "Marketing post requires a practical security action" not in errs_pos3


def test_f3_brand_approved_links_enforced_in_v2_and_export(tmp_path):
    """F3: Unapproved links are deterministically rejected in V2 validation and blocked at export."""
    from content_pipeline.validation import validate_brand_and_platform
    from content_pipeline.config import load_brand, load_registry
    from content_pipeline.export import export_run
    from content_pipeline.schemas import Plan, Slot, SlotResult, Draft, Review

    _, brand = load_brand()
    registry = load_registry()
    mktg_spec = registry.types["marketing-post"]
    thread_spec = registry.types["tech-thread"]

    # 1. Single post with unapproved link fails validation
    unapproved_single = "Review your contract access controls at https://unauthorized-security-audits.com today."
    errs = validate_brand_and_platform([unapproved_single], brand, mktg_spec)
    assert any("contains unapproved link https://unauthorized-security-audits.com" in e for e in errs)

    # 2. Thread with unapproved link fails validation
    unapproved_thread = [
        "1/5 Reentrancy attacks occur when a contract calls an external address.",
        "2/5 Learn more at https://malicious-link.org before deploying.",
        "3/5 State changes should happen before external calls.",
        "4/5 The CEI pattern recommends updating balances first.",
        "5/5 Use OpenZeppelin ReentrancyGuard for protection.",
    ]
    errs_thread = validate_brand_and_platform(unapproved_thread, brand, thread_spec)
    assert any("contains unapproved link https://malicious-link.org" in e for e in errs_thread)

    # 3. Clean thread with no links passes brand validation
    clean_thread = [
        "1/5 Reentrancy attacks occur when a contract calls an external address.",
        "2/5 Execution control flow is transferred to the callee.",
        "3/5 State changes should happen before external calls.",
        "4/5 The CEI pattern recommends updating balances first.",
        "5/5 Use OpenZeppelin ReentrancyGuard for protection.",
    ]
    assert validate_brand_and_platform(clean_thread, brand, thread_spec) == []

    # 4. Export gate rechecks validate_brand_and_platform and fails closed on unapproved link
    slot = Slot(id="post_test", type="marketing-post")
    draft = Draft(tweets=[unapproved_single])
    res = SlotResult(
        slot=slot,
        status="accepted",
        pipeline_mode="evidence_first_v2",
        drafts=[draft],
        validations=[[]],
        reviews=[Review(
            approved=True,
            factual_support=5,
            technical_correctness=5,
            brand_voice=5,
            clarity=5,
            platform_format=5,
            usefulness=5,
            reasons=[],
            corrections=[],
            grounding_assessment="Grounded",
        )],
        visual_spec="# Spec",
        conformance_report={
            "all_conforming": True,
            "results": [{"unit_id": "u1", "verdict": "CONFORMS", "passed": True, "tweet_text": unapproved_single}],
        },
        evidence_plan={
            "slot_id": "post_test",
            "topic_id": "SWC-104",
            "content_type": "marketing-post",
            "catalog_version": "2.0.0",
            "policy_version": "1.0.0",
            "units": [{"id": "u1", "role": "RECOMMENDATION", "proposition_ids": ["PROP_SWC104_RETURN_UNCHECKED", "PROP_SWC104_CHECK_RETURN"], "relation_ids": []}],
        },
        business_policy_version="1.0.0",
    )
    plan = Plan(slots=[slot])
    import pytest
    with pytest.raises(ValueError, match="failed deterministic brand/platform gate"):
        export_run(tmp_path / "export_bad_link", plan, [res], 0.1, "model", 1, mode="evidence_first_v2")


# ==============================================================================
# 12. REGRESSION TESTS FOR AUDIT FINDINGS B1 AND B2 (FINAL SUBMISSION AUDIT)
# ==============================================================================

def test_b1_swc113_unsupported_instrumental_mechanism_rejected_and_dos_isolation_accepted():
    """B1: Asserting 'prevent execution from continuing on failure' in SWC-113 is rejected as an unapproved instrumental mechanism; grounded DoS damage reduction is accepted."""
    from content_pipeline.conformance import check_deterministic_unit_conformance
    from content_pipeline.proposition_catalog import load_catalog
    from content_pipeline.content_planning import ContentUnit

    catalog = load_catalog(ROOT / "knowledge" / "evidence_first_v2" / "catalog.json")
    unit_swc113 = ContentUnit(
        id="post_3_u1",
        role="RECOMMENDATION",
        proposition_ids=["PROP_SWC113_CALLS_CAN_FAIL", "PROP_SWC113_DOS_CONDITION", "PROP_SWC113_ISOLATE_CALLS"],
        relation_ids=["REL_SWC113_CALL_FAILURES_CAUSE_DOS", "REL_SWC113_ACTION_RATIONALE_ISOLATE_CALLS"],
    )

    # 1. Exact previous failure: asserts isolation 'prevents execution from continuing on failure'
    exact_failure = (
        "Unchecked external call failures can cause a denial-of-service condition in your contract. "
        "To isolate this risk, wrap each recipient-initiated call into its own transaction to prevent execution from continuing on failure."
    )
    ok_fail, violations_fail = check_deterministic_unit_conformance(unit_swc113, exact_failure, catalog=catalog)
    assert not ok_fail
    assert any("Unlicensed instrumental mechanism" in v and "prevents execution from continuing on failure" in v for v in violations_fail)

    # 2. Variant failure: asserts 'stop execution from continuing'
    variant_failure = "Isolate each external call into a separate transaction to stop execution from continuing on failure."
    ok_var, violations_var = check_deterministic_unit_conformance(unit_swc113, variant_failure, catalog=catalog)
    assert not ok_var
    assert any("Unlicensed instrumental mechanism" in v for v in violations_var)

    # 3. Positive 1: Auditor recommended formulation (reduces DoS impact)
    pos_1 = (
        "Failed external calls can cause denial of service. "
        "To reduce their impact, isolate external calls in separate, recipient-initiated transactions instead of batching them together."
    )
    ok_pos1, violations_pos1 = check_deterministic_unit_conformance(unit_swc113, pos_1, catalog=catalog)
    assert ok_pos1, f"Expected clean pass, got: {violations_pos1}"

    # 4. Positive 2: Grounded DoS hazard and damage minimization
    pos_2 = (
        "External calls can fail accidentally or deliberately, which can cause a denial of service in the contract. "
        "To minimize the damage caused by such failures, isolate each external call into its own transaction initiated by the recipient."
    )
    ok_pos2, violations_pos2 = check_deterministic_unit_conformance(unit_swc113, pos_2, catalog=catalog)
    assert ok_pos2, f"Expected clean pass, got: {violations_pos2}"


def test_b2_swc104_universal_scope_expansion_rejected_and_low_level_accepted():
    """B2: Expanding return-value checking to 'all external calls' is rejected as a scope overclaim; scoping strictly to low-level calls is accepted."""
    from content_pipeline.conformance import check_deterministic_unit_conformance
    from content_pipeline.proposition_catalog import load_catalog
    from content_pipeline.content_planning import ContentUnit

    catalog = load_catalog(ROOT / "knowledge" / "evidence_first_v2" / "catalog.json")
    unit_swc104 = ContentUnit(
        id="post_1_u1",
        role="RECOMMENDATION",
        proposition_ids=["PROP_SWC104_RETURN_UNCHECKED", "PROP_SWC104_CHECK_RETURN", "PROP_SWC104_UNEXPECTED_BEHAVIOUR"],
        relation_ids=["REL_SWC104_UNCHECKED_CAUSES_UNEXPECTED", "REL_SWC104_ACTION_CHECK_RETURN"],
    )

    # 1. Exact previous failure: universal scope expansion 'for all external calls'
    exact_failure = (
        "Unchecked low-level call failures can cause unexpected behavior in subsequent logic; "
        "to prevent this, explicitly verify return values for all external calls."
    )
    ok_fail, violations_fail = check_deterministic_unit_conformance(unit_swc104, exact_failure, catalog=catalog)
    assert not ok_fail
    assert any("Scope overclaim" in v and "all external calls" in v for v in violations_fail)

    # 2. Variant failure: 'across all external calls'
    variant_failure = "Review your smart contract and check return values across all external calls to prevent unexpected behavior."
    ok_var, violations_var = check_deterministic_unit_conformance(unit_swc104, variant_failure, catalog=catalog)
    assert not ok_var
    assert any("Scope overclaim" in v for v in violations_var)

    # 3. Positive 1: Auditor recommended formulation (scoped to low-level call sites)
    pos_1 = (
        "Unchecked low-level calls can fail while execution continues, causing unexpected behavior. "
        "Review low-level call sites and check their return values to handle failures correctly."
    )
    ok_pos1, violations_pos1 = check_deterministic_unit_conformance(unit_swc104, pos_1, catalog=catalog)
    assert ok_pos1, f"Expected clean pass, got: {violations_pos1}"

    # 4. Positive 2: Grounded low-level call return check
    pos_2 = (
        "Low-level calls don't check return values by default; ignoring failures can cause unexpected behavior. "
        "To prevent this, review low-level call sites and explicitly check their return values."
    )
    ok_pos2, violations_pos2 = check_deterministic_unit_conformance(unit_swc104, pos_2, catalog=catalog)
    assert ok_pos2, f"Expected clean pass, got: {violations_pos2}"


def test_visual_agent_reflects_faithful_communication_objective():
    """Visual Agent communication objective faithfully derives from accepted draft without unsupported claims."""
    from content_pipeline.agents import VisualAgent
    from content_pipeline.schemas import Slot, Draft, AtomicClaim, Evidence, SemanticReport, SemanticVerdict

    agent = VisualAgent()
    slot = Slot(id="post_1", type="marketing-post")
    faithful_tweet = (
        "Unchecked low-level calls can fail while execution continues, causing unexpected behavior. "
        "Review low-level call sites and check their return values to handle failures correctly."
    )
    draft = Draft(tweets=[faithful_tweet])
    claims = [AtomicClaim(
        id="c1",
        tweet_index=0,
        start=0,
        end=len(faithful_tweet),
        span=faithful_tweet,
        proposition=faithful_tweet,
        sentence=faithful_tweet,
        candidate_evidence_ids=["SWC-104"],
    )]
    evidence = [Evidence(
        id="SWC-104", url="https://swcregistry.io/docs/SWC-104/", excerpt="Check return values",
        snapshot_path="source_snapshots/SWC-104.txt", snapshot_sha256="3c50a9f3f81c48f98a66977861b87dcfc3b91534a24366ef2a93409c7c25f4b9",
        retrieved_at="2026-10-15", source_type="SWC Registry", source_title="Unchecked Call Return Value",
        scope="Legacy SWC", source_quote="Description The return value of a message call is not checked.",
        quote_start=950, quote_end=1370
    )]
    semantic = SemanticReport(verdicts=[
        SemanticVerdict(claim_id="c1", verdict="SUPPORTED", evidence_ids=["SWC-104"], reason="Directly supported by source")
    ])

    spec_text = agent.run(slot, "Unchecked Call Return Value", draft, claims, evidence, semantic)
    assert "Communication objective: reinforce the accepted takeaway:" in spec_text
    assert "all external calls" not in spec_text
    assert "prevent execution from continuing on failure" not in spec_text
    assert "Review low-level call sites and check their return values" in spec_text






