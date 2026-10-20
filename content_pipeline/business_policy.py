"""Business Policy V1 Contract for SanadSquad Evidence-First V2.

Separates hard, mechanically verifiable business/regulatory constraints from
soft model-interpreted editorial preferences.
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Literal
from pydantic import BaseModel, Field, model_validator


class PlatformConstraints(BaseModel):
    max_tweet_chars: int = 280
    min_tech_thread_tweets: int = 5
    max_tech_thread_tweets: int = 10
    marketing_post_tweets: int = 1
    forbid_hashtags: bool = True
    allowed_domains: list[str] = Field(default_factory=list)


class QualityThresholds(BaseModel):
    min_factual_support: int = Field(default=4, ge=0, le=5)
    min_technical_correctness: int = Field(default=4, ge=0, le=5)
    min_brand_voice: int = Field(default=3, ge=0, le=5)
    min_clarity: int = Field(default=3, ge=0, le=5)
    min_platform_format: int = Field(default=3, ge=0, le=5)
    min_usefulness: int = Field(default=3, ge=0, le=5)


class HumanReviewRequirements(BaseModel):
    require_human_approval_for_ship: bool = False
    flag_ambiguous_verdicts: bool = True
    flag_financial_or_legal_topics: bool = True


class BusinessPolicy(BaseModel):
    business_id: str
    policy_version: str
    brand_profile: str
    target_audience: str
    content_objectives: list[str] = Field(min_length=1)
    approved_source_ids: list[str] = Field(min_length=1)
    allowed_topics: list[str] = Field(min_length=1)
    prohibited_claim_categories: list[str] = Field(default_factory=list)
    platform_constraints: PlatformConstraints = Field(default_factory=PlatformConstraints)
    mandatory_disclaimers: list[str] = Field(default_factory=list)
    allowed_content_types: list[str] = Field(default_factory=lambda: ["tech-thread", "marketing-post"])
    quality_thresholds: QualityThresholds = Field(default_factory=QualityThresholds)
    human_review_requirements: HumanReviewRequirements = Field(default_factory=HumanReviewRequirements)

    @property
    def policy_id(self) -> str:
        return self.business_id

    def compute_hash(self) -> str:
        import hashlib
        return hashlib.sha256(self.model_dump_json(exclude_none=True).encode("utf-8")).hexdigest()

    @model_validator(mode="after")
    def validate_policy_invariants(self) -> BusinessPolicy:
        if not self.business_id.strip():
            raise ValueError("business_id cannot be empty")
        if not self.policy_version.strip():
            raise ValueError("policy_version cannot be empty")
        if not self.approved_source_ids:
            raise ValueError("approved_source_ids cannot be empty")
        if not self.allowed_topics:
            raise ValueError("allowed_topics cannot be empty")
        return self

    def check_hard_policy_compliance(
        self,
        topic_id: str,
        content_type: str,
        used_source_ids: list[str],
        tweet_texts: list[str],
    ) -> tuple[bool, list[str]]:
        """Mechanically check hard business rules without LLM speculation."""
        violations: list[str] = []

        # 1. Allowed topic check
        # For marketing posts or external tech posts, topics are dynamic research topics
        is_marketing = content_type == "marketing-post" or topic_id.startswith("MKT_")
        is_external_tech = topic_id.startswith("TECH_EXT_")

        if is_marketing:
            valid_marketing_services = {
                "web3-security", "pentesting", "agentic-security", "agentic-payments",
                "web3", "web2", "ai", "payments", "solana", "evm", "infrastructure",
                "prompt injection", "x402", "mpp", "smart contract", "access control",
                "reentrancy", "oracle manipulation", "wallet",
            }
            topic_lower = topic_id.lower()
            topic_allowed = (
                topic_id.startswith("MKT_")
                or any(s in topic_lower for s in valid_marketing_services)
                or any(t.lower() in topic_lower or topic_lower in t.lower() for t in self.allowed_topics)
            )
        elif is_external_tech:
            topic_allowed = True
        else:
            # Match static KB topic ID or topic name
            topic_allowed = any(
                t.lower() in topic_id.lower() or topic_id.lower() in t.lower()
                for t in self.allowed_topics
            )

        if not topic_allowed:
            violations.append(f"Hard Policy Violation: Topic {topic_id!r} is not in allowed_topics: {self.allowed_topics}")

        # 2. Allowed content type
        if content_type not in self.allowed_content_types:
            violations.append(f"Hard Policy Violation: Content type {content_type!r} is not in allowed_content_types: {self.allowed_content_types}")

        # 3. Approved source IDs check
        unapproved_sources = []
        for sid in used_source_ids:
            if is_marketing and (sid.startswith("ev_web_") or sid.startswith("supp_")):
                continue
            if is_external_tech and sid.startswith("ev_tech_ext_"):
                continue
            normalized_sids = {sid, f"SRC_{sid.replace('-', '_')}", sid.replace("SRC_", "").replace("_", "-")}
            if not any(ns in self.approved_source_ids for ns in normalized_sids):
                unapproved_sources.append(sid)
        if unapproved_sources:
            violations.append(f"Hard Policy Violation: Unapproved source(s) used: {unapproved_sources}")

        # 4. Platform length and tweet count constraints
        if content_type == "marketing-post":
            if len(tweet_texts) != self.platform_constraints.marketing_post_tweets:
                violations.append(f"Hard Policy Violation: Marketing post must have exactly {self.platform_constraints.marketing_post_tweets} tweet(s), got {len(tweet_texts)}")
        elif content_type == "tech-thread":
            if not (self.platform_constraints.min_tech_thread_tweets <= len(tweet_texts) <= self.platform_constraints.max_tech_thread_tweets):
                violations.append(
                    f"Hard Policy Violation: Technical thread must have between {self.platform_constraints.min_tech_thread_tweets} and {self.platform_constraints.max_tech_thread_tweets} tweets, got {len(tweet_texts)}"
                )

        for idx, text in enumerate(tweet_texts, 1):
            if len(text) > self.platform_constraints.max_tweet_chars:
                violations.append(f"Hard Policy Violation: Tweet {idx} exceeds {self.platform_constraints.max_tweet_chars} chars ({len(text)} chars)")
            if self.platform_constraints.forbid_hashtags and "#" in text:
                violations.append(f"Hard Policy Violation: Tweet {idx} contains forbidden hashtag")

        # 5. Prohibited phrases / categories
        for prohibited in self.prohibited_claim_categories:
            for idx, text in enumerate(tweet_texts, 1):
                if prohibited.lower() in text.lower():
                    violations.append(f"Hard Policy Violation: Tweet {idx} contains prohibited claim category/term: {prohibited!r}")

        # 6. Mandatory disclaimers
        for disclaimer in self.mandatory_disclaimers:
            if not any(disclaimer.lower() in text.lower() for text in tweet_texts):
                violations.append(f"Hard Policy Violation: Missing mandatory disclaimer: {disclaimer!r}")

        return (len(violations) == 0, violations)


def load_business_policy(policy_path: Path | str | None = None) -> BusinessPolicy:
    """Load and validate a BusinessPolicy JSON specification."""
    if policy_path is None:
        policy_path = "security_audit_firm"
    p = Path(policy_path)
    if not p.exists():
        from .config import ROOT
        cand = ROOT / "knowledge" / "evidence_first_v2" / "policies" / f"{policy_path}.json"
        if cand.exists():
            p = cand
        elif (ROOT / "knowledge" / "evidence_first_v2" / "policies" / policy_path).exists():
            p = ROOT / "knowledge" / "evidence_first_v2" / "policies" / policy_path
        else:
            raise FileNotFoundError(f"Business policy file not found: {policy_path}")
    return BusinessPolicy.model_validate_json(p.read_text())


# Built-in synthetic profile generators for testing (Stage 5 requirements)
def create_synthetic_profiles(root_dir: Path) -> dict[str, Path]:
    """Generate the three mandated synthetic business profiles for testing."""
    policies_dir = root_dir / "knowledge" / "evidence_first_v2" / "policies"
    policies_dir.mkdir(parents=True, exist_ok=True)

    profiles = {
        "security_audit_firm": BusinessPolicy(
            business_id="sanadsquad_security_audit",
            policy_version="1.0.0",
            brand_profile="Authoritative, cautious, deeply technical smart contract auditing firm.",
            target_audience="Protocol founders, lead smart contract engineers, security researchers.",
            content_objectives=["Educate developers on subtle EVM vulnerability mechanisms", "Promote rigorous auditing workflows"],
            approved_source_ids=[
                "SWC-107", "SWC-104", "SWC-113", "SWC-105", "SCWE-028", "SWC-107-1", "OWASP-SC03",
                "SRC_SWC_107", "SRC_SWC_104", "SRC_SWC_113", "SRC_SWC_105", "SRC_SCWE_028", "SRC_OWASP_SC03", "SRC_OZ_REENTRANCY", "SRC_OZ_OWNABLE"
            ],
            allowed_topics=["SWC-107", "SWC-104", "SWC-113", "SWC-105", "SCWE-028", "reentrancy", "access control", "oracle manipulation", "call return", "failed call", "price oracle", "withdrawal", "ether withdrawal"],
            prohibited_claim_categories=["100% secure", "unhackable", "revolutionary", "zero risk", "guaranteed exploit prevention"],
            platform_constraints=PlatformConstraints(max_tweet_chars=280, forbid_hashtags=True),
            mandatory_disclaimers=[],
            quality_thresholds=QualityThresholds(min_factual_support=4, min_technical_correctness=4),
            human_review_requirements=HumanReviewRequirements(require_human_approval_for_ship=False),
        ),
        "strict_professional_client": BusinessPolicy(
            business_id="strict_enterprise_auditing",
            policy_version="1.0.0",
            brand_profile="Conservative, institutional enterprise security client.",
            target_audience="C-suite executives, compliance officers, enterprise risk committees.",
            content_objectives=["Highlight regulatory compliance and systematic risk reduction"],
            approved_source_ids=["SWC-107", "SWC-105", "SRC_SWC_107", "SRC_SWC_105", "SRC_OZ_OWNABLE"],
            allowed_topics=["SWC-107", "SWC-105", "reentrancy", "access control"],
            prohibited_claim_categories=["guaranteed", "immediate hack", "massive exploit", "financial loss"],
            platform_constraints=PlatformConstraints(max_tweet_chars=280, forbid_hashtags=True),
            mandatory_disclaimers=["Educational overview only."],
            quality_thresholds=QualityThresholds(min_factual_support=5, min_technical_correctness=5),
            human_review_requirements=HumanReviewRequirements(require_human_approval_for_ship=True),
        ),
        "creative_tech_brand": BusinessPolicy(
            business_id="creative_web3_labs",
            policy_version="1.0.0",
            brand_profile="Dynamic, high-energy Web3 developer tooling brand.",
            target_audience="Hackathon developers, EVM builders, DeFi developers.",
            content_objectives=["Engage developers with punchy, actionable EVM security best practices"],
            approved_source_ids=[
                "SWC-107", "SWC-104", "SWC-113", "SWC-105", "SCWE-028", "SWC-107-1", "OWASP-SC03",
                "SRC_SWC_107", "SRC_SWC_104", "SRC_SWC_113", "SRC_SWC_105", "SRC_SCWE_028", "SRC_OWASP_SC03", "SRC_OZ_REENTRANCY", "SRC_OZ_OWNABLE"
            ],
            allowed_topics=["SWC-107", "SWC-104", "SWC-113", "SWC-105", "SCWE-028", "reentrancy", "access control", "oracle manipulation", "call return", "failed call", "price oracle", "withdrawal", "ether withdrawal"],
            prohibited_claim_categories=["guaranteed moon", "investment advice"],
            platform_constraints=PlatformConstraints(max_tweet_chars=280, forbid_hashtags=True),
            mandatory_disclaimers=[],
            quality_thresholds=QualityThresholds(min_factual_support=3, min_technical_correctness=3),
            human_review_requirements=HumanReviewRequirements(require_human_approval_for_ship=False),
        ),
    }

    paths = {}
    for name, policy in profiles.items():
        file_path = policies_dir / f"{name}.json"
        file_path.write_text(policy.model_dump_json(indent=2) + "\n")
        paths[name] = file_path

    return paths
