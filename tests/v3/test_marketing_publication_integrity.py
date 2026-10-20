"""Targeted adversarial and regression test suite for Directive SANADSQUAD_V3_MARKETING_PUBLICATION_INTEGRITY_03.

Enforces:
1. Rejection of unapproved company contact details and synthetic demonstration placeholders.
2. Exact URL verification (permitted domain, live resolution, retrieved evidence excerpt, claim support).
3. Accurate source-to-claim alignment:
   - Rejection of cloud APIs/CI pipeline claims mapped to agent-wallet articles.
   - Distinguishing HTTP 402 signaling from facilitator verification and settlement.
   - Rejection of overbroad coverage claims ("secures the entire connected stack").
4. Meaningful post-format checks:
   - news-reaction requires event/announcement marker, attributable source/date, and analytical interpretation.
   - learning-resource requires why-it-is-worth-reading rationale.
   - Generic advice with a URL is rejected.
5. Strict separation and labeling of demonstration fixtures vs real model outputs.
"""
from __future__ import annotations

import pytest
import re
from pathlib import Path

from content_pipeline.contact_config import (
    CompanyContactConfig,
    load_company_contact,
    is_synthetic_contact,
    SYNTHETIC_DEMO_CONTACTS,
)
from content_pipeline.marketing_format import (
    MarketingFormat,
    validate_marketing_format,
)
from content_pipeline.marketing_policy import (
    validate_marketing_claims,
    validate_contact_cta,
)
from content_pipeline.marketing_planner import (
    MarketingSlotPlanner,
    Slot,
)
from content_pipeline.research.config import load_sources_config
from content_pipeline.research.provider import FixtureResearchProvider
from content_pipeline.export import export_run
from content_pipeline.schemas import (
    Plan,
    SlotResult,
    Draft,
    Evidence,
    BrandRules,
    WriterConfig,
)


# ==============================================================================
# 1. Reject Unapproved Company Contact Details & Fail-Closed Gating
# ==============================================================================

def test_unapproved_company_contact_on_disk_fails_closed():
    """[HANDWRITTEN_TEST_VECTOR] company-contact.json on disk has approved=false; planner must not allocate CTAs."""
    contact_cfg = load_company_contact()
    assert contact_cfg.approved is False
    assert not contact_cfg.is_operational()

    slots = [
        Slot(id="post_1", type="marketing-post", focus="post-audit deployment drift"),
        Slot(id="post_2", type="marketing-post", focus="prompt injection"),
        Slot(id="post_3", type="marketing-post", focus="x402 payment signaling"),
    ]
    plan = MarketingSlotPlanner.plan_weekly_slots(slots)
    # Fail-closed: 0 marketing slots have has_cta when contacts are unapproved
    assert sum(1 for s in plan.slots if s.has_cta) == 0


def test_synthetic_demonstration_placeholders_rejected_for_publication():
    """[HANDWRITTEN_TEST_VECTOR] contact@sanadsquad.com and +1-555-0199 must never be exported in publication content."""
    for demo_contact in SYNTHETIC_DEMO_CONTACTS:
        assert is_synthetic_contact(f"Contact us at {demo_contact}") is True


def test_export_rejects_unapproved_contact_details(tmp_path):
    """[HANDWRITTEN_TEST_VECTOR] export_run fails closed if post contains contact details when disk approval is false."""
    plan = Plan(slots=[Slot(id="post_1", type="marketing-post", focus="web3")])
    result = SlotResult(
        slot=plan.slots[0],
        status="accepted",
        topic="web3",
        source_ids=["ev_1"],
        drafts=[Draft(tweets=["Review protocol access controls and invariant assertions. Contact SanadSquad. Email: contact@sanadsquad.com | Phone: +1-555-0199"])],
        evidence=[Evidence(id="ev_1", url="https://solana.com/docs/programs/verified-builds", excerpt="verified builds")],
        visual_spec="spec:visual_specs/test.md",
        authorization_mode="publication_eligible",
        pipeline_mode="evidence_first_v2",
        conformance_report={
            "all_conforming": True,
            "results": [{"unit_id": "u1", "verdict": "CONFORMS", "passed": True, "tweet_text": "Review protocol access controls and invariant assertions. Contact SanadSquad. Email: contact@sanadsquad.com | Phone: +1-555-0199"}],
        },
        evidence_plan={
            "slot_id": "post_1",
            "topic_id": "service_positioning",
            "content_type": "marketing-post",
            "catalog_version": "2.0.0",
            "policy_id": "security_audit_firm",
            "policy_version": "1.0.0",
            "authorization_mode": "publication_eligible",
            "units": [{"id": "u1", "role": "RECOMMENDATION", "proposition_ids": [], "max_chars": 280, "guidance": "test"}],
        },
    )

    with pytest.raises(ValueError, match="demonstration placeholder"):
        export_run(
            output=tmp_path / "illegal_export",
            plan=plan,
            results=[result],
            elapsed=1.0,
            model_name="qwen3.5:4b",
            peak_active=1,
            mode="v3",
        )


# ==============================================================================
# 2. Verify Every Publication URL
# ==============================================================================

def test_dead_and_synthetic_urls_rejected_by_export(tmp_path):
    """[HANDWRITTEN_TEST_VECTOR] Posts citing 404 or unretrieved URLs must be rejected at export."""
    sources_cfg = load_sources_config()

    # The 404 synthetic URL from the previous broken demo
    fake_url = "https://simonwillison.net/2026/May/18/agentic-wallet-security-policy"
    plan = Plan(slots=[Slot(id="post_1", type="marketing-post", focus="agentic")])
    result = SlotResult(
        slot=plan.slots[0],
        status="accepted",
        topic="agentic",
        source_ids=["ev_1"],
        drafts=[Draft(tweets=[f"OWASP reported prompt injection risk in agentic tools: {fake_url}"])],
        evidence=[Evidence(id="ev_1", url="https://genai.owasp.org/initiatives/agentic-security-initiative/", excerpt="prompt injection")],
        fetched_urls=["https://genai.owasp.org/initiatives/agentic-security-initiative/"],
        visual_spec="spec:visual_specs/test.md",
        pipeline_mode="evidence_first_v2",
        conformance_report={
            "all_conforming": True,
            "results": [{"unit_id": "u1", "verdict": "CONFORMS", "passed": True, "tweet_text": f"OWASP reported prompt injection risk in agentic tools: {fake_url}"}],
        },
        evidence_plan={
            "slot_id": "post_1",
            "topic_id": "service_positioning",
            "content_type": "marketing-post",
            "catalog_version": "2.0.0",
            "policy_id": "security_audit_firm",
            "policy_version": "1.0.0",
            "authorization_mode": "publication_eligible",
            "units": [{"id": "u1", "role": "RECOMMENDATION", "proposition_ids": [], "max_chars": 280, "guidance": "test"}],
        },
    )

    with pytest.raises(ValueError, match=r"(?:unverified URL|unapproved link)"):
        export_run(
            output=tmp_path / "fake_url_export",
            plan=plan,
            results=[result],
            elapsed=1.0,
            model_name="mock_test",
            peak_active=1,
            mode="v3",
        )


def test_unallowlisted_domains_rejected_by_sources_config():
    """[HANDWRITTEN_TEST_VECTOR] Domains not on the allowlist or on global denylist are rejected."""
    sources_cfg = load_sources_config()
    assert sources_cfg.is_domain_allowed("https://attacker-domain.com/exploit", "web3-security") is False
    assert sources_cfg.is_domain_allowed("https://medium.com/post-mortem", "web3-security") is False
    assert sources_cfg.is_domain_allowed("https://x402.org/specs/fake", "pentesting") is False


# ==============================================================================
# 3. Source-to-Claim Alignment & Service-Positioning Guardrails
# ==============================================================================

def test_source_to_claim_alignment_rejects_cloud_api_claims_with_agent_source():
    """[HANDWRITTEN_TEST_VECTOR] Post claiming cloud APIs and CI pipelines with an agent wallet source must be rejected."""
    bad_tweet = (
        "Attackers target connected cloud APIs and CI pipelines before touching on-chain code. "
        "See verified details: https://simonwillison.net/2023/Apr/14/worst-that-can-happen/"
    )
    errors = validate_marketing_claims([bad_tweet])
    assert any("Source-to-claim mismatch" in err and "cloud APIs" in err for err in errors)


def test_accurate_x402_specification_mechanics_enforced():
    """[HANDWRITTEN_TEST_VECTOR] Reject claiming HTTP 402 is used for facilitator settlement."""
    inaccurate_tweet = (
        "x402 protocol uses HTTP 402 for facilitator settlement. "
        "Details: https://github.com/coinbase/x402"
    )
    errors = validate_marketing_claims([inaccurate_tweet])
    assert any("Inaccurate x402 specification claim" in err for err in errors)

    accurate_tweet = (
        "Coinbase x402 specification defines HTTP 402 signaling while facilitators verify and settle payments. "
        "Details: https://github.com/coinbase/x402"
    )
    errors_ok = validate_marketing_claims([accurate_tweet])
    assert not any("Inaccurate x402 specification claim" in err for err in errors_ok)


def test_overbroad_coverage_guarantee_rejected():
    """[HANDWRITTEN_TEST_VECTOR] Rejection of claims that SanadSquad 'secures the entire connected stack'."""
    overbroad_tweet = (
        "Auditing smart contracts is necessary, but protocols fail when frontends get hijacked. "
        "SanadSquad secures the entire connected stack."
    )
    errors = validate_marketing_claims([overbroad_tweet])
    assert any("Overbroad coverage claim" in err for err in errors)

    compliant_tweet = (
        "Auditing smart contracts is necessary, but protocols also face infrastructure and frontend risks. "
        "SanadSquad audits smart contracts and assesses deployment infrastructure."
    )
    errors_ok = validate_marketing_claims([compliant_tweet])
    assert not any("Overbroad coverage claim" in err for err in errors_ok)


# ==============================================================================
# 4. Meaningful Post-Format Validation
# ==============================================================================

def test_generic_security_advice_with_url_rejected_as_news_reaction():
    """[HANDWRITTEN_TEST_VECTOR] Generic advice with a URL lacks event, attribution, and interpretation."""
    generic_tweet = (
        "Attackers target connected cloud APIs and CI pipelines before touching on-chain code. "
        "See verified details: https://top10.owasp.org/"
    )
    errors = validate_marketing_format(
        tweets=[generic_tweet],
        selected_format=MarketingFormat.NEWS_REACTION,
        fetched_urls=["https://top10.owasp.org/"],
    )
    assert any("news-reaction" in err.lower() and "lacks required components" in err.lower() for err in errors)


def test_valid_news_reaction_accepted():
    """[HANDWRITTEN_TEST_VECTOR] News reaction with event, attribution, and interpretation is accepted."""
    valid_news = (
        "OWASP reported that software integrity failures in CI/CD pipelines allow attackers to alter deployment artifacts. "
        "This disclosure demonstrates why frontend build environments require penetration testing: https://top10.owasp.org/"
    )
    errors = validate_marketing_format(
        tweets=[valid_news],
        selected_format=MarketingFormat.NEWS_REACTION,
        fetched_urls=["https://top10.owasp.org/"],
    )
    assert errors == []


def test_generic_advice_rejected_as_learning_resource():
    """[HANDWRITTEN_TEST_VECTOR] Learning resource must explain why the link is worth reading."""
    generic_resource = (
        "Always review payment facilitator settlement parameters. "
        "Details: https://github.com/coinbase/x402"
    )
    errors = validate_marketing_format(
        tweets=[generic_resource],
        selected_format=MarketingFormat.LEARNING_RESOURCE,
        fetched_urls=["https://github.com/coinbase/x402"],
    )
    assert any("learning-resource" in err.lower() and "must explain why" in err.lower() for err in errors)


def test_valid_learning_resource_accepted():
    """[HANDWRITTEN_TEST_VECTOR] Learning resource with educational utility rationale is accepted."""
    valid_resource = (
        "Coinbase x402 specification defines HTTP 402 payment signaling while facilitators handle settlement. "
        "Excellent breakdown of session mechanics: https://github.com/coinbase/x402"
    )
    errors = validate_marketing_format(
        tweets=[valid_resource],
        selected_format=MarketingFormat.LEARNING_RESOURCE,
        fetched_urls=["https://github.com/coinbase/x402"],
    )
    assert errors == []
