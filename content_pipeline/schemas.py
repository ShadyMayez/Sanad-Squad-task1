from __future__ import annotations

from typing import Literal
from pydantic import BaseModel, Field, model_validator

ClaimRelation = Literal["DESCRIPTIVE_FACT", "ROOT_CAUSE", "EXECUTION_MECHANISM", "CONSEQUENCE",
    "MITIGATION_RECOMMENDATION", "MITIGATION_EFFECTIVENESS", "CONDITIONAL_CLAIM", "OTHER"]
EvidenceRelation = Literal["DIRECT_DESCRIPTIVE_SUPPORT", "DIRECT_CAUSAL_SUPPORT", "DIRECT_RECOMMENDATION",
    "DIRECT_EFFECTIVENESS_SUPPORT", "CONTEXTUAL_SUPPORT", "INSUFFICIENT_RELATION",
    "CONTRADICTORY_RELATION", "AMBIGUOUS_RELATION"]
RelationshipVerdict = Literal["ENTAILED", "NOT_ENTAILED", "CONTRADICTED", "AMBIGUOUS"]


class Evidence(BaseModel):
    id: str
    url: str = Field(pattern=r"^https://[^\s]+$")
    excerpt: str = Field(min_length=12)
    source_title: str | None = None
    source_type: str | None = None
    snapshot_path: str | None = None
    snapshot_sha256: str | None = None
    retrieved_at: str | None = None
    source_quote: str | None = None
    quote_start: int | None = None
    quote_end: int | None = None
    scope: str | None = None


class Vulnerability(BaseModel):
    id: str
    name: str
    severity: Literal["low", "medium", "high", "critical"]
    category: str
    description: str
    root_cause: str
    evidence: list[Evidence] = Field(min_length=1)


class KnowledgeBase(BaseModel):
    vulnerabilities: list[Vulnerability] = Field(min_length=15)

    @model_validator(mode="after")
    def unique_ids(self):
        ids = [v.id for v in self.vulnerabilities]
        if len(ids) != len(set(ids)):
            raise ValueError("knowledge-base vulnerability IDs must be unique")
        evidence_ids = [e.id for v in self.vulnerabilities for e in v.evidence]
        if len(evidence_ids) != len(set(evidence_ids)):
            raise ValueError("knowledge-base evidence IDs must be unique")
        return self



class SentenceRelationRecord(BaseModel):
    id: str
    tweet_index: int = Field(ge=0)
    sentence: str
    start: int = Field(ge=0)
    end: int = Field(gt=0)
    connector: str
    premise: str
    conclusion: str
    relation_type: Literal["CAUSAL", "INSTRUMENTAL", "TELEOLOGICAL", "ACTION_RATIONALE", "CONDITIONAL"]
    candidate_evidence_ids: list[str] = Field(default_factory=list)
    direction: str = "premise_to_conclusion"
    quantifiers: list[str] = Field(default_factory=list)
    conditions: list[str] = Field(default_factory=list)
    supporting_spans: list[str] = Field(default_factory=list)
    semantic_verdict: str | None = None
    justification: str | None = None


class AtomicClaim(BaseModel):
    id: str
    tweet_index: int = Field(ge=0)
    start: int = Field(ge=0)
    end: int = Field(gt=0)
    span: str = Field(min_length=1)
    proposition: str = Field(min_length=1)
    sentence: str = Field(min_length=1)
    qualifiers: list[str] = Field(default_factory=list)
    claim_type: Literal["factual", "uncertain"] = "factual"
    candidate_evidence_ids: list[str] = Field(min_length=1)
    relation_hints: list[ClaimRelation] = Field(default_factory=list)
    sentence_relation: SentenceRelationRecord | None = None


class SupportingSpan(BaseModel):
    evidence_id: str
    quote: str = Field(min_length=8)


class EvidenceContext(BaseModel):
    evidence_id: str
    snapshot_sha256: str
    source_scope: str = ""
    start: int = Field(ge=0)
    end: int = Field(gt=0)
    text: str = Field(min_length=8)
    truncated: bool = False
    window_partial: bool | None = None
    token_budget_upper_bound: int = Field(default=1400, gt=0)
    token_upper_bound: int | None = Field(default=None, ge=0)


class VerificationPass(BaseModel):
    verdict: Literal["SUPPORTED", "CONTRADICTED", "INSUFFICIENT_EVIDENCE", "AMBIGUOUS", "VERIFICATION_ERROR"]
    support_option_ids: list[str] = Field(default_factory=list)
    reason: str
    claim_relations: list[ClaimRelation] = Field(default_factory=list)
    evidence_relation: EvidenceRelation | None = None
    relationship_verdict: RelationshipVerdict | None = None
    contradiction_detected: bool | None = None
    uncertainty_detected: bool | None = None
    relation_error: str = ""
    selected_source_roles: dict[str, list[str]] = Field(default_factory=dict)


class SemanticVerdict(BaseModel):
    claim_id: str
    verdict: Literal["SUPPORTED", "CONTRADICTED", "INSUFFICIENT_EVIDENCE", "AMBIGUOUS", "VERIFICATION_ERROR"]
    evidence_ids: list[str] = Field(default_factory=list)
    supporting_spans: list[SupportingSpan] = Field(default_factory=list)
    supporting_span_ids: list[str] = Field(default_factory=list)
    reason: str = Field(min_length=8)
    missing_information: str = ""
    scope_mismatch: str = ""
    confidence: float | None = Field(default=None, ge=0, le=1)
    verification_error: str | None = None
    context_windows: list[EvidenceContext] = Field(default_factory=list)
    proposed_supporting_spans: list[SupportingSpan] = Field(default_factory=list)
    initial_pass: VerificationPass | None = None
    skeptical_pass: VerificationPass | None = None
    claim_relations: list[ClaimRelation] = Field(default_factory=list)
    evidence_relation: EvidenceRelation | None = None
    relationship_verdict: RelationshipVerdict | None = None
    relation_integrity_passed: bool = False
    relation_error: str = ""
    selected_source_roles: dict[str, list[str]] = Field(default_factory=dict)


class SemanticReport(BaseModel):
    verdicts: list[SemanticVerdict]
    sentence_relations: list[SentenceRelationRecord] = Field(default_factory=list)


class ModelSemanticDecision(BaseModel):
    """Small local-model contract; claim/source IDs are assigned by Python."""
    verdict: Literal["SUPPORTED", "CONTRADICTED", "INSUFFICIENT_EVIDENCE", "AMBIGUOUS", "VERIFICATION_ERROR"]
    support_option_ids: list[str] = Field(default_factory=list)
    reason: str = Field(min_length=8)
    missing_information: str = ""
    scope_mismatch: str = ""
    confidence: float | None = Field(default=None, ge=0, le=1)
    claim_relations: list[ClaimRelation] = Field(min_length=1)
    evidence_relation: EvidenceRelation
    relationship_verdict: RelationshipVerdict
    contradiction_detected: bool
    uncertainty_detected: bool
    missing_relation_support: str = ""


class Slot(BaseModel):
    id: str = Field(pattern=r"^[a-z][a-z0-9_]*$")
    type: str
    focus: str | None = None
    service_line: str | None = None
    has_cta: bool = False


class Plan(BaseModel):
    slots: list[Slot] = Field(min_length=1)

    @model_validator(mode="after")
    def valid_slots(self):
        ids = [s.id for s in self.slots]
        if len(ids) != len(set(ids)):
            raise ValueError("plan slot IDs must be unique")
        return self


class Claim(BaseModel):
    text: str = Field(min_length=5)
    evidence_ids: list[str] = Field(min_length=1)


class Draft(BaseModel):
    tweets: list[str] = Field(min_length=1)
    claims: list[Claim] = Field(default_factory=list)


class MarketingDraft(Draft):
    tweets: list[str] = Field(
        min_length=1,
        max_length=1,
        description="Exactly one marketing post tweet (multiple sentences inside this single tweet are permitted, strictly under 280 characters).",
    )
    mandatory_link: str | None = Field(
        default=None,
        description="When the task specifies a required source URL, you MUST repeat that exact URL in this field as an explicit structured constraint.",
    )

    @model_validator(mode="after")
    def _ensure_mandatory_link_in_tweet(self) -> MarketingDraft:
        if self.mandatory_link:
            link = self.mandatory_link.strip()
            if self.tweets and link and link not in self.tweets[0]:
                candidate = f"{self.tweets[0].rstrip()} {link}"
                if len(candidate) <= 280:
                    self.tweets[0] = candidate
                    for c in self.claims:
                        if c.text in candidate:
                            c.text = candidate
        return self


class MarketingDraftWithLink(MarketingDraft):
    mandatory_link: str = Field(
        ...,
        description="MANDATORY: You MUST provide the exact authorized source URL specified in the prompt as a structured constraint.",
    )

    @model_validator(mode="after")
    def _validate_mandatory_link_present(self) -> MarketingDraftWithLink:
        link = self.mandatory_link.strip() if self.mandatory_link else ""
        if not link:
            raise ValueError("mandatory_link must not be empty")
        if not self.tweets or link not in self.tweets[0]:
            candidate = f"{self.tweets[0].rstrip()} {link}" if self.tweets else link
            if len(candidate) <= 280:
                self.tweets[0] = candidate
            else:
                raise ValueError(
                    f"Draft tweet must contain the mandatory link: '{link}', but incorporating it exceeds 280 characters ({len(candidate)} chars)."
                )
        return self


class TechThreadDraft(Draft):
    tweets: list[str] = Field(
        min_length=5,
        max_length=10,
        description="Five to ten ordered technical thread tweets, each strictly under 280 characters.",
    )


class ClaimSupport(BaseModel):
    claim_text: str
    evidence_id: str
    evidence_quote: str
    supported: bool


class Review(BaseModel):
    factual_support: int = Field(ge=0, le=5)
    technical_correctness: int = Field(ge=0, le=5)
    brand_voice: int = Field(ge=0, le=5)
    clarity: int = Field(ge=0, le=5)
    platform_format: int = Field(ge=0, le=5)
    usefulness: int = Field(ge=0, le=5)
    approved: bool
    reasons: list[str] = Field(default_factory=list)
    corrections: list[str] = Field(default_factory=list)
    grounding_assessment: str
    claim_support: list[ClaimSupport] = Field(default_factory=list)


class WriterConfig(BaseModel):
    instruction_file: str
    min_tweets: int = 1
    max_tweets: int = 1
    max_chars: int = 280
    require_review_invitation: bool = False


class Registry(BaseModel):
    types: dict[str, WriterConfig]


class BrandRules(BaseModel):
    banned_words: list[str]
    banned_characters: list[str]
    forbid_hashtags: bool
    allowed_links: list[str]
    approved_statistics: list[str]


class HumanApprovalRecord(BaseModel):
    approver_id: str
    approver_role: str
    approved_at: str
    approved_draft_hash: str
    policy_id: str
    policy_version: str
    approval_witness: str
    notes: str = ""

    @property
    def witness_signature(self) -> str:
        return self.approval_witness

    @classmethod
    def create(
        cls,
        approver_id: str,
        approver_role: str,
        draft_text: str,
        policy_id: str,
        policy_version: str,
        notes: str = "",
    ) -> "HumanApprovalRecord":
        import hashlib
        from datetime import datetime, timezone
        draft_hash = hashlib.sha256(draft_text.encode("utf-8")).hexdigest()
        now_iso = datetime.now(timezone.utc).isoformat()
        payload = f"{approver_id}:{approver_role}:{now_iso}:{draft_hash}:{policy_id}:{policy_version}"
        witness = hashlib.sha256(payload.encode("utf-8")).hexdigest()
        return cls(
            approver_id=approver_id,
            approver_role=approver_role,
            approved_at=now_iso,
            approved_draft_hash=draft_hash,
            policy_id=policy_id,
            policy_version=policy_version,
            approval_witness=witness,
            notes=notes,
        )

    def verify(self, draft_text: str, expected_policy_id: str, expected_policy_version: str) -> tuple[bool, str]:
        import hashlib
        draft_hash = hashlib.sha256(draft_text.encode("utf-8")).hexdigest()
        if self.approved_draft_hash != draft_hash:
            return False, f"Draft hash mismatch: approved {self.approved_draft_hash[:12]}... != current {draft_hash[:12]}..."
        if self.policy_id != expected_policy_id:
            return False, f"Policy ID mismatch: approved {self.policy_id!r} != expected {expected_policy_id!r}"
        if self.policy_version != expected_policy_version:
            return False, f"Policy version mismatch: approved {self.policy_version!r} != expected {expected_policy_version!r}"
        payload = f"{self.approver_id}:{self.approver_role}:{self.approved_at}:{self.approved_draft_hash}:{self.policy_id}:{self.policy_version}"
        expected_witness = hashlib.sha256(payload.encode("utf-8")).hexdigest()
        if self.approval_witness != expected_witness:
            return False, "Approval witness signature invalid"
        return True, "Valid"


class SlotResult(BaseModel):
    slot: Slot
    status: Literal["accepted", "dropped", "failed"]
    has_cta: bool = False
    topic: str | None = None
    source_ids: list[str] = Field(default_factory=list)
    evidence: list[Evidence] = Field(default_factory=list)
    drafts: list[Draft] = Field(default_factory=list)
    validations: list[list[str]] = Field(default_factory=list)
    reviews: list[Review] = Field(default_factory=list)
    reason: str | None = None
    visual_spec: str | None = None
    prompt_tokens: int | None = None
    completion_tokens: int | None = None
    usage_measurements_complete: bool = True
    atomic_claims: list[list[AtomicClaim]] = Field(default_factory=list)
    sentence_relations: list[list[SentenceRelationRecord]] = Field(default_factory=list)
    semantic_reports: list[SemanticReport] = Field(default_factory=list)
    verification_latencies_seconds: list[float] = Field(default_factory=list)
    provenance_errors: list[str] = Field(default_factory=list)
    conformance_report: dict | None = None
    evidence_plan: dict | None = None
    human_approval_required: bool = False
    human_approved: bool | None = None
    human_approval_witness: dict | str | None = None
    human_approval_record: HumanApprovalRecord | None = None
    authorization_mode: str = "pilot_evaluation"
    publication_status: str = "SHIPPED"
    business_policy_version: str | None = None
    pipeline_mode: str = "legacy"
    fetched_urls: list[str] = Field(default_factory=list)
    writing_quality_report: dict | None = None
    source_strategy: str | None = None


class ResearchRecord(BaseModel):
    slot_id: str
    topic: str | None = None
    source_ids: list[str]
    evidence: list[Evidence]
    status: Literal["accepted", "dropped", "failed"]
    reason: str | None = None


class ValidationRecord(BaseModel):
    slot_id: str
    attempts: list[list[str]]


class ReviewRecord(BaseModel):
    slot_id: str
    attempts: list[Review]


class FailureRecord(BaseModel):
    slot_id: str
    status: Literal["dropped", "failed"]
    reason: str | None = None


class AcceptedRecord(SlotResult):
    status: Literal["accepted"]
    image_spec_reference: str


class Summary(BaseModel):
    model: str
    planned: int
    shipped: int
    ready_for_human_review: int = 0
    dropped: int
    failed: int
    reasons: list[FailureRecord]
    elapsed_seconds: float
    prompt_tokens_recorded: int | None
    completion_tokens_recorded: int | None
    usage_complete: bool
    peak_simultaneous_ollama_calls: int
    external_model_api_charges_usd: float
    local_inference_cost: str
    pipeline_mode: str = "legacy"


class ClaimsRecord(BaseModel):
    slot_id: str
    attempts: list[list[AtomicClaim]]


class EvidenceProvenanceRecord(BaseModel):
    slot_id: str
    errors: list[str]
    evidence: list[Evidence]


class SemanticRecord(BaseModel):
    schema_version: Literal["2.0"] | None = None
    slot_id: str
    attempts: list[SemanticReport]
    latencies_seconds: list[float]


class GroundingSummary(BaseModel):
    slots: int
    atomic_claims_evaluated: int
    verdict_counts: dict[str, int]
    verification_latency_seconds: float
    accepted_claims: int

