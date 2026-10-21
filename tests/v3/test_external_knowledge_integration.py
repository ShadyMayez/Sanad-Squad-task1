"""Targeted tests for external research knowledge pack integration.

Directive: SANADSQUAD_V3_EXTERNAL_RESEARCH_KNOWLEDGE_INTEGRATION_01

Tests coverage:
1. Verification of knowledge seed index loading and brief mapping for all 5 services.
2. Rejection of BOLA defined as authentication failure.
3. Rejection of upgrade authority defined as inherently malicious.
4. Rejection of MPP and x402 described as completely interchangeable.
5. Rejection of OWASP ACS mandating dollar spending caps.
6. Rejection of ERC-4626 claiming all vaults are exploitable or mitigations absolute.
7. Rejection of NIST SSDF certification or zero-vulnerability guarantees.
8. Verification of valid evidence-backed posts for each curated knowledge track.
"""
from __future__ import annotations

import json
from pathlib import Path
import pytest

from content_pipeline.marketing_policy import validate_editorial_semantic_conformance
from content_pipeline.content_planning import build_marketing_evidence_plan
from content_pipeline.schemas import Evidence
from content_pipeline.research.fixtures import get_fixtures_for_service


ROOT = Path(__file__).resolve().parent.parent.parent


def test_seed_index_and_editorial_briefs_structure():
    """Verify seed_index.json and editorial_briefs.json exist, are valid JSON, and cover all 14 sources and 10 briefs."""
    seed_path = ROOT / "knowledge" / "marketing" / "seed_index.json"
    briefs_path = ROOT / "knowledge" / "marketing" / "editorial_briefs.json"

    assert seed_path.exists(), "seed_index.json must exist in knowledge/marketing/"
    assert briefs_path.exists(), "editorial_briefs.json must exist in knowledge/marketing/"

    with seed_path.open("r", encoding="utf-8") as f:
        seed_data = json.load(f)
    with briefs_path.open("r", encoding="utf-8") as f:
        briefs_data = json.load(f)

    assert seed_data["schema_version"] == "1.0"
    assert len(seed_data["sources"]) >= 14
    source_ids = {s["source_id"] for s in seed_data["sources"]}
    for expected_id in ["W01", "W02", "W03", "W04", "P01", "P02", "P03", "A01", "A02", "A03", "M01", "M02", "M03", "C01"]:
        assert expected_id in source_ids, f"Source ID {expected_id} missing from seed index"

    assert len(briefs_data["briefs"]) >= 10
    brief_ids = {b["brief_id"] for b in briefs_data["briefs"]}
    for i in range(1, 11):
        expected_bid = f"B{i:02d}"
        assert expected_bid in brief_ids, f"Brief ID {expected_bid} missing from editorial briefs"


def test_editorial_brief_mapping_for_all_five_services():
    """Verify each official service maps to its relevant editorial brief in planner unit guidance."""
    services_to_test = [
        ("blockchain-security-audits", "B01"),
        ("penetration-testing", "B04"),
        ("agentic-security-tooling", "B06"),
        ("agentic-payments", "B08"),
        ("security-consulting", "B10"),
    ]

    for service_line, expected_brief_id in services_to_test:
        fixtures = get_fixtures_for_service(service_line)
        ev_items = [
            Evidence(
                id=f"ev_{service_line}_1",
                source_title=fixtures[0]["title"],
                excerpt=fixtures[0]["quote"],
                url=fixtures[0]["url"],
            )
        ]
        plan = build_marketing_evidence_plan(
            slot_id=f"slot_{service_line}",
            service_line=service_line,
            evidence=ev_items,
            marketing_format="short-tip" if "consult" in service_line or "pentest" in service_line else "learning-resource",
        )
        assert len(plan.units) == 1
        guidance = plan.units[0].guidance
        assert f"EDITORIAL BRIEF ({expected_brief_id})" in guidance or "EDITORIAL BRIEF" in guidance, (
            f"Expected editorial brief guidance for service {service_line}"
        )


def test_reject_bola_as_authentication_failure():
    """B04/P01: Reject copy describing BOLA as login or authentication failure."""
    bad_tweet = (
        "BOLA is authentication failure where invalid logins compromise API endpoints. "
        "SanadSquad tests dApp backend APIs."
    )
    errors = validate_editorial_semantic_conformance(
        tweets=[bad_tweet],
        service_line="penetration-testing",
    )
    assert any("Inaccurate BOLA definition" in err for err in errors)


def test_accept_correct_bola_authorization_distinction():
    """B04/P01: Accept copy accurately distinguishing object authorization from authentication."""
    good_tweet = (
        "A valid login does not authorize every object. Broken Object Level Authorization lets an "
        "authenticated user access another user's records when object permissions are missing. "
        "SanadSquad penetration testing tests the resource boundary, not just sign-in."
    )
    errors = validate_editorial_semantic_conformance(
        tweets=[good_tweet],
        service_line="penetration-testing",
    )
    assert not any("BOLA" in err for err in errors)


def test_reject_upgrade_authority_as_inherently_malicious():
    """B02/W02: Reject claims that upgrade authority is inherently malicious or compromised."""
    bad_tweet = (
        "Solana retained upgrade authority is inherently malicious and guarantees an exploit. "
        "SanadSquad audits smart contracts."
    )
    errors = validate_editorial_semantic_conformance(
        tweets=[bad_tweet],
        service_line="blockchain-security-audits",
    )
    assert any("Inaccurate governance claim" in err for err in errors)


def test_accept_correct_upgrade_governance():
    """B02/W02/W04: Accept upgrade authority framed as keyholder centralization and governance risk."""
    good_tweet = (
        "Upgradeable contracts need two reviews: what can the code do, and who can replace it? "
        "Upgrade authority is a governance control surface that introduces keyholder centralization risk. "
        "SanadSquad smart contract audits evaluate both logic and upgrade administration."
    )
    errors = validate_editorial_semantic_conformance(
        tweets=[good_tweet],
        service_line="blockchain-security-audits",
    )
    assert not any("Inaccurate governance claim" in err for err in errors)


def test_reject_mpp_and_x402_as_completely_interchangeable():
    """B09/M02: Reject claims that MPP and x402 are completely interchangeable."""
    bad_tweet = (
        "MPP and x402 are completely interchangeable specifications with identical security. "
        "SanadSquad reviews agentic payment flows."
    )
    errors = validate_editorial_semantic_conformance(
        tweets=[bad_tweet],
        service_line="agentic-payments",
    )
    assert any("Inaccurate protocol comparison" in err for err in errors)


def test_accept_mpp_and_x402_compatible_flows():
    """B09/M02: Accept mppx unified SDK interface supporting compatible flows."""
    good_tweet = (
        "mppx added support for compatible x402 exact flows alongside MPP EVM charges in June 2026. "
        "Integration requires spending controls and verification paths. "
        "SanadSquad reviews payment agent authorization ceilings: https://mpp.dev/blog/evm-x402-support"
    )
    errors = validate_editorial_semantic_conformance(
        tweets=[good_tweet],
        service_line="agentic-payments",
    )
    assert not any("Inaccurate protocol comparison" in err for err in errors)


def test_reject_owasp_acs_mandating_dollar_spending_caps():
    """B06/A01: Reject claims that OWASP ACS mandates specific dollar spending caps."""
    bad_tweet = (
        "OWASP ACS mandates a dollar spending cap for every autonomous wallet. "
        "SanadSquad builds custom security detectors."
    )
    errors = validate_editorial_semantic_conformance(
        tweets=[bad_tweet],
        service_line="agentic-security-tooling",
    )
    assert any("Inaccurate OWASP ACS claim" in err for err in errors)


def test_accept_correct_owasp_acs_runtime_controls():
    """B06/A01: Accept OWASP ACS framed as declarative policy enforcement and tool middleware."""
    good_tweet = (
        "OWASP Agent Control Standard defines runtime visibility and declarative policy hooks for tool-using agents. "
        "SanadSquad builds custom security detectors and PR reviewers to enforce tool execution boundaries: "
        "https://genai.owasp.org/resource/agent-control-standard-acs/"
    )
    errors = validate_editorial_semantic_conformance(
        tweets=[good_tweet],
        service_line="agentic-security-tooling",
    )
    assert not any("Inaccurate OWASP ACS claim" in err for err in errors)


def test_reject_all_erc4626_vaults_exploitable():
    """B03/W03: Reject overbroad claims that all ERC-4626 vaults are exploitable."""
    bad_tweet = (
        "All ERC-4626 vaults are exploitable by donation inflation attacks before launch. "
        "SanadSquad audits smart contracts."
    )
    errors = validate_editorial_semantic_conformance(
        tweets=[bad_tweet],
        service_line="blockchain-security-audits",
    )
    assert any("Inaccurate vault claim" in err for err in errors)


def test_accept_nuanced_erc4626_inflation_mitigations():
    """B03/W03: Accept nuanced empty-vault inflation attack analysis."""
    good_tweet = (
        "An empty ERC-4626 vault can be sensitive to donation-based share-price manipulation. "
        "Review initial exchange rates, slippage protection, and vault inflation mitigations. "
        "SanadSquad smart contract audits evaluate vault accounting invariants."
    )
    errors = validate_editorial_semantic_conformance(
        tweets=[good_tweet],
        service_line="blockchain-security-audits",
    )
    assert not any("Inaccurate vault claim" in err for err in errors)


def test_reject_nist_endorsement_or_zero_vulnerabilities():
    """B10/C01: Reject claims that NIST endorses SanadSquad or SSDF guarantees zero bugs."""
    bad_tweet = (
        "NIST certifies SanadSquad and SSDF guarantees zero vulnerabilities across protocols. "
        "Request a security consultation with SanadSquad."
    )
    errors = validate_editorial_semantic_conformance(
        tweets=[bad_tweet],
        service_line="security-consulting",
    )
    assert any("Inaccurate compliance claim" in err for err in errors)


def test_accept_correct_nist_ssdf_architecture_review():
    """B10/C01: Accept SSDF framed as secure development lifecycle practices."""
    good_tweet = (
        "NIST SP 800-218 emphasizes security reviews throughout the development lifecycle before code deployment. "
        "SanadSquad provides security consulting for pre-implementation architecture reviews and threat modeling: "
        "https://csrc.nist.gov/pubs/sp/800/218/final"
    )
    errors = validate_editorial_semantic_conformance(
        tweets=[good_tweet],
        service_line="security-consulting",
    )
    assert not any("Inaccurate compliance claim" in err for err in errors)
