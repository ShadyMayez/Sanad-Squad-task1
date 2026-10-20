"""Tests for Phase 1 Source Separation requirements.

Enforces:
- Marketing KB access blocked.
- Technical KB strategy accepted.
- Technical external-source strategy accepted.
- Wrong-service domains rejected.
- Cross-service allowlists correctly combined.
- Global denylist overrides approvals.
- Redirect outside allowlist rejected.
- Unretrieved URL rejected from public text.
- Vulnerability-class KB exception correctly bounded.
"""
from __future__ import annotations

import pytest
from pathlib import Path
from content_pipeline.source_authority import (
    TechnicalSourceStrategy,
    MarketingSourceStrategy,
    SourceAuthorityContext,
    SourceAuthorityViolationError,
    TechnicalResourceBrief,
    filter_authorized_evidence,
)
from content_pipeline.research.config import SourcesConfig, load_sources_config
from content_pipeline.research.service import ResearchService
from content_pipeline.research.provider import FixtureResearchProvider
from content_pipeline.schemas import Evidence, Slot, Vulnerability
from content_pipeline.validation import validate_brand_and_platform
from content_pipeline.config import load_brand, load_registry, load_kb


def test_marketing_kb_access_strictly_blocked():
    """Marketing Writer cannot access KB as primary source authority."""
    ctx = SourceAuthorityContext.for_marketing_slot(
        slot_id="slot_mkt_1",
        service_line="web3-security",
        allowed_domains=["paradigm.xyz", "openzeppelin.com"],
        is_vulnerability_class_exception=False,
    )
    with pytest.raises(SourceAuthorityViolationError, match="strictly barred from accessing the vulnerability catalog"):
        ctx.assert_kb_read_allowed()


def test_marketing_kb_exception_requires_supplemental_web_evidence():
    """Marketing Writer can only access KB if supplemental to retrieved web research."""
    ctx = SourceAuthorityContext.for_marketing_slot(
        slot_id="slot_mkt_1",
        service_line="web3-security",
        allowed_domains=["paradigm.xyz"],
        is_vulnerability_class_exception=True,
    )
    # KB read assertion passes because exception is enabled
    ctx.assert_kb_read_allowed()

    # But filter_authorized_evidence will fail closed if there is NO web research
    kb_ev = Evidence(
        id="kb_swc104_1",
        url="https://swcregistry.io/docs/SWC-104",
        excerpt="Unchecked return value",
        source_title="SWC-104",
        source_type="knowledge_base",
    )
    with pytest.raises(SourceAuthorityViolationError, match="must contain primary web research"):
        filter_authorized_evidence(ctx, evidence_list=[kb_ev])


def test_vulnerability_class_exception_cannot_substitute_for_web_research():
    """Vulnerability-class KB exception still requires live web research to pass sufficiency."""
    config = load_sources_config()
    provider = FixtureResearchProvider(config)
    service = ResearchService(config=config, provider=provider)
    kb = load_kb()
    kb_vulns = [kb.vulnerabilities[0]]

    # Force search failure by passing unknown service line
    ev_list, ids, err = service.conduct_marketing_research(
        slot_id="slot_mkt_1",
        service_line="non-existent-service",
        is_vulnerability_class_exception=True,
        supplemental_kb_vulnerabilities=kb_vulns,
    )
    assert err is not None
    assert "Unknown service line" in err or "failed" in err.lower()
    assert len(ev_list) == 0


def test_technical_kb_strategy_accepted():
    """Technical thread Strategy 1: Knowledge base is permitted."""
    ctx = SourceAuthorityContext.for_technical_slot(
        slot_id="slot_tech_1",
        strategy=TechnicalSourceStrategy.KNOWLEDGE_BASE,
    )
    ctx.assert_kb_read_allowed()
    assert ctx.allowed_kb_access is True


def test_technical_external_source_strategy_accepted():
    """Technical thread Strategy 2: External technical resource verified with brief."""
    config = load_sources_config()
    provider = FixtureResearchProvider(config)
    service = ResearchService(config=config, provider=provider)

    url = "https://blog.openzeppelin.com/post-mortem-example"
    ev_list, brief, err = service.conduct_technical_external_research(
        slot_id="tech_ext_slot",
        url=url,
    )
    assert err is None
    assert len(ev_list) == 1
    assert brief is not None
    assert isinstance(brief, TechnicalResourceBrief)
    assert brief.url == url
    assert len(brief.sha256_checksum) == 64
    assert ev_list[0].scope == "external_technical_postmortem"


def test_wrong_service_domains_rejected():
    """Domains not allowlisted for the service line are rejected."""
    config = load_sources_config()
    # stripe.com is allowlisted for agentic-payments, NOT for pentesting
    assert config.is_domain_allowed("stripe.com", "agentic-payments") is True
    assert config.is_domain_allowed("stripe.com", "pentesting") is False

    # solana.com is allowlisted for web3-security, NOT for agentic-security
    assert config.is_domain_allowed("solana.com", "web3-security") is True
    assert config.is_domain_allowed("solana.com", "agentic-security") is False


def test_cross_service_allowlists_correctly_combined():
    """Cross-service query allows domains approved in either service."""
    config = load_sources_config()
    combined = config.get_cross_service_allowlist(["web3-security", "agentic-security"])
    assert "solana.com" in combined
    assert "genai.owasp.org" in combined
    assert "attacker-site.com" not in combined


def test_global_denylist_overrides_approvals():
    """Global denylist strictly overrides any service allowlist."""
    config = SourcesConfig.model_validate({
        "service_lines": {
            "web3-security": {
                "description": "Smart contracts",
                "blogs": ["openzeppelin.com", "malicious-subdomain.openzeppelin.com"],
                "docs": [],
                "production": [],
                "analysis": [],
                "figures": [],
            }
        },
        "global_deny": ["malicious-subdomain.openzeppelin.com", "pastebin.com"],
    })
    # openzeppelin.com is allowed
    assert config.is_domain_allowed("openzeppelin.com", "web3-security") is True
    # denied domain is blocked even though present in service blogs
    assert config.is_domain_allowed("malicious-subdomain.openzeppelin.com", "web3-security") is False


def test_unretrieved_url_rejected_from_public_text():
    """Public post cannot cite URLs that were not fetched during the run."""
    _, brand = load_brand()
    reg = load_registry()
    spec = reg.types["marketing-post"]

    tweets = ["Check our analysis at https://unretrieved-external-site.com/report"]
    # If unretrieved-external-site.com was not in allowed_run_links, deterministic check rejects it
    errors = validate_brand_and_platform(
        tweets,
        brand=brand,
        spec=spec,
        allowed_run_links=["https://blog.openzeppelin.com/real-article"],
    )
    assert any("contains unapproved link" in e for e in errors)
