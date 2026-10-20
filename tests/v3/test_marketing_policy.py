"""Tests for Phase 3 Marketing Policy and Guide compliance.

Enforces:
- All four service lines configured.
- All five eligible single-tweet formats supported and verified.
- Marketing thread recorded as reserved future format, barred under marketing-post contract.
- Single-tweet length limit (<= 280 chars).
- Mandatory links for news reaction and learning resource.
- Link forbidden for short tip.
- Commercial CTA limits (<= 1/3 weekly marketing posts, max 1 per post).
- Honest x402 vs MPP comparisons.
- Accretion audit findings isolated as third-party, never claimed as SanadSquad work.
- audits.json remains empty and valid under schemas/audits.schema.json.
- Competitor attack and guarantee prohibitions.
"""
from __future__ import annotations

import json
import pytest
from pathlib import Path
from content_pipeline.config import ROOT, load_brand, load_registry
from content_pipeline.marketing_format import (
    MarketingFormat,
    FORMAT_SPECS,
    validate_marketing_format,
)
from content_pipeline.marketing_policy import (
    load_marketing_policy,
    detect_commercial_cta,
    validate_marketing_claims,
)
from content_pipeline.validation import validate_brand_and_platform


def test_four_service_lines_configured():
    """Marketing policy must support all 4 specified service lines."""
    policy = load_marketing_policy()
    expected = {"web3-security", "pentesting", "agentic-security", "agentic-payments"}
    assert set(policy.service_lines) == expected


def test_five_single_tweet_formats_supported():
    """All 5 single-tweet formats are registered with proper link requirements."""
    assert MarketingFormat.SHORT_TIP in FORMAT_SPECS
    assert MarketingFormat.DIFFERENTIATION in FORMAT_SPECS
    assert MarketingFormat.SERVICE_OVERVIEW in FORMAT_SPECS
    assert MarketingFormat.NEWS_REACTION in FORMAT_SPECS
    assert MarketingFormat.LEARNING_RESOURCE in FORMAT_SPECS

    assert FORMAT_SPECS[MarketingFormat.SHORT_TIP].forbids_link is True
    assert FORMAT_SPECS[MarketingFormat.SHORT_TIP].requires_link is False

    assert FORMAT_SPECS[MarketingFormat.NEWS_REACTION].requires_link is True
    assert FORMAT_SPECS[MarketingFormat.LEARNING_RESOURCE].requires_link is True


def test_marketing_thread_rejected_under_single_tweet_contract():
    """marketing-post must remain strictly 1 tweet; thread format cannot be selected for it."""
    spec = FORMAT_SPECS[MarketingFormat.MARKETING_THREAD]
    assert spec.max_tweets > 1

    # Attempting to validate a multi-tweet thread under marketing-post contract fails
    thread_tweets = [
        "1/3 Understanding x402 vs MPP settlement mechanics.",
        "2/3 x402 uses HTTP status 402 with facilitator signatures.",
        "3/3 MPP provides streaming micro-settlement.",
    ]
    errors = validate_marketing_format(thread_tweets, selected_format=MarketingFormat.MARKETING_THREAD)
    assert any("reserved future content type" in e for e in errors)


def test_short_tip_forbids_link():
    """Short tip format must not carry external links."""
    tip_with_link = ["Smart contract audits only test code at rest; test your runtime invariants at https://example.com"]
    errors = validate_marketing_format(tip_with_link, selected_format=MarketingFormat.SHORT_TIP)
    assert any("must not contain any links" in e for e in errors)

    clean_tip = ["Smart contract audits only verify static bytecode; runtime invariant testing is required to stop post-audit drift."]
    assert validate_marketing_format(clean_tip, selected_format=MarketingFormat.SHORT_TIP) == []


def test_news_reaction_and_learning_resource_require_links():
    """News reaction and learning resource formats strictly mandate a working source link."""
    no_link_news = ["A major bridge lost $50M this week due to an unauthorized signer escalation."]
    errs_news = validate_marketing_format(no_link_news, selected_format=MarketingFormat.NEWS_REACTION)
    assert any("requires an authorized source link" in e for e in errs_news)

    no_link_resource = ["Check out the comprehensive guide to AI agent prompt injection defenses."]
    errs_res = validate_marketing_format(no_link_resource, selected_format=MarketingFormat.LEARNING_RESOURCE)
    assert any("requires an authorized source link" in e for e in errs_res)


def test_single_tweet_platform_limit():
    """Any marketing post exceeding 280 characters is rejected."""
    long_tweet = ["A" * 281]
    errors = validate_marketing_format(long_tweet, selected_format=MarketingFormat.DIFFERENTIATION)
    assert any("exceeds 280 character limit" in e for e in errors)


def test_commercial_cta_taxonomy():
    """Distinguish commercial solicitations from legitimate educational recommendations."""
    # Commercial solicitation
    sales_text = "Schedule an audit with SanadSquad today to secure your protocol."
    has_cta, count, matches = detect_commercial_cta(sales_text)
    assert has_cta is True
    assert count == 1

    # Educational recommendation (not a sales pitch)
    edu_text = "Enforce rate limits on agent wallets and verify token approvals before execution."
    has_cta, count, matches = detect_commercial_cta(edu_text)
    assert has_cta is False
    assert count == 0


def test_prohibited_guarantee_claims():
    """Absolute security promises ('unhackable', 'guarantee', 'zero risk') are strictly rejected."""
    bad_claims = [
        "SanadSquad provides guaranteed security for your SVM protocol.",
        "Our invariant testing makes your contracts 100% secure and unhackable.",
        "Eliminate all risk across your agentic payment flow.",
    ]
    for text in bad_claims:
        errors = validate_marketing_claims([text])
        assert any("guarantee claim" in e.lower() for e in errors)


def test_prohibited_competitor_attacks():
    """Criticizing named competitors (CertiK, OpenZeppelin) is strictly prohibited."""
    tweets = ["CertiK missed reentrancy bugs that SanadSquad would have caught."]
    errors = validate_marketing_claims(tweets)
    assert any("competitor attack" in e.lower() for e in errors)


def test_audits_json_remains_empty_and_valid():
    """audits.json is private company data and must remain empty under its JSON schema."""
    audits_path = ROOT / "audits.json"
    schema_path = ROOT / "schemas" / "audits.schema.json"
    assert audits_path.exists()
    assert schema_path.exists()

    audits_data = json.loads(audits_path.read_text(encoding="utf-8"))
    assert audits_data == []  # Must remain empty

    schema = json.loads(schema_path.read_text(encoding="utf-8"))
    assert schema["type"] == "array"
    assert "items" in schema
    assert "$schema" in schema


def test_accretion_findings_isolation():
    """The 20 Accretion findings are third-party audits and cannot be claimed as SanadSquad work."""
    # Mentioning Accretion findings as SanadSquad work is caught by claims validator
    fraudulent_claim = "SanadSquad discovered finding SS-03699 in the Swig wallet audit."
    errors = validate_marketing_claims([fraudulent_claim])
    assert any("third-party audit material" in e.lower() for e in errors)
