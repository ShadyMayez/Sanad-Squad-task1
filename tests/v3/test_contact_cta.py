"""Permanent regression tests for SanadSquad Marketing Contact CTA Integration.

Directive: SANADSQUAD_V3_OFFICIAL_BRAND_INTEGRATION_01

Enforces deterministic validation of:
1. Rejection of unapproved email addresses, fictional phone numbers (+1-555-0199), and synthetic contacts (contact@sanadsquad.com).
2. Rejection of recruitment email (career@sanadsquad.com) for commercial CTAs.
3. Graceful handling of missing phone numbers (email-only and website contact form CTAs).
4. Rejection of contact details when approval status is false.
5. Rejection of more than one weekly marketing CTA across three marketing posts.
6. Rejection of multiple CTAs within one post.
7. Match verification of displayed email/channels against approved configuration.
8. Verification of 280-character limit after contact information is inserted.
9. Technical threads strictly barred from commercial CTAs or contact info.
10. Contextual CTA template generation across all 5 official services without banned characters.
11. Contact metadata treated strictly as company info, never external research evidence.
"""
from __future__ import annotations

import json
import pytest
from pathlib import Path

from content_pipeline.contact_config import (
    CompanyContactConfig,
    load_company_contact,
    build_contextual_cta,
    is_synthetic_contact,
    is_recruitment_email,
)
from content_pipeline.marketing_policy import (
    detect_commercial_cta,
    validate_contact_cta,
    validate_marketing_claims,
)
from content_pipeline.marketing_planner import (
    WeeklyMarketingPlan,
    MarketingSlotMetadata,
    MarketingFormat,
    validate_weekly_marketing_results,
    OFFICIAL_COMMERCIAL_SERVICES,
    normalize_commercial_service,
    map_service_to_research_category,
)
from content_pipeline.validation import validate_piece_deterministic
from content_pipeline.schemas import (
    BrandRules,
    Slot,
    SlotResult,
    Draft,
    Claim,
    Evidence,
    WriterConfig,
)


@pytest.fixture
def approved_contact() -> CompanyContactConfig:
    return CompanyContactConfig(
        company_name="SanadSquad",
        business_inquiries_email="frank@sanadsquad.com",
        business_phone_number=None,
        contact_form_url="https://sanadsquad.com/contact/",
        telegram="@castle_chain",
        x_handle="@SanadSquad",
        official_website="https://sanadsquad.com",
        approved=True,
        status="APPROVED",
        approved_by="SanadSquad Project Owner",
        notes="Verified website contact details per Directive SANADSQUAD_V3_OFFICIAL_BRAND_INTEGRATION_01.",
    )


@pytest.fixture
def approved_contact_with_phone() -> CompanyContactConfig:
    return CompanyContactConfig(
        company_name="SanadSquad",
        business_inquiries_email="frank@sanadsquad.com",
        business_phone_number="+44 20 7946 0991",
        contact_form_url="https://sanadsquad.com/contact/",
        telegram="@castle_chain",
        x_handle="@SanadSquad",
        official_website="https://sanadsquad.com",
        approved=True,
        status="APPROVED",
    )


@pytest.fixture
def unapproved_contact() -> CompanyContactConfig:
    return CompanyContactConfig(
        company_name="SanadSquad",
        business_inquiries_email="frank@sanadsquad.com",
        business_phone_number=None,
        approved=False,
        status="AWAITING_OWNER_APPROVAL",
    )


@pytest.fixture
def empty_contact() -> CompanyContactConfig:
    return CompanyContactConfig(
        company_name="SanadSquad",
        business_inquiries_email="",
        business_phone_number=None,
        contact_form_url=None,
        approved=False,
        status="AWAITING_OWNER_APPROVAL",
    )


@pytest.fixture
def brand_rules() -> BrandRules:
    return BrandRules(
        approved_statistics=["100%"],
        banned_words=["leverage", "delve", "robust"],
        banned_characters=["—", "–", "“", "”", "’"],
        forbid_hashtags=True,
        allowed_links=["https://x402.org", "https://solana.com", "https://sanadsquad.com"],
    )


class TestCompanyContactConfiguration:
    def test_empty_config_reports_missing_fields(self, empty_contact):
        assert not empty_contact.is_operational()
        missing = empty_contact.get_missing_fields()
        assert any("business_inquiries_email" in m for m in missing)
        assert any("approved" in m for m in missing)

    def test_reject_synthetic_email_in_approved_config(self):
        with pytest.raises(ValueError, match="Fictional or unapproved contact placeholder"):
            CompanyContactConfig(
                company_name="SanadSquad",
                business_inquiries_email="contact@sanadsquad.com",
                approved=True,
            )

    def test_reject_synthetic_phone_in_approved_config(self):
        with pytest.raises(ValueError, match="Fictional telephone number"):
            CompanyContactConfig(
                company_name="SanadSquad",
                business_inquiries_email="frank@sanadsquad.com",
                business_phone_number="+1-555-0199",
                approved=True,
            )

    def test_reject_recruitment_email_for_commercial_inquiries(self):
        with pytest.raises(ValueError, match="Recruitment email"):
            CompanyContactConfig(
                company_name="SanadSquad",
                business_inquiries_email="career@sanadsquad.com",
                approved=True,
            )

    def test_missing_phone_handled_gracefully(self, approved_contact):
        assert approved_contact.is_operational()
        assert approved_contact.business_phone_number is None
        assert approved_contact.status == "APPROVED"
        assert approved_contact.get_missing_fields() == []

    def test_approved_phone_requires_country_code(self):
        with pytest.raises(ValueError, match="must include a country code starting with '\\+'"):
            CompanyContactConfig(
                company_name="SanadSquad",
                business_inquiries_email="frank@sanadsquad.com",
                business_phone_number="02079460991",
                approved=True,
            )


class TestContextualCTAGeneration:
    def test_contextual_cta_generation_all_five_official_services(self, approved_contact):
        services = [
            ("blockchain-security-audits", "audit"),
            ("penetration-testing", "infrastructure"),
            ("agentic-security-tooling", "ai detectors"),
            ("agentic-payments", "payment agent"),
            ("security-consulting", "architecture"),
        ]
        for s_line, expected_keyword in services:
            cta = build_contextual_cta(s_line, approved_contact)
            assert "frank@sanadsquad.com" in cta
            assert expected_keyword.lower() in cta.lower()
            # Must NOT contain phone when none is configured
            assert "Phone:" not in cta
            assert "+1-555-0199" not in cta
            # Must NOT contain banned characters
            assert "—" not in cta
            assert "–" not in cta
            assert "“" not in cta
            assert "”" not in cta
            assert "’" not in cta

    def test_contextual_cta_generation_with_phone_when_configured(self, approved_contact_with_phone):
        cta = build_contextual_cta("blockchain-security-audits", approved_contact_with_phone)
        assert "frank@sanadsquad.com" in cta
        assert "+44 20 7946 0991" in cta
        assert "Phone: +44 20 7946 0991" in cta

    def test_unapproved_contact_cannot_build_cta(self, unapproved_contact):
        with pytest.raises(ValueError, match="Contact details are not approved or operational"):
            build_contextual_cta("blockchain-security-audits", unapproved_contact)


class TestDeterministicValidationRules:
    def test_reject_when_approval_status_is_false(self, unapproved_contact):
        tweet = (
            "SVM accounts without owner checks allow unauthorized authority transfers. "
            "Reviewing protocol security? Contact SanadSquad to discuss. "
            "Email: frank@sanadsquad.com"
        )
        errors = validate_contact_cta(
            tweets=[tweet],
            contact_config=unapproved_contact,
            allow_cta=True,
            content_type="marketing-post",
        )
        assert any("approval status is false" in err for err in errors)

    def test_reject_synthetic_contact_email(self, approved_contact):
        tweet = (
            "Reviewing protocol security? Contact SanadSquad to discuss. "
            "Email: contact@sanadsquad.com"
        )
        errors = validate_contact_cta(
            tweets=[tweet],
            contact_config=approved_contact,
            allow_cta=True,
            content_type="marketing-post",
        )
        assert any("Fictional or unapproved contact placeholder 'contact@sanadsquad.com'" in err for err in errors)

    def test_reject_synthetic_phone_number(self, approved_contact):
        tweet = (
            "Reviewing protocol security? Contact SanadSquad to discuss. "
            "Email: frank@sanadsquad.com | Phone: +1-555-0199"
        )
        errors = validate_contact_cta(
            tweets=[tweet],
            contact_config=approved_contact,
            allow_cta=True,
            content_type="marketing-post",
        )
        assert any("Fictional telephone placeholder '+1-555-0199'" in err for err in errors)

    def test_reject_recruitment_email(self, approved_contact):
        tweet = (
            "Building AI payment agents? Contact SanadSquad: career@sanadsquad.com"
        )
        errors = validate_contact_cta(
            tweets=[tweet],
            contact_config=approved_contact,
            allow_cta=True,
            content_type="marketing-post",
        )
        assert any("Recruitment email 'career@sanadsquad.com'" in err for err in errors)

    def test_missing_phone_accepted_gracefully(self, approved_contact):
        tweet = (
            "Reviewing protocol security? Contact SanadSquad to discuss: frank@sanadsquad.com"
        )
        errors = validate_contact_cta(
            tweets=[tweet],
            contact_config=approved_contact,
            allow_cta=True,
            content_type="marketing-post",
        )
        assert errors == []

    def test_reject_unapproved_published_phone(self, approved_contact):
        tweet = (
            "Reviewing protocol security? Contact SanadSquad: frank@sanadsquad.com | Phone: +1-202-555-0143"
        )
        errors = validate_contact_cta(
            tweets=[tweet],
            contact_config=approved_contact,
            allow_cta=True,
            content_type="marketing-post",
        )
        assert any("does not publish an approved phone number" in err for err in errors)

    def test_reject_cta_when_slot_not_reserved(self, approved_contact):
        tweet = (
            "Solana token accounts require sign_v1 signer validation. "
            "Contact SanadSquad to discuss risks. Email: frank@sanadsquad.com"
        )
        errors = validate_contact_cta(
            tweets=[tweet],
            contact_config=approved_contact,
            allow_cta=False,
            content_type="marketing-post",
        )
        assert any("CTA eligibility is not reserved" in err for err in errors)

    def test_reject_multiple_ctas_in_single_post(self, approved_contact):
        tweet = (
            "Work with SanadSquad for your smart contract audits. "
            "Also schedule an audit with our team. "
            "Email: frank@sanadsquad.com"
        )
        errors = validate_contact_cta(
            tweets=[tweet],
            contact_config=approved_contact,
            allow_cta=True,
            content_type="marketing-post",
        )
        assert any("Maximum 1 CTA permitted per post" in err for err in errors)

    def test_reject_technical_threads_with_cta_or_contact_info(self, approved_contact):
        tweet = "Contact SanadSquad for your audits: frank@sanadsquad.com"
        errors = validate_contact_cta(
            tweets=[tweet],
            contact_config=approved_contact,
            allow_cta=True,
            content_type="tech-thread",
        )
        assert any("Technical threads are strictly barred" in err for err in errors)

    def test_reject_character_count_over_280_after_cta(self, approved_contact):
        long_insight = (
            "State-machine flaws in Solana account abstraction programs allow unauthenticated accounts "
            "to execute arbitrary cross-program invocations when token limits are not strictly enforced in runtime bytecode. "
            "This vulnerability occurs across multiple program boundaries. "
        )
        cta = build_contextual_cta("blockchain-security-audits", approved_contact)
        oversized_tweet = f"{long_insight}{cta}"
        assert len(oversized_tweet) > 280

        errors = validate_contact_cta(
            tweets=[oversized_tweet],
            contact_config=approved_contact,
            allow_cta=True,
            content_type="marketing-post",
        )
        assert any("exceeds 280-character limit" in err for err in errors)

    def test_passing_post_with_approved_cta_under_280(self, approved_contact, brand_rules):
        tweet = (
            "SVM accounts without owner checks allow authority hijacking. "
            "Reviewing protocol security? Contact SanadSquad to discuss an audit: frank@sanadsquad.com"
        )
        assert len(tweet) <= 280

        passed, errors, _ = validate_piece_deterministic(
            tweets=[tweet],
            brand=brand_rules,
            spec=WriterConfig(instruction_file="instructions/marketing-post.md", min_tweets=1, max_tweets=1, max_chars=280),
            contact_config=approved_contact,
            allow_cta=True,
            content_type="marketing-post",
        )
        assert passed, f"Expected validation pass but got errors: {errors}"
        assert errors == []


class TestFiveOfficialServicesAndClaims:
    def test_all_five_official_services_recognized(self):
        assert len(OFFICIAL_COMMERCIAL_SERVICES) == 5
        for s in [
            "blockchain-security-audits",
            "penetration-testing",
            "agentic-security-tooling",
            "agentic-payments",
            "security-consulting",
        ]:
            assert s in OFFICIAL_COMMERCIAL_SERVICES
            norm = normalize_commercial_service(s)
            assert norm == s

    def test_four_category_research_taxonomy_mapping(self):
        mappings = {
            "blockchain-security-audits": "web3-security",
            "penetration-testing": "pentesting",
            "agentic-security-tooling": "agentic-security",
            "agentic-payments": "agentic-payments",
            "security-consulting": "web3-security",
        }
        for s, expected_tax in mappings.items():
            assert map_service_to_research_category(s) == expected_tax

    def test_reject_unsupported_company_statistics(self):
        bad_texts = [
            "SanadSquad completed 60+ Rust audits with zero post-deployment issues.",
            "Our researchers uncovered 300+ criticals across EVM and SVM protocols.",
            "We have completed 50+ audits with a 100% success rate.",
        ]
        for t in bad_texts:
            errs = validate_marketing_claims([t])
            assert any("unsupported company statistics" in e.lower() for e in errs)

    def test_reject_generic_marketing_claims(self):
        generic_claims = [
            "We secure everything across Web3 and AI financial platforms.",
            "SanadSquad provides the best blockchain security in the market.",
            "Contact us for all your cybersecurity needs.",
        ]
        for g in generic_claims:
            errs = validate_marketing_claims([g])
            assert any("generic marketing claims prohibited" in e.lower() for e in errs)

    def test_reject_wrong_service_marketing_claims(self):
        # Claiming pentesting tests smart contract invariants
        errs_pt = validate_marketing_claims(
            ["Our penetration testing verifies smart contract invariants on Solana."],
            service_line="penetration-testing",
        )
        assert any("wrong-service claim" in e.lower() for e in errs_pt)

        # Claiming blockchain audits perform cloud IAM pentests
        errs_audit = validate_marketing_claims(
            ["SanadSquad blockchain security audits review your cloud IAM pentest configurations."],
            service_line="blockchain-security-audits",
        )
        assert any("wrong-service claim" in e.lower() for e in errs_audit)


class TestWeeklyPlannerCTAFrequency:
    def test_weekly_plan_rejects_more_than_one_cta_in_three_posts(self):
        slots = [
            MarketingSlotMetadata(
                slot_id="s1",
                commercial_service="blockchain-security-audits",
                service_line="blockchain-security-audits",
                research_category="web3-security",
                research_angle="deployment drift",
                selected_format=MarketingFormat.DIFFERENTIATION,
                requires_link=False,
                forbids_link=False,
                has_cta=True,
                topic_fingerprint="fp1",
            ),
            MarketingSlotMetadata(
                slot_id="s2",
                commercial_service="agentic-security-tooling",
                service_line="agentic-security-tooling",
                research_category="agentic-security",
                research_angle="prompt injection",
                selected_format=MarketingFormat.NEWS_REACTION,
                requires_link=True,
                forbids_link=False,
                has_cta=True,  # Second CTA violation!
                topic_fingerprint="fp2",
            ),
            MarketingSlotMetadata(
                slot_id="s3",
                commercial_service="agentic-payments",
                service_line="agentic-payments",
                research_category="agentic-payments",
                research_angle="x402 vs mpp",
                selected_format=MarketingFormat.LEARNING_RESOURCE,
                requires_link=True,
                forbids_link=False,
                has_cta=False,
                topic_fingerprint="fp3",
            ),
        ]
        plan = WeeklyMarketingPlan(slots=slots)
        errors = plan.validate_constraints()
        assert any("Weekly mix violation: 2 marketing posts contain CTAs" in err for err in errors)

    def test_weekly_results_reject_multiple_ctas_across_three_posts(self):
        slot1 = Slot(id="m1", type="marketing-post", service_line="blockchain-security-audits")
        slot2 = Slot(id="m2", type="marketing-post", service_line="agentic-security-tooling")
        slot3 = Slot(id="m3", type="marketing-post", service_line="agentic-payments")

        r1 = SlotResult(
            slot=slot1,
            status="accepted",
            drafts=[Draft(tweets=[
                "SVM account checks prevent authority hijacking. "
                "Contact SanadSquad to discuss an audit: frank@sanadsquad.com"
            ])],
        )
        r2 = SlotResult(
            slot=slot2,
            status="accepted",
            drafts=[Draft(tweets=[
                "Agent tool abuse requires spending policy bounds. Details: https://x402.org"
            ])],
        )
        r3 = SlotResult(
            slot=slot3,
            status="accepted",
            drafts=[Draft(tweets=[
                "x402 protocol uses HTTP 402 for facilitator settlement. Details: https://x402.org. "
                "Building a payment agent? Contact SanadSquad: frank@sanadsquad.com"
            ])],
        )

        errors = validate_weekly_marketing_results([r1, r2, r3])
        assert any("Weekly accepted marketing results contain 2 posts with CTAs" in err for err in errors)

    def test_weekly_results_pass_with_exactly_one_cta_across_three_posts(self):
        slot1 = Slot(id="m1", type="marketing-post", service_line="blockchain-security-audits")
        slot2 = Slot(id="m2", type="marketing-post", service_line="agentic-security-tooling")
        slot3 = Slot(id="m3", type="marketing-post", service_line="agentic-payments")

        r1 = SlotResult(
            slot=slot1,
            status="accepted",
            drafts=[Draft(tweets=[
                "SVM account validation must check owner programs before CPI execution to avoid account state confusion."
            ])],
        )
        r2 = SlotResult(
            slot=slot2,
            status="accepted",
            drafts=[Draft(tweets=[
                "AI agent wallet safety depends on strict tool authorization boundaries. Research: https://x402.org"
            ])],
        )
        r3 = SlotResult(
            slot=slot3,
            status="accepted",
            drafts=[Draft(tweets=[
                "x402 uses HTTP 402 for agentic payments. Guide: https://x402.org "
                "Building a payment agent? SanadSquad reviews authorization and facilitator integrations: frank@sanadsquad.com"
            ])],
        )

        errors = validate_weekly_marketing_results([r1, r2, r3])
        assert errors == [], f"Expected clean weekly validation, got: {errors}"


class TestNonEvidenceTreatment:
    def test_contact_details_not_treated_as_evidence(self, approved_contact):
        with pytest.raises(Exception):
            Evidence.model_validate(approved_contact.model_dump())
