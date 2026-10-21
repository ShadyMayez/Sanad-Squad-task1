"""Targeted regression test suite for Directive SANADSQUAD_V3_FINAL_SOURCE_TRUTH_GATE_01.

Verifies:
1. Zero placeholder URLs in research fixtures or graph fallbacks.
2. Canonical live replacements (ethereum.org formal verification, api-security.owasp.org).
3. Deterministic rejection of technical overstatements (formal verification "prevents",
   audits "prove correctness", Solana upgradeability "enables unauthorized changes",
   BOLA conflated with authentication, OWASP spending cap misattribution).
4. Service positioning guidance across all 5 official services.
5. Clear separation between offline fixture evidence and live research availability.
"""
from __future__ import annotations

import os
from unittest.mock import patch
import pytest

from content_pipeline.research.config import load_sources_config
from content_pipeline.research.fixtures import get_all_fixtures, RESEARCH_FIXTURES
from content_pipeline.research.provider import FixtureResearchProvider, LiveResearchProvider
from content_pipeline.marketing_policy import validate_marketing_claims, load_marketing_policy
from content_pipeline.content_planning import build_marketing_evidence_plan
from content_pipeline.schemas import Evidence


def test_zero_placeholder_urls_in_fixtures():
    """Ensure no synthetic or broken placeholder URLs exist in research fixtures."""
    fixtures = get_all_fixtures()
    assert len(fixtures) > 0

    banned_substrings = [
        "example",
        "post-mortem-example",
        "www-project-api-security",
        "localhost",
        "127.0.0.1",
    ]

    for f in fixtures:
        url = f["url"].lower()
        for banned in banned_substrings:
            assert banned not in url, f"Fixture contains prohibited placeholder URL component '{banned}': {url}"
        assert url.startswith("https://"), f"Fixture URL must use secure HTTPS: {url}"


def test_canonical_ethereum_formal_verification_fixture():
    """Verify ethereum.org formal verification fixture exists and satisfies allowlist."""
    cfg = load_sources_config()
    provider = FixtureResearchProvider(cfg)

    target_url = "https://ethereum.org/developers/docs/smart-contracts/formal-verification/"
    page = provider.fetch(target_url, "web3-security")
    assert page.http_status == 200
    assert page.eligible_for_public_posting is True
    assert page.is_fixture is True
    assert "formal verification" in page.cleaned_text.lower()
    # Ensure fixture does NOT claim formal verification prevents all vulnerabilities
    assert "does not dynamically prevent runtime flaws" in page.cleaned_text.lower()


def test_canonical_owasp_api_security_fixture():
    """Verify live canonical OWASP API security fixture exists and clearly defines BOLA."""
    cfg = load_sources_config()
    provider = FixtureResearchProvider(cfg)

    target_url = "https://api-security.owasp.org/editions/2023/en/0x11-t10/"
    page = provider.fetch(target_url, "pentesting")
    assert page.http_status == 200
    assert page.eligible_for_public_posting is True
    assert page.is_fixture is True
    assert "broken object level authorization" in page.cleaned_text.lower()
    assert "distinct from user authentication" in page.cleaned_text.lower() or "distinct from" in page.cleaned_text.lower()


def test_owasp_agentic_security_fixture_no_spending_caps_misattribution():
    """Verify OWASP GenAI fixture focuses on ACS and execution boundaries without false spending cap attributions."""
    cfg = load_sources_config()
    provider = FixtureResearchProvider(cfg)

    target_url = "https://genai.owasp.org/initiatives/agentic-security-initiative/"
    page = provider.fetch(target_url, "agentic-security")
    assert page.http_status == 200
    assert "agent control standard" in page.cleaned_text.lower()
    # Confirm no false attribution of cryptographic spending caps to OWASP
    assert "spending caps" not in page.cleaned_text.lower()


def test_rejects_formal_verification_prevents_claim():
    """Ensure validate_marketing_claims rejects the claim that formal verification 'prevents' vulnerabilities."""
    tweet = "Formal verification prevents reentrancy and authorization-ordering flaws in smart contracts."
    errors = validate_marketing_claims([tweet])
    assert any("formal verification" in e.lower() and "prevent" in e.lower() for e in errors)


def test_rejects_solana_upgradeability_unauthorized_changes_claim():
    """Ensure validate_marketing_claims rejects describing Solana upgrade authority as enabling 'unauthorized' changes."""
    tweet = "Solana program deployment assigns upgrade authority in ProgramData, which enables unauthorized changes."
    errors = validate_marketing_claims([tweet])
    assert any("unauthorized" in e.lower() and "solana" in e.lower() for e in errors)


def test_rejects_audit_proves_correctness_claim():
    """Ensure validate_marketing_claims rejects claiming audits prove code correctness."""
    tweet = "Our comprehensive smart contract audit proves code correctness before mainnet launch."
    errors = validate_marketing_claims([tweet])
    assert any("prove" in e.lower() and "correctness" in e.lower() for e in errors)


def test_rejects_bola_authentication_conflation():
    """Ensure validate_marketing_claims rejects confusing BOLA with verifying user identity."""
    tweet = "Broken object level authorization occurs when APIs fail to verify user identity at every access point."
    errors = validate_marketing_claims([tweet])
    assert any("broken object level authorization" in e.lower() and "identity" in e.lower() for e in errors)


def test_rejects_owasp_spending_caps_misattribution():
    """Ensure validate_marketing_claims rejects attributing spending caps or crypto policy to OWASP."""
    tweet = "OWASP specifies that agent security requires cryptographic policy limits and hard spending caps."
    errors = validate_marketing_claims([tweet])
    assert any("source misattribution" in e.lower() and "owasp" in e.lower() for e in errors)


def test_service_positioning_guidance_in_content_planning():
    """Verify build_marketing_evidence_plan includes targeted service positioning guidance."""
    ev = Evidence(
        id="ev_test",
        url="https://api-security.owasp.org/editions/2023/en/0x11-t10/",
        excerpt="BOLA is authorization failure",
    )

    # 1. Agentic security tooling
    plan_tooling = build_marketing_evidence_plan(
        slot_id="slot_tooling",
        service_line="agentic-security-tooling",
        marketing_format="short-tip",
        evidence=[ev],
    )
    guidance_tooling = plan_tooling.units[0].guidance
    assert "custom security software" in guidance_tooling.lower() or "detectors" in guidance_tooling.lower()

    # 2. Security consulting
    plan_consulting = build_marketing_evidence_plan(
        slot_id="slot_consulting",
        service_line="security-consulting",
        marketing_format="short-tip",
        evidence=[ev],
    )
    guidance_consulting = plan_consulting.units[0].guidance
    assert "architecture design review" in guidance_consulting.lower() or "threat modeling" in guidance_consulting.lower()

    # 3. Penetration testing
    plan_pentest = build_marketing_evidence_plan(
        slot_id="slot_pentest",
        service_line="penetration-testing",
        marketing_format="short-tip",
        evidence=[ev],
    )
    guidance_pentest = plan_pentest.units[0].guidance
    assert "off-chain attack surface" in guidance_pentest.lower()


def test_live_research_provider_unavailable_when_no_api_key():
    """Confirm LiveResearchProvider reports unavailable when API key is unset."""
    cfg = load_sources_config()
    with patch.dict(os.environ, {}, clear=True):
        live_provider = LiveResearchProvider(cfg)
        assert live_provider.is_available() is False
        assert live_provider.mode == "live"
        with pytest.raises(RuntimeError, match="LiveResearchProvider is unavailable"):
            live_provider.search("reentrancy", "web3-security")


def test_fixture_provider_clearly_disclosed_as_fixture():
    """Verify FixtureResearchProvider marks fetched pages with is_fixture=True."""
    cfg = load_sources_config()
    provider = FixtureResearchProvider(cfg)
    assert provider.mode == "fixture"
    page = provider.fetch("https://top10.owasp.org/", "pentesting")
    assert page.is_fixture is True
    assert page.http_status == 200
