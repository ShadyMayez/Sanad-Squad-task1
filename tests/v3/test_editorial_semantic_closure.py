"""Targeted adversarial and conformance tests for editorial accuracy and service alignment closure.

Directive: SANADSQUAD_V3_EDITORIAL_SEMANTIC_CLOSURE_02

Demonstrates rejection of:
1. An OWASP claim linked only to a Simon Willison article.
2. A legitimate source incorrectly described as a different organization's standard.
3. Unsupported absolute claims about preventing prompt injection.
4. A technically correct but service-irrelevant consulting post.
5. x402 statements incorrectly making facilitators mandatory.
6. Verified-build claims that confuse matching bytecode with security.
7. Unsupported attribution despite successful HTTP retrieval.

Includes counterexamples demonstrating acceptance of accurate, properly attributed posts
across all five official SanadSquad commercial services.
"""
from __future__ import annotations

import pytest

from content_pipeline.marketing_policy import (
    validate_editorial_semantic_conformance,
    validate_marketing_claims,
)
from content_pipeline.validation import validate_piece_deterministic
from content_pipeline.schemas import BrandRules, WriterConfig
from content_pipeline.marketing_format import MarketingFormat


@pytest.fixture
def default_brand() -> BrandRules:
    return BrandRules(
        approved_statistics=["100%"],
        banned_characters=["—", "–", "“", "”", "’"],
        forbid_hashtags=True,
        banned_words=["vital", "crucial", "landscape", "delve"],
        allowed_links=[
            "https://genai.owasp.org/resource/agent-control-standard-acs/",
            "https://simonwillison.net/2023/Apr/14/worst-that-can-happen/",
            "https://github.com/x402-foundation/x402",
            "https://github.com/coinbase/x402",
            "https://solana.com/docs/programs/verified-builds",
            "https://solana.com/docs/core/programs/program-deployment",
            "https://api-security.owasp.org/editions/2023/en/0x11-t10/",
        ],
    )


@pytest.fixture
def marketing_spec() -> WriterConfig:
    return WriterConfig(
        name="marketing-post",
        instruction_file="instructions/marketing-post.md",
        min_tweets=1,
        max_tweets=1,
        max_chars=280,
        require_review_invitation=False,
    )


# =========================================================================
# 1. OWASP Claim Linked to Simon Willison Blog Rejection
# =========================================================================
def test_rejects_owasp_claim_linked_to_simon_willison_blog():
    """Verify rejection of OWASP claim linked to Simon Willison's personal research blog."""
    tweet = (
        "OWASP Agent Control Standards define hard execution boundaries outside LLM context to prevent prompt injection. "
        "Review the spec: https://simonwillison.net/2023/Apr/14/worst-that-can-happen/"
    )
    errors = validate_editorial_semantic_conformance([tweet], service_line="agentic-security-tooling")

    # Must reject publisher attribution mismatch
    assert any("publisher attribution mismatch" in e.lower() for e in errors)
    assert any("simon willison's personal blog" in e.lower() for e in errors)
    # Must reject "the spec" mislabeling
    assert any("not a formal specification" in e.lower() for e in errors)
    # Must reject universal prompt injection prevention claim
    assert any("prevent prompt injection" in e.lower() for e in errors)


# =========================================================================
# 2. Legitimate Source Described as Different Organization's Standard
# =========================================================================
def test_rejects_legitimate_source_described_as_different_org_standard():
    """Verify rejection when a researcher's blog is described as an official OWASP standard."""
    tweet = (
        "According to OWASP GenAI standards, tools must have execution limits. "
        "Review the spec: https://simonwillison.net/2023/Apr/14/worst-that-can-happen/"
    )
    errors = validate_editorial_semantic_conformance([tweet], service_line="agentic-security-tooling")
    assert any("publisher attribution mismatch" in e.lower() for e in errors)


# =========================================================================
# 3. Absolute Prompt Injection Prevention Claims Rejection
# =========================================================================
def test_rejects_unsupported_absolute_prompt_injection_prevention_claims():
    """Verify rejection of claims that runtime controls universally prevent prompt injection."""
    tweet = (
        "Enforcing hard runtime execution boundaries around AI agent tools to prevent prompt injection across all workflows."
    )
    errors = validate_editorial_semantic_conformance([tweet], service_line="agentic-security-tooling")
    assert any("overstated certainty" in e.lower() and "prevent prompt injection" in e.lower() for e in errors)


# =========================================================================
# 4. Service-Irrelevant Consulting Post Rejection
# =========================================================================
def test_rejects_technically_correct_but_service_irrelevant_consulting_post():
    """Verify rejection of a post that describes Solana upgrade authority without explaining consulting."""
    tweet = (
        "Deploying a Solana program assigns an initial upgrade authority in ProgramData. "
        "If not transferred to multi-sig or revoked, that authority can alter code anytime."
    )
    errors = validate_editorial_semantic_conformance([tweet], service_line="security-consulting")
    assert any("weak service alignment" in e.lower() and "consulting" in e.lower() for e in errors)


# =========================================================================
# 5. Mandatory x402 Facilitator Claims Rejection
# =========================================================================
def test_rejects_x402_mandatory_facilitator_claims():
    """Verify rejection of claims that all x402 deployments require third-party facilitators."""
    tweet = (
        "The x402 protocol standardizes payment signaling, but all x402 deployments require a third-party facilitator "
        "for payment settlement. https://github.com/x402-foundation/x402"
    )
    errors = validate_editorial_semantic_conformance([tweet], service_line="agentic-payments")
    assert any("inaccurate x402 requirement" in e.lower() for e in errors)
    assert any("facilitator-based verification and settlement is optional" in e.lower() for e in errors)


# =========================================================================
# 6. Verified-Build Claims Confusing Matching Bytecode with Security Rejection
# =========================================================================
def test_rejects_verified_builds_confusing_bytecode_with_security():
    """Verify rejection of claims that verified builds guarantee application security."""
    tweet = (
        "Solana verified builds prove that deployed bytecode matches the Git commit, "
        "which guarantees application security across deployed contracts."
    )
    errors = validate_editorial_semantic_conformance([tweet], service_line="blockchain-security-audits")
    assert any("inaccurate verified build claim" in e.lower() for e in errors)
    assert any("source-to-deployment correspondence" in e.lower() for e in errors)


# =========================================================================
# 7. Unsupported Attribution Despite Successful HTTP Retrieval Rejection
# =========================================================================
def test_rejects_unsupported_attribution_despite_successful_http_retrieval():
    """Verify rejection when an authentic HTTP 200 URL is misattributed to an unrelated organization."""
    tweet = (
        "OWASP GenAI specifications define Solana program upgrade authorities and multi-sig deployment rules: "
        "https://solana.com/docs/core/programs/program-deployment"
    )
    # The URL resolves and is on the allowlist, but attributing Solana Docs to OWASP GenAI is a publisher attribution mismatch
    errors = validate_editorial_semantic_conformance([tweet], service_line="security-consulting")
    assert any(
        "publisher attribution mismatch" in e.lower() or "source-to-claim" in e.lower()
        for e in errors
    )


# =========================================================================
# 8. Counterexample: Accepted Agentic Tooling Post
# =========================================================================
def test_accepts_properly_attributed_agentic_tooling_counterexample(default_brand, marketing_spec):
    """Verify acceptance of authentic OWASP ACS citation with custom tooling service alignment."""
    tweet = (
        "OWASP Agent Control Standards define runtime tool boundaries to restrict unauthorized actions. "
        "SanadSquad builds custom security detectors and PR reviewers. Review the spec: "
        "https://genai.owasp.org/resource/agent-control-standard-acs/"
    )
    passed, errors, _ = validate_piece_deterministic(
        tweets=[tweet],
        brand=default_brand,
        spec=marketing_spec,
        allowed_run_links=["https://genai.owasp.org/resource/agent-control-standard-acs/"],
        marketing_format="learning-resource",
        service_line="agentic-security-tooling",
    )
    assert passed is True, f"Expected acceptance, got errors: {errors}"
    assert len(errors) == 0


# =========================================================================
# 9. Counterexample: Accepted Security Consulting Post
# =========================================================================
def test_accepts_properly_attributed_consulting_counterexample(default_brand, marketing_spec):
    """Verify acceptance of Solana upgrade authority post meaningfully connected to security consulting."""
    tweet = (
        "Solana programs assign an upgrade authority in ProgramData that retains unilateral power to deploy new bytecode until revoked or transferred. "
        "SanadSquad security consulting helps teams design secure multi-sig governance before deployment."
    )
    passed, errors, _ = validate_piece_deterministic(
        tweets=[tweet],
        brand=default_brand,
        spec=marketing_spec,
        allowed_run_links=[],
        marketing_format="short-tip",
        service_line="security-consulting",
    )
    assert passed is True, f"Expected acceptance, got errors: {errors}"
    assert len(errors) == 0


# =========================================================================
# 10. Counterexample: Accepted Blockchain Security Audits Post
# =========================================================================
def test_accepts_properly_attributed_blockchain_audit_counterexample(default_brand, marketing_spec):
    """Verify acceptance of verified builds post with proper correspondence scope and invariant audits."""
    tweet = (
        "Solana verified builds establish source-to-deployment correspondence, proving bytecode matches Git commit without ensuring application security. "
        "When upgrades change the executable, new versions call for invariant audits."
    )
    passed, errors, _ = validate_piece_deterministic(
        tweets=[tweet],
        brand=default_brand,
        spec=marketing_spec,
        allowed_run_links=[],
        marketing_format="short-tip",
        service_line="blockchain-security-audits",
    )
    assert passed is True, f"Expected acceptance, got errors: {errors}"
    assert len(errors) == 0


# =========================================================================
# 11. Counterexample: Accepted Penetration Testing Post
# =========================================================================
def test_accepts_properly_attributed_pentesting_counterexample(default_brand, marketing_spec):
    """Verify acceptance of BOLA post connecting to dApp backend APIs and relayer infrastructure."""
    tweet = (
        "Broken Object Level Authorization (BOLA) lets authenticated users access unauthorized tenant objects when endpoints omit object checks. "
        "Penetration testing identifies these gaps across dApp backend APIs and relayer infrastructure."
    )
    passed, errors, _ = validate_piece_deterministic(
        tweets=[tweet],
        brand=default_brand,
        spec=marketing_spec,
        allowed_run_links=[],
        marketing_format="short-tip",
        service_line="penetration-testing",
    )
    assert passed is True, f"Expected acceptance, got errors: {errors}"
    assert len(errors) == 0


# =========================================================================
# 12. Counterexample: Accepted Agentic Payments Post
# =========================================================================
def test_accepts_properly_attributed_agentic_payments_counterexample(default_brand, marketing_spec):
    """Verify acceptance of x402 payment signaling post distinguishing optional facilitator settlement."""
    tweet = (
        "The x402 standard defines HTTP 402 payment signaling where resource servers specify payment requirements in headers. "
        "Facilitator-based settlement is optional; direct peer-to-peer settlement is fully supported. "
        "Spec: https://github.com/x402-foundation/x402"
    )
    passed, errors, _ = validate_piece_deterministic(
        tweets=[tweet],
        brand=default_brand,
        spec=marketing_spec,
        allowed_run_links=["https://github.com/x402-foundation/x402"],
        marketing_format="learning-resource",
        service_line="agentic-payments",
    )
    assert passed is True, f"Expected acceptance, got errors: {errors}"
    assert len(errors) == 0
