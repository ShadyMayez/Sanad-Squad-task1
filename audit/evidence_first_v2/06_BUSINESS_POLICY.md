# Stage 6 / Policy: Lean Business Policy Configuration

**Document ID:** `AUDIT_EVIDENCE_FIRST_V2_06_BUSINESS_POLICY`  
**Date:** October 2026  
**System:** SanadSquad V2 Content Generation Engine  
**Status:** IMPLEMENTED AND QUALIFIED  

---

## 1. Objective and Architectural Intent

SanadSquad must be adaptable to varying organizational risk tolerances, brand personalities, and regulatory postures without introducing heavy enterprise multi-tenant databases, microservices, or complex policy-inheritance engines.

Stage 5 introduces `BusinessPolicy` V1—a lean, versioned, strictly typed configuration contract that separates:
1. **Hard Policy:** Mechanically checkable invariants enforced by Python without model speculation.
2. **Soft Policy:** Brand tone, audience preferences, and stylistic goals interpreted by the Writer and Reviewer models.

---

## 2. BusinessPolicy V1 Specification

The specification is formalized in `content_pipeline/business_policy.py`:

```python
class PlatformConstraints(BaseModel):
    max_tweet_chars: int = 280
    min_tech_thread_tweets: int = 5
    max_tech_thread_tweets: int = 10
    marketing_post_tweets: int = 1
    forbid_hashtags: bool = True

class QualityThresholds(BaseModel):
    min_factual_support: int = 4
    min_technical_correctness: int = 4
    min_clarity: int = 3
    min_brand_voice: int = 3

class HumanReviewRequirements(BaseModel):
    require_human_approval_for_ship: bool = False
    flag_controversial_mechanisms: bool = True

class BusinessPolicy(BaseModel):
    business_id: str
    policy_version: str
    brand_profile: str
    target_audience: str
    content_objectives: list[str]
    approved_source_ids: list[str]
    allowed_topics: list[str]
    prohibited_claim_categories: list[str]
    platform_constraints: PlatformConstraints = Field(default_factory=PlatformConstraints)
    mandatory_disclaimers: list[str] = Field(default_factory=list)
    allowed_content_types: list[str] = ["tech-thread", "marketing-post"]
    quality_thresholds: QualityThresholds = Field(default_factory=QualityThresholds)
    human_review_requirements: HumanReviewRequirements = Field(default_factory=HumanReviewRequirements)
```

---

## 3. Hard Policy vs Soft Policy Separation

### 3.1 Hard Policy Invariants (Deterministic Enforcement)
Enforced via `BusinessPolicy.check_hard_policy_compliance()`:
- **Source Authority:** The evidence used must match `approved_source_ids` (supporting both exact canonical IDs and `SRC_` prefixed IDs). Any unapproved source triggers immediate policy veto.
- **Allowed Topics:** The selected topic must match `allowed_topics`. Unlisted topics fail closed.
- **Allowed Content Types:** Content types must belong to `allowed_content_types`.
- **Platform Constraints:**
  - Technical threads: between 5 and 10 tweets.
  - Marketing posts: exactly 1 tweet.
  - Max tweet length: strictly $\le 280$ characters.
  - Hashtag restrictions: forbidden hashtags trigger immediate failure.
- **Prohibited Claim Categories:** Forbidden marketing superlatives (e.g. "100% secure", "unhackable", "revolutionary", "guaranteed exploit prevention") are checked deterministically and trigger immediate rejection.
- **Mandatory Disclaimers:** Required disclaimers (e.g. "Educational overview only.") must be present in at least one tweet.

### 3.2 Soft Policy (Model Interpretation)
- `brand_profile`: Injected into Writer prompt to shape narrative voice and cadence.
- `target_audience`: Injected into Writer prompt to calibrate technical depth.
- `content_objectives`: Guides the focal message of each unit.

---

## 4. Synthetic Business Profiles

Three distinct synthetic business profiles were constructed and stored in `knowledge/evidence_first_v2/policies/` to validate policy adaptability:

### Profile 1: Security Audit Firm (`security_audit_firm.json`)
- **Business ID:** `sanadsquad_security_audit`
- **Brand Profile:** Authoritative, cautious, deeply technical smart contract auditing firm.
- **Audience:** Protocol founders, lead smart contract engineers, security researchers.
- **Approved Sources:** SWC-107, SWC-104, SWC-113, SWC-105, SCWE-028, OpenZeppelin.
- **Prohibited:** "100% secure", "unhackable", "revolutionary", "zero risk", "guaranteed exploit prevention".
- **Human Approval Required:** False.

### Profile 2: Strict Professional Client (`strict_professional_client.json`)
- **Business ID:** `strict_enterprise_auditing`
- **Brand Profile:** Conservative, institutional enterprise security client.
- **Audience:** C-suite executives, compliance officers, enterprise risk committees.
- **Approved Sources:** Restricted subset (SWC-107, SWC-105, OpenZeppelin Ownable).
- **Mandatory Disclaimer:** "Educational overview only."
- **Prohibited:** "guaranteed", "immediate hack", "massive exploit", "financial loss".
- **Thresholds:** High quality thresholds (5/5 factual, 5/5 technical).
- **Human Approval Required:** True (`require_human_approval_for_ship = true`). Shipped pieces are flagged with `"requires_human_approval": true` in export metadata.

### Profile 3: Creative Technology Brand (`creative_tech_brand.json`)
- **Business ID:** `creative_web3_labs`
- **Brand Profile:** Dynamic, high-energy Web3 developer tooling brand.
- **Audience:** Hackathon developers, EVM builders, DeFi developers.
- **Approved Sources:** Full pilot catalog.
- **Prohibited:** "guaranteed moon", "investment advice".
- **Thresholds:** Standard thresholds (3/5).
- **Human Approval Required:** False.

---

## 5. Policy Change Invalidation Invariant

A content plan, draft, or conformance decision is bound to a specific `policy_version`. When the business policy version changes:
- All cached conformance verdicts referencing prior policy versions are invalidated.
- Unapproved source additions or topic removals fail closed immediately.
- Export records record `business_policy_version` to maintain complete audit traceability.
