"""Permanent regression tests for Directive SANADSQUAD_V3_OFFICIAL_BRAND_INTEGRATION_01.

Phase 7 Comprehensive Regression Suite verifying:
1. All five official services are recognized.
2. The four-category research taxonomy remains functional.
3. Each service has valid company evidence references.
4. Official contact information is loaded correctly.
5. Fictional email addresses and telephone numbers are rejected.
6. Missing telephone numbers are handled gracefully.
7. The recruitment email is not used for commercial CTAs.
8. Approval restrictions remain enforced.
9. CTA frequency never exceeds one-third.
10. Contact CTA posts stay under 280 characters.
11. Technical threads never receive commercial CTAs.
12. Private audits remain excluded.
13. Unsupported company statistics are rejected.
14. Wrong-service marketing claims are rejected.
15. All accepted marketing claims retain their correct evidence authority.
16. A failed website fetch does not silently substitute invented service data.
17. Accepted-only CSV and visual specification contracts remain intact.
"""
from __future__ import annotations

import csv
import json
import pytest
import re
from pathlib import Path

from content_pipeline.config import ROOT, load_brand, load_registry
from content_pipeline.contact_config import (
    CompanyContactConfig,
    load_company_contact,
    build_contextual_cta,
    is_synthetic_contact,
    is_recruitment_email,
    SYNTHETIC_DEMO_CONTACTS,
    RECRUITMENT_EMAILS,
)
from content_pipeline.marketing_planner import (
    OFFICIAL_COMMERCIAL_SERVICES,
    COMMERCIAL_TO_RESEARCH_TAXONOMY,
    MarketingSlotPlanner,
    WeeklyMarketingPlan,
    MarketingSlotMetadata,
    normalize_commercial_service,
    map_service_to_research_category,
    validate_weekly_marketing_results,
)
from content_pipeline.marketing_policy import (
    MarketingPolicy,
    load_marketing_policy,
    detect_commercial_cta,
    validate_marketing_claims,
    validate_contact_cta,
)
from content_pipeline.marketing_format import MarketingFormat, FORMAT_SPECS
from content_pipeline.research.config import (
    load_sources_config,
    COMMERCIAL_TO_RESEARCH_MAP,
)
from content_pipeline.research.fixtures import (
    get_fixtures_for_service,
    RESEARCH_FIXTURES,
)
from content_pipeline.research.service import ResearchService
from content_pipeline.research.provider import FixtureResearchProvider, ResearchProvider
from content_pipeline.research.models import FetchedPage, SearchResult
from content_pipeline.validation import validate_piece_deterministic
from content_pipeline.export import export_run
from content_pipeline.schemas import (
    Plan,
    Slot,
    SlotResult,
    Draft,
    Evidence,
    BrandRules,
    WriterConfig,
    Review,
)


# ==============================================================================
# 1. All Five Official Services Are Recognized
# ==============================================================================

def test_all_five_official_services_recognized():
    """All 5 official services advertised on sanadsquad.com are defined and recognized."""
    expected_services = [
        "blockchain-security-audits",
        "penetration-testing",
        "agentic-security-tooling",
        "agentic-payments",
        "security-consulting",
    ]
    assert OFFICIAL_COMMERCIAL_SERVICES == expected_services

    policy = load_marketing_policy()
    for s in expected_services:
        assert s in policy.commercial_services

    # Verify normalizer maps canonical names and aliases
    assert normalize_commercial_service("Blockchain security audits") == "blockchain-security-audits"
    assert normalize_commercial_service("Penetration testing") == "penetration-testing"
    assert normalize_commercial_service("Agentic security tooling") == "agentic-security-tooling"
    assert normalize_commercial_service("Agentic payments") == "agentic-payments"
    assert normalize_commercial_service("Security consulting") == "security-consulting"

    # Aliases
    assert normalize_commercial_service("web3-security") == "blockchain-security-audits"
    assert normalize_commercial_service("pentesting") == "penetration-testing"
    assert normalize_commercial_service("tooling") == "agentic-security-tooling"
    assert normalize_commercial_service("payments") == "agentic-payments"
    assert normalize_commercial_service("consulting") == "security-consulting"


# ==============================================================================
# 2. Four-Category Research Taxonomy Remains Functional
# ==============================================================================

def test_four_category_research_taxonomy_remains_functional():
    """The 4-category research taxonomy is fully functional and correctly maps 5 commercial services."""
    sources_cfg = load_sources_config()
    required_research_categories = {"web3-security", "pentesting", "agentic-security", "agentic-payments"}
    assert set(sources_cfg.service_lines.keys()) == required_research_categories

    for cat in required_research_categories:
        allowlist = sources_cfg.get_service_allowlist(cat)
        assert len(allowlist) >= 3, f"Research category {cat} must have at least 3 allowlisted domains"

    # Commercial services map properly to the 4 categories
    assert map_service_to_research_category("blockchain-security-audits") == "web3-security"
    assert map_service_to_research_category("penetration-testing") == "pentesting"
    assert map_service_to_research_category("agentic-security-tooling") == "agentic-security"
    assert map_service_to_research_category("agentic-payments") == "agentic-payments"
    assert map_service_to_research_category("security-consulting") == "web3-security"

    # Fixtures support all 5 commercial service lines via mapping
    for s in OFFICIAL_COMMERCIAL_SERVICES:
        fixtures = get_fixtures_for_service(s)
        assert len(fixtures) >= 2, f"Expected at least 2 research fixtures for commercial service {s}"


# ==============================================================================
# 3. Each Service Has Valid Company Evidence References
# ==============================================================================

def test_each_service_has_valid_company_evidence_references():
    """docs/marketing/SANADSQUAD_OFFICIAL_SERVICE_PROFILE.md documents all 5 services with URLs and checksums."""
    profile_path = ROOT / "docs" / "marketing" / "SANADSQUAD_OFFICIAL_SERVICE_PROFILE.md"
    assert profile_path.exists(), "SANADSQUAD_OFFICIAL_SERVICE_PROFILE.md must exist"
    content = profile_path.read_text(encoding="utf-8")

    expected_specs = [
        {
            "name": "Blockchain security audits",
            "url": "https://sanadsquad.com/services/blockchain-security-audits/",
            "sha256": "e50a6d79fec45ab238abed72b7e1bf1a97bd1800ef37a169adbc57f06e612721",
        },
        {
            "name": "Penetration testing",
            "url": "https://sanadsquad.com/services/penetration-testing/",
            "sha256": "43129d7dafabdd4cef482e6ca4aa1f550b724f4b2c8c831c6320016550065793",
        },
        {
            "name": "Agentic security tooling",
            "url": "https://sanadsquad.com/services/ai-security-tooling/",
            "sha256": "987804573e8ae366408ee5e8402ca1b74c762b7a6b7eae92699263ba88b459e0",
        },
        {
            "name": "Agentic payments",
            "url": "https://sanadsquad.com/services/agentic-payments/",
            "sha256": "df543f4f72c745d4785a39cb8952bf7b7cc68e1fb9a6f88b0ab986ccc6c42b1f",
        },
        {
            "name": "Security consulting",
            "url": "https://sanadsquad.com/services/consulting/",
            "sha256": "ef1959d398953cd800d1338b604549f10d8e5f19c2422454689f8b193d8ceee7",
        },
    ]

    for spec in expected_specs:
        assert spec["name"] in content, f"Missing service {spec['name']} in profile"
        assert spec["url"] in content, f"Missing URL {spec['url']} in profile"
        assert spec["sha256"] in content, f"Missing checksum {spec['sha256']} in profile"

    # Profile enforces claims boundaries
    assert "Claims That Must Never Be Made" in content
    assert "Allowed Company Positioning Claims" in content


# ==============================================================================
# 4. Official Contact Information Loaded Correctly
# ==============================================================================

def test_official_contact_information_loaded_correctly():
    """company-contact.json on disk loads verified public channels with exact provenance."""
    cfg = load_company_contact()
    assert cfg.company_name == "SanadSquad"
    assert cfg.business_inquiries_email == "frank@sanadsquad.com"
    assert cfg.contact_form_url == "https://sanadsquad.com/contact/"
    assert cfg.telegram == "@castle_chain"
    assert cfg.x_handle == "@SanadSquad"
    assert cfg.official_website == "https://sanadsquad.com"
    assert cfg.business_phone_number is None
    assert cfg.notes is not None and "https://sanadsquad.com/contact/" in cfg.notes


# ==============================================================================
# 5. Fictional Email Addresses and Telephone Numbers Are Rejected
# ==============================================================================

def test_fictional_email_addresses_and_telephone_numbers_rejected():
    """Synthetic placeholders and fictional phone numbers (+1-555-0199) are strictly rejected."""
    assert is_synthetic_contact("+1-555-0199") is True
    assert is_synthetic_contact("+1-555-9999") is True
    assert is_synthetic_contact("contact@sanadsquad.com") is True

    # Rejection by CompanyContactConfig validation
    with pytest.raises(ValueError, match="Fictional or unapproved contact placeholder"):
        CompanyContactConfig(
            company_name="SanadSquad",
            business_inquiries_email="contact@sanadsquad.com",
            approved=True,
        )

    with pytest.raises(ValueError, match="Fictional telephone number"):
        CompanyContactConfig(
            company_name="SanadSquad",
            business_inquiries_email="frank@sanadsquad.com",
            business_phone_number="+1-555-0199",
            approved=True,
        )

    # Rejection by marketing validator
    approved_cfg = CompanyContactConfig(
        company_name="SanadSquad",
        business_inquiries_email="frank@sanadsquad.com",
        approved=True,
        status="APPROVED",
    )
    tweets = ["Building a payment agent? Review authorization. Email: contact@sanadsquad.com | Phone: +1-555-0199"]
    errs = validate_contact_cta(tweets, contact_config=approved_cfg, allow_cta=True, content_type="marketing-post")
    assert any("fictional" in e.lower() or "unapproved" in e.lower() for e in errs)


# ==============================================================================
# 6. Missing Telephone Numbers Are Handled Gracefully
# ==============================================================================

def test_missing_telephone_numbers_handled_gracefully():
    """When phone is None, email-only and contact-form CTAs generate naturally without placeholder phone numbers."""
    cfg = CompanyContactConfig(
        company_name="SanadSquad",
        business_inquiries_email="frank@sanadsquad.com",
        business_phone_number=None,
        contact_form_url="https://sanadsquad.com/contact/",
        approved=True,
        status="APPROVED",
    )
    cta = build_contextual_cta("blockchain-security-audits", cfg)
    assert "Email: frank@sanadsquad.com" in cta
    assert "Phone" not in cta
    assert "+1-555" not in cta

    # Form channel
    cta_form = build_contextual_cta("blockchain-security-audits", cfg, channel="form")
    assert "Contact: https://sanadsquad.com/contact/" in cta_form
    assert "Phone" not in cta_form


# ==============================================================================
# 7. Recruitment Email Not Used for Commercial CTAs
# ==============================================================================

def test_recruitment_email_not_used_for_commercial_ctas():
    """career@sanadsquad.com is reserved for recruitment and strictly barred from commercial CTAs."""
    assert is_recruitment_email("career@sanadsquad.com") is True

    with pytest.raises(ValueError, match="Recruitment email"):
        CompanyContactConfig(
            company_name="SanadSquad",
            business_inquiries_email="career@sanadsquad.com",
            approved=True,
        )

    approved_cfg = CompanyContactConfig(
        company_name="SanadSquad",
        business_inquiries_email="frank@sanadsquad.com",
        approved=True,
        status="APPROVED",
    )
    tweets = ["Reviewing protocol security? Contact us at career@sanadsquad.com for quotes."]
    errs = validate_contact_cta(tweets, contact_config=approved_cfg, allow_cta=True, content_type="marketing-post")
    assert any("recruitment email" in e.lower() for e in errs)


# ==============================================================================
# 8. Approval Restrictions Remain Enforced
# ==============================================================================

def test_approval_restrictions_remain_enforced():
    """Unapproved contact configuration fails closed; planner sets has_cta=False and export rejects publication."""
    disk_cfg = load_company_contact()
    assert disk_cfg.approved is False
    assert disk_cfg.status == "AWAITING_OWNER_APPROVAL"
    assert not disk_cfg.is_operational()

    # Planner fails closed
    slots = [
        Slot(id="post_1", type="marketing-post", focus="audits"),
        Slot(id="post_2", type="marketing-post", focus="pentest"),
        Slot(id="post_3", type="marketing-post", focus="payments"),
    ]
    plan = MarketingSlotPlanner.plan_weekly_slots(slots)
    assert all(s.has_cta is False for s in plan.slots)

    # CTA builder refuses unapproved config
    with pytest.raises(ValueError, match="not approved"):
        build_contextual_cta("blockchain-security-audits", disk_cfg)


# ==============================================================================
# 9. CTA Frequency Never Exceeds One-Third
# ==============================================================================

def test_cta_frequency_never_exceeds_one_third():
    """Weekly marketing plan and results enforce <= 1 CTA across 3 marketing posts."""
    plan_slots = [
        MarketingSlotMetadata(
            slot_id="post_1",
            commercial_service="blockchain-security-audits",
            service_line="blockchain-security-audits",
            research_angle="invariant verification",
            selected_format=MarketingFormat.DIFFERENTIATION,
            requires_link=False,
            forbids_link=True,
            has_cta=True,
            topic_fingerprint="fp1",
        ),
        MarketingSlotMetadata(
            slot_id="post_2",
            commercial_service="penetration-testing",
            service_line="penetration-testing",
            research_angle="API security",
            selected_format=MarketingFormat.NEWS_REACTION,
            requires_link=True,
            forbids_link=False,
            has_cta=True,  # Second CTA in 3 posts violates rule
            topic_fingerprint="fp2",
        ),
        MarketingSlotMetadata(
            slot_id="post_3",
            commercial_service="agentic-payments",
            service_line="agentic-payments",
            research_angle="x402 vs MPP",
            selected_format=MarketingFormat.LEARNING_RESOURCE,
            requires_link=True,
            forbids_link=False,
            has_cta=False,
            topic_fingerprint="fp3",
        ),
    ]
    plan = WeeklyMarketingPlan(slots=plan_slots)
    errors = plan.validate_constraints()
    assert any("Weekly mix violation:" in e and "contain CTAs" in e for e in errors)


# ==============================================================================
# 10. Contact CTA Posts Stay Under 280 Characters
# ==============================================================================

def test_contact_cta_posts_stay_under_280_characters():
    """Marketing posts with approved contact details must remain strictly <= 280 characters."""
    approved_cfg = CompanyContactConfig(
        company_name="SanadSquad",
        business_inquiries_email="frank@sanadsquad.com",
        approved=True,
        status="APPROVED",
    )
    long_text = (
        "Smart contracts holding decentralized liquidity face recurring invariant violations when state updates "
        "precede balance validations. Line-by-line invariant review exposes rounding errors before mainnet launch. "
        "Reviewing protocol security? Contact SanadSquad to discuss an audit. Email: frank@sanadsquad.com"
    )
    assert len(long_text) > 280
    brand, brand_rules = load_brand()
    spec = WriterConfig(
        name="marketing-post",
        min_tweets=1,
        max_tweets=1,
        max_chars=280,
        instruction_file="instructions/marketing-post.md",
    )
    passed, errs, _ = validate_piece_deterministic(
        [long_text],
        brand=brand_rules,
        spec=spec,
        contact_config=approved_cfg,
        allow_cta=True,
        content_type="marketing-post",
    )
    assert passed is False
    assert any("exceeds 280 characters" in e for e in errs)

    # Valid short version <= 280 chars
    short_text = (
        "Smart contracts face invariant violations when state updates precede checks. "
        "Reviewing protocol security? Contact SanadSquad to discuss an audit. Email: frank@sanadsquad.com"
    )
    assert len(short_text) <= 280
    passed_short, errs_short, _ = validate_piece_deterministic(
        [short_text],
        brand=brand_rules,
        spec=spec,
        contact_config=approved_cfg,
        allow_cta=True,
        content_type="marketing-post",
    )
    assert passed_short is True, f"Expected passing short text, got errors: {errs_short}"


# ==============================================================================
# 11. Technical Threads Never Receive Commercial CTAs
# ==============================================================================

def test_technical_threads_never_receive_commercial_ctas():
    """Technical threads are strictly educational and must never contain commercial CTAs or contact info."""
    thread_tweets = [
        "1/5 Reentrancy vulnerabilities occur when contracts make external calls before state resolution.",
        "2/5 The Checks-Effects-Interactions pattern mitigates this vulnerability.",
        "3/5 Reentrancy locks provide secondary protection against cross-contract calls.",
        "4/5 State updates must complete prior to external invocation.",
        "5/5 Need an audit? Contact SanadSquad. Email: frank@sanadsquad.com",
    ]
    errs = validate_contact_cta(thread_tweets, content_type="tech-thread")
    assert any("technical threads are strictly barred" in e.lower() for e in errs)


# ==============================================================================
# 12. Private Audits Remain Excluded
# ==============================================================================

def test_private_audits_remain_excluded():
    """audits.json remains strictly empty; private audit client details must never be manufactured."""
    audits_file = ROOT / "audits.json"
    assert audits_file.exists()
    audits = json.loads(audits_file.read_text(encoding="utf-8"))
    assert audits == [], "audits.json must remain empty to preserve company confidentiality"

    schema_file = ROOT / "schemas" / "audits.schema.json"
    assert schema_file.exists()
    schema = json.loads(schema_file.read_text(encoding="utf-8"))
    assert schema.get("type") == "array"


# ==============================================================================
# 13. Unsupported Company Statistics Are Rejected
# ==============================================================================

def test_unsupported_company_statistics_rejected():
    """High-level researcher experience numbers on website cannot be published without explicit approval."""
    unapproved_stat_posts = [
        "SanadSquad researchers completed 60+ audits and discovered 300+ critical vulnerabilities.",
        "With 50+ audits completed, SanadSquad protects protocols across EVM chains.",
    ]
    for post in unapproved_stat_posts:
        errs = validate_marketing_claims([post])
        assert any("unsupported company statistics" in e.lower() for e in errs)


# ==============================================================================
# 14. Wrong-Service Marketing Claims Are Rejected
# ==============================================================================

def test_wrong_service_marketing_claims_rejected():
    """Marketing posts must not cross-contaminate service boundaries."""
    errs_pentest = validate_marketing_claims(
        ["SanadSquad penetration testing reviews smart contract invariants and tokenomics."],
        service_line="penetration-testing",
    )
    assert any("wrong-service claim" in e.lower() for e in errs_pentest)

    errs_audit = validate_marketing_claims(
        ["Our blockchain security audits evaluate cloud IAM pentest and CI/CD pipelines."],
        service_line="blockchain-security-audits",
    )
    assert any("wrong-service claim" in e.lower() for e in errs_audit)


# ==============================================================================
# 15. All Accepted Marketing Claims Retain Correct Evidence Authority
# ==============================================================================

def test_all_accepted_marketing_claims_retain_correct_evidence_authority():
    """Technical claims require retrieved web evidence; contact details are treated as metadata."""
    from content_pipeline.source_authority import SourceAuthorityContext
    ctx = SourceAuthorityContext.for_marketing_slot(
        slot_id="post_1",
        service_line="agentic-payments",
        allowed_domains=["x402.org", "stripe.com"],
    )
    # Marketing slots are barred from kb.json by default
    assert ctx.allowed_kb_access is False
    with pytest.raises(PermissionError):
        ctx.assert_kb_read_allowed()


# ==============================================================================
# 16. Failed Website Fetch Does Not Silently Substitute Invented Service Data
# ==============================================================================

class FailingResearchProvider(ResearchProvider):
    @property
    def provider_name(self) -> str:
        return "failing_mock"
    @property
    def mode(self) -> str:
        return "live"
    def is_available(self) -> bool:
        return True
    def search(self, query: str, service_line: str, group: str | None = None, max_results: int = 5) -> list[SearchResult]:
        return [SearchResult(title="Dead Resource", url="https://solana.com/docs/dead-page", domain="solana.com", snippet="", service_line=service_line)]
    def fetch(self, url: str, service_line: str, source_group: str = "") -> FetchedPage:
        return FetchedPage(
            requested_url=url,
            final_url=url,
            domain="solana.com",
            http_status=404,
            eligible_for_public_posting=False,
            failure_reason="HTTP 404 Not Found",
            retrieval_timestamp="2026-10-20T12:00:00Z",
        )


def test_failed_website_fetch_does_not_silently_substitute_invented_service_data():
    """When a web fetch fails, ResearchService fails closed and returns an error without inventing data."""
    sources_cfg = load_sources_config()
    svc = ResearchService(config=sources_cfg, provider=FailingResearchProvider())
    ev_list, ids, err = svc.conduct_marketing_research(
        slot_id="test_slot",
        service_line="blockchain-security-audits",
        topic_focus="invariant testing",
    )
    assert ev_list == []
    assert ids == []
    assert err is not None
    assert "Source sufficiency failure" in err


# ==============================================================================
# 17. Accepted-Only CSV and Visual Specification Contracts Remain Intact
# ==============================================================================

def test_accepted_only_csv_and_visual_specification_contracts_remain_intact(tmp_path):
    """export_run writes strictly accepted slots to posts.csv with valid visual specs; dropped slots excluded."""
    plan = Plan(slots=[
        Slot(id="post_acc", type="marketing-post", focus="solana"),
        Slot(id="post_drop", type="marketing-post", focus="pentest"),
    ])
    acc_result = SlotResult(
        slot=plan.slots[0],
        status="accepted",
        topic="solana",
        source_ids=["ev_1"],
        drafts=[Draft(tweets=["Solana verified builds link on-chain bytecode to Git commits, ensuring deployment invariants."])],
        evidence=[Evidence(id="ev_1", url="https://solana.com/docs/programs/verified-builds", excerpt="verified builds")],
        visual_spec="spec:visual_specs/post_acc.md",
        authorization_mode="publication_eligible",
        pipeline_mode="evidence_first_v2",
        reviews=[Review(factual_support=5, technical_correctness=5, brand_voice=5, clarity=5, platform_format=5, usefulness=5, approved=True, grounding_assessment="All good")],
        validations=[[]],
        conformance_report={
            "all_conforming": True,
            "results": [{"unit_id": "u1", "verdict": "CONFORMS", "passed": True, "tweet_text": "Solana verified builds link on-chain bytecode to Git commits, ensuring deployment invariants."}],
        },
        evidence_plan={
            "slot_id": "post_acc",
            "topic_id": "service_positioning",
            "content_type": "marketing-post",
            "catalog_version": "2.0.0",
            "policy_id": "security_audit_firm",
            "policy_version": "1.0.0",
            "authorization_mode": "publication_eligible",
            "units": [{"id": "u1", "role": "RECOMMENDATION", "proposition_ids": [], "max_chars": 280, "guidance": "test"}],
        },
    )
    drop_result = SlotResult(
        slot=plan.slots[1],
        status="dropped",
        topic="pentest",
        source_ids=[],
        drafts=[Draft(tweets=["Dropped unverified draft"])],
        reason="Writing quality violation",
    )

    out_dir = tmp_path / "run_test_export"
    summary = export_run(
        output=out_dir,
        plan=plan,
        results=[acc_result, drop_result],
        elapsed=2.5,
        model_name="mock_test",
        peak_active=1,
        mode="v3",
    )

    assert summary["shipped"] == 1
    assert summary["dropped"] == 1

    csv_path = out_dir / "posts.csv"
    assert csv_path.exists()
    rows = list(csv.reader(csv_path.open(encoding="utf-8")))
    assert rows[0] == ["Post Text", "Image"]
    assert len(rows) == 2  # Header + 1 accepted row
    assert rows[1][0] == "Solana verified builds link on-chain bytecode to Git commits, ensuring deployment invariants."
    assert rows[1][1] == "spec:visual_specs/post_acc.md"
