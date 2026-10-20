"""Tests for Directive SANADSQUAD_V3_MARKETING_RESEARCH_QUALITY_02: Marketing Intelligence Enhancement.

Enforces:
1. Service positioning accuracy: All 4 service lines are defined with target customers, technical mechanisms, and verified service offerings.
2. Source-to-customer-problem mappings: Every service line maps real security concerns to verified technical research.
3. Corrected format taxonomy: 5 eligible single-tweet formats, marketing-thread disabled under marketing-post contract, format-specific link rules.
4. Complete banned vocabulary: All 14 original assignment banned terms plus all retained buzzwords (23+ terms) with word-boundary checks.
5. Proper source attribution: External incidents and third-party findings are properly attributed; source links preserved where required.
6. Company contact approval: Contact details only published when approved; all 5 commercial offerings supported.
7. Commercial CTA limits: <= 1/3 weekly marketing posts with CTAs, max 1 CTA per post, CTAs strictly optional.
8. Unsupported superiority claims: Rejection of superlative claims (e.g. "industry-leading", "best security firm").
9. Unverified company experience: Rejection of claims that SanadSquad audited external incident targets (e.g. Bybit, Safe, Solana) without audit records.
10. Separation of facts, opinions, and service positioning: Fact vs interpretation vs company positioning vs commercial CTA.
"""
from __future__ import annotations

import json
import pytest
from pathlib import Path

from content_pipeline.config import ROOT, load_brand, load_registry
from content_pipeline.contact_config import (
    CompanyContactConfig,
    load_company_contact,
    build_contextual_cta,
)
from content_pipeline.marketing_format import (
    MarketingFormat,
    FORMAT_SPECS,
    validate_marketing_format,
)
from content_pipeline.marketing_policy import (
    MarketingPolicy,
    load_marketing_policy,
    detect_commercial_cta,
    validate_marketing_claims,
    validate_contact_cta,
)
from content_pipeline.writing_quality import (
    validate_writing_quality,
    detect_banned_vocabulary,
    load_writing_quality_rules,
)
from content_pipeline.research.config import load_sources_config
from content_pipeline.research.provider import FixtureResearchProvider, LiveResearchProvider
from content_pipeline.research.service import ResearchService
from content_pipeline.validation import validate_piece_deterministic


# ==============================================================================
# 1. Service Positioning Accuracy
# ==============================================================================

def test_service_positioning_all_four_lines_documented():
    """Positioning guide docs/marketing/SERVICE_RESEARCH_AND_POSITIONING.md must cover all 4 service lines."""
    guide_path = ROOT / "docs" / "marketing" / "SERVICE_RESEARCH_AND_POSITIONING.md"
    assert guide_path.exists(), "SERVICE_RESEARCH_AND_POSITIONING.md must exist"
    content = guide_path.read_text(encoding="utf-8")

    # All 4 services present
    assert "Web3 Security (EVM & SVM)" in content
    assert "Web2 Pentesting" in content
    assert "Agentic Security and Red Teaming" in content
    assert "Agentic Payment Protocols" in content

    # Key mechanisms and distinctions
    assert "SVM" in content
    assert "Verified Builds" in content or "verified builds" in content
    assert "invariant" in content.lower()
    assert "Source Verification vs Security Audit vs Ongoing Monitoring" in content or "monitoring" in content.lower()
    assert "Bybit/Safe" in content or "bybit" in content.lower()
    assert "OWASP" in content
    assert "Prompt injection" in content or "prompt injection" in content.lower()
    assert "x402" in content
    assert "MPP" in content


def test_service_positioning_policy_services_match():
    """Policy service lines match the 4 official offerings."""
    policy = load_marketing_policy()
    expected = {"web3-security", "pentesting", "agentic-security", "agentic-payments"}
    assert set(policy.service_lines) == expected


# ==============================================================================
# 2. Source-to-Customer-Problem Mappings
# ==============================================================================

def test_source_to_customer_problem_mappings():
    """Sources configuration must have verified domains for all 4 service lines."""
    sources_cfg = load_sources_config()
    for s_line in ["web3-security", "pentesting", "agentic-security", "agentic-payments"]:
        domains = sources_cfg.get_service_allowlist(s_line)
        assert len(domains) >= 3, f"Service line {s_line} must have at least 3 allowlisted research domains"

    # Specific key domains per service line
    assert "solana.com" in sources_cfg.get_service_allowlist("web3-security")
    assert "owasp.org" in sources_cfg.get_service_allowlist("pentesting")
    assert "genai.owasp.org" in sources_cfg.get_service_allowlist("agentic-security")
    assert "x402.org" in sources_cfg.get_service_allowlist("agentic-payments") or "stripe.com" in sources_cfg.get_service_allowlist("agentic-payments")


def test_research_fixtures_cover_four_service_problems():
    """Research fixtures contain verified grounding for all 4 service scenarios."""
    prov = FixtureResearchProvider(load_sources_config())
    web3_fix = prov.search("verified builds", "web3-security")
    assert len(web3_fix) >= 1
    assert any("solana.com" in r.url for r in web3_fix)

    web2_fix = prov.search("frontend signing", "pentesting")
    assert len(web2_fix) >= 1
    assert any("owasp.org" in r.url for r in web2_fix)

    agent_fix = prov.search("prompt injection", "agentic-security")
    assert len(agent_fix) >= 1
    assert any("agentic" in r.title.lower() for r in agent_fix)

    pay_fix = prov.search("x402 mpp", "agentic-payments")
    assert len(pay_fix) >= 1
    assert any("x402" in r.url for r in pay_fix)


# ==============================================================================
# 3. Corrected Format Taxonomy
# ==============================================================================

def test_corrected_format_taxonomy():
    """Exactly five single-tweet formats exist; thread is disabled for marketing-post."""
    formats = [
        MarketingFormat.SHORT_TIP,
        MarketingFormat.DIFFERENTIATION,
        MarketingFormat.SERVICE_OVERVIEW,
        MarketingFormat.NEWS_REACTION,
        MarketingFormat.LEARNING_RESOURCE,
    ]
    for fmt in formats:
        assert fmt in FORMAT_SPECS
        assert FORMAT_SPECS[fmt].max_tweets == 1

    # Marketing thread is marked as multi-tweet and forbidden for single-tweet contract
    thread_spec = FORMAT_SPECS[MarketingFormat.MARKETING_THREAD]
    assert thread_spec.max_tweets == 7
    assert thread_spec.max_tweets > 1
    errs = validate_marketing_format(["Post 1", "Post 2"], selected_format=MarketingFormat.MARKETING_THREAD)
    assert any("reserved future content type" in e for e in errs)


def test_format_link_constraints():
    """Link constraints are enforced strictly per format."""
    # short-tip: strictly NO link
    tip_errs = validate_marketing_format(
        ["Auditing verifies logic at rest. Verify runtime invariants on-chain: https://solana.com/docs"],
        selected_format=MarketingFormat.SHORT_TIP,
    )
    assert any("must not contain any links" in e for e in tip_errs)

    clean_tip = validate_marketing_format(
        ["Auditing verifies logic at rest, but runtime invariants guard against post-audit upgrade drift."],
        selected_format=MarketingFormat.SHORT_TIP,
    )
    assert clean_tip == []

    # news-reaction & learning-resource: MUST have link
    news_no_link = validate_marketing_format(
        ["Bybit infrastructure incident highlights the need for frontend signing calldata validation."],
        selected_format=MarketingFormat.NEWS_REACTION,
    )
    assert any("requires an authorized source link" in e for e in news_no_link)

    learn_no_link = validate_marketing_format(
        ["Guide to comparative settlement mechanics between x402 and Machine Payments Protocol."],
        selected_format=MarketingFormat.LEARNING_RESOURCE,
    )
    assert any("requires an authorized source link" in e for e in learn_no_link)


# ==============================================================================
# 4. Complete Banned Vocabulary
# ==============================================================================

def test_complete_banned_vocabulary_all_terms():
    """All 14 original assignment banned terms plus all retained terms are rejected."""
    # 14 original assignment terms:
    original_terms = [
        "delve", "testament", "tapestry", "vital", "crucial", "beacon",
        "game-changer", "game changer", "synergy", "unleash", "elevate",
        "paramount", "revolutionize", "cornerstone", "foster"
    ]
    # Retained terms:
    retained_terms = [
        "leverage", "underscore", "pivotal", "realm", "landscape",
        "seamless", "robust", "navigate", "ever-evolving"
    ]
    all_terms = original_terms + retained_terms

    rules = load_writing_quality_rules()
    configured_banned = set(rules.get("banned_vocabulary", []))
    for term in all_terms:
        assert term in configured_banned, f"Term '{term}' must be present in writing-quality-rules.json"

    # Test detection with word boundaries
    for term in all_terms:
        test_sentence = f"We must {term} our security methodology across the protocol."
        errs = detect_banned_vocabulary(test_sentence, rules)
        assert len(errs) >= 1, f"Term '{term}' should be detected as banned vocabulary"


def test_banned_vocabulary_word_boundaries_no_false_positives():
    """Legitimate technical terms containing banned substrings must not be falsely flagged."""
    rules = load_writing_quality_rules()
    # 'deliver' does not flag 'delve'
    assert detect_banned_vocabulary("We deliver verified bytecode.", rules) == []
    # 'clever' does not flag 'leverage'
    assert detect_banned_vocabulary("A clever invariant check prevents griefing.", rules) == []


# ==============================================================================
# 5. Proper Source Attribution
# ==============================================================================

def test_proper_source_attribution_and_preservation():
    """External research and incidents must cite verified sources and maintain attribution."""
    sources_cfg = load_sources_config()
    fetcher = FixtureResearchProvider(sources_cfg)

    # Valid source from allowlist
    solana_page = fetcher.fetch("https://solana.com/docs/programs/verified-builds", "web3-security")
    assert solana_page.eligible_for_public_posting is True
    assert solana_page.sha256_checksum != ""
    assert "Verified Builds" in solana_page.title

    # Unverified external domain cannot be fetched for public posting
    unverified_page = fetcher.fetch("https://unverified-hacker-blog.xyz/post", "web3-security")
    assert unverified_page.eligible_for_public_posting is False
    assert unverified_page.http_status == 403


# ==============================================================================
# 6. Company Contact Approval & Offerings
# ==============================================================================

def test_company_contact_approval_gating():
    """Contact details are published ONLY when approval_status is approved."""
    # When approved:
    approved_cfg = CompanyContactConfig(
        company_name="SanadSquad",
        business_inquiries_email="frank@sanadsquad.com",
        contact_form_url="https://sanadsquad.com/contact/",
        telegram="@castle_chain",
        x_handle="@SanadSquad",
        approved=True,
    )
    assert approved_cfg.is_operational() is True
    cta = build_contextual_cta("web3-security", approved_cfg, offering_type="web3-audit")
    assert "frank@sanadsquad.com" in cta

    # When unapproved (e.g. approved=False):
    unapproved_cfg = CompanyContactConfig(
        company_name="SanadSquad",
        business_inquiries_email="frank@sanadsquad.com",
        approved=False,
    )
    assert unapproved_cfg.is_operational() is False
    with pytest.raises(ValueError):
        build_contextual_cta("web3-security", unapproved_cfg, offering_type="web3-audit")

    # When unapproved, publishing contact info causes validation failure
    errs = validate_contact_cta(
        ["Discuss your smart contract audit with SanadSquad: frank@sanadsquad.com"],
        contact_config=unapproved_cfg,
        allow_cta=True,
    )
    assert any("approval status is false" in e for e in errs)


def test_five_commercial_offerings_supported():
    """build_contextual_cta supports all 5 specified commercial offerings."""
    cfg = CompanyContactConfig(
        company_name="SanadSquad",
        business_inquiries_email="frank@sanadsquad.com",
        contact_form_url="https://sanadsquad.com/contact/",
        approved=True,
    )
    offerings = [
        ("security-consultation", "Request a security consultation with SanadSquad"),
        ("web3-audit", "discuss an audit"),
        ("pentest-assessment", "penetration test"),
        ("agentic-security-review", "AI detectors"),
        ("agentic-payments-review", "payment agent"),
    ]
    for off_type, expected_phrase in offerings:
        cta = build_contextual_cta(off_type, cfg, offering_type=off_type)
        assert expected_phrase.lower() in cta.lower()
        assert "frank@sanadsquad.com" in cta


# ==============================================================================
# 7. Commercial CTA Limits
# ==============================================================================

def test_commercial_cta_limits_per_post_and_week():
    """Enforce at most 1 CTA per post and at most 1/3 of weekly posts with CTAs."""
    approved_cfg = CompanyContactConfig(
        company_name="SanadSquad",
        business_inquiries_email="frank@sanadsquad.com",
        contact_form_url="https://sanadsquad.com/contact/",
        approved=True,
    )

    # Multiple CTAs in single post rejected
    multi_cta = [
        "Work with SanadSquad to audit your contracts. Also contact SanadSquad: frank@sanadsquad.com."
    ]
    errs = validate_contact_cta(multi_cta, contact_config=approved_cfg, allow_cta=True)
    assert any("multiple CTAs" in e or "Maximum 1 CTA" in e for e in errs)

    # CTA on slot where eligibility is False rejected
    single_cta = [
        "Discuss a Web3 audit with SanadSquad: frank@sanadsquad.com."
    ]
    errs_unreserved = validate_contact_cta(single_cta, contact_config=approved_cfg, allow_cta=False)
    assert any("CTA eligibility is not reserved" in e for e in errs_unreserved)


# ==============================================================================
# 8. Unsupported Superiority Claims
# ==============================================================================

def test_unsupported_superiority_claims_rejected():
    """Superlative superiority claims are caught and rejected."""
    bad_claims = [
        "SanadSquad is the industry-leading Web3 security firm.",
        "Our team offers unmatched expertise across EVM and SVM architectures.",
        "Work with the best security firm to protect your protocol.",
        "We are the market leader in autonomous AI agent red teaming.",
        "SanadSquad provides number one in security verification.",
    ]
    for text in bad_claims:
        errs = validate_marketing_claims([text])
        assert any("unsupported superiority claim" in e.lower() for e in errs), f"Failed to flag: {text}"


# ==============================================================================
# 9. Unverified Company Experience Claims
# ==============================================================================

def test_unverified_company_experience_rejected():
    """Claiming SanadSquad audited external incident targets (Bybit, Safe, Solana) is rejected."""
    bad_experience_claims = [
        "We audited Bybit and identified their frontend signing vulnerability.",
        "Our audit of Safe prevented further calldata tampering.",
        "Our client Bybit suffered a major supply chain attack.",
        "We secured Solana by deploying verified builds.",
        "We audited the affected contract in the recent multi-million dollar exploit.",
    ]
    for text in bad_experience_claims:
        errs = validate_marketing_claims([text])
        assert any("unverified company experience" in e.lower() for e in errs), f"Failed to flag: {text}"


# ==============================================================================
# 10. Separation of Facts, Opinions, and Service Positioning
# ==============================================================================

def test_epistemic_separation_valid_marketing_piece():
    """A well-crafted marketing piece cleanly separates fact, interpretation, positioning, and CTA."""
    approved_cfg = CompanyContactConfig(
        company_name="SanadSquad",
        business_inquiries_email="frank@sanadsquad.com",
        contact_form_url="https://sanadsquad.com/contact/",
        approved=True,
    )

    # Fact: Solana verified builds match source hash to on-chain bytecode.
    # Interpretation: Audits alone miss unverified deployment changes or upgrade authority misuse.
    # Positioning: SanadSquad provides deployment verification and invariant monitoring.
    # CTA: Optional contact invitation.
    piece_text = (
        "Solana verified builds verify that deployed bytecode matches audited source. "
        "Audits verify logic at rest; unverified scripts can alter runtime state. "
        "SanadSquad verifies program builds and upgrade authority. "
        "Web3 audit: frank@sanadsquad.com"
    )
    # Character limit check: <= 280 chars
    assert len(piece_text) <= 280, f"Length {len(piece_text)} exceeds 280"

    # Deterministic validation passes cleanly
    claim_errs = validate_marketing_claims([piece_text])
    assert claim_errs == []

    cta_errs = validate_contact_cta([piece_text], contact_config=approved_cfg, allow_cta=True)
    assert cta_errs == []

    writing_rep = validate_writing_quality([piece_text])
    assert writing_rep.passed is True
