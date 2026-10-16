from __future__ import annotations

from typing import Literal
from pydantic import BaseModel, Field, model_validator


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


class SemanticReport(BaseModel):
    verdicts: list[SemanticVerdict]


class ModelSemanticDecision(BaseModel):
    """Small local-model contract; claim/source IDs are assigned by Python."""
    verdict: Literal["SUPPORTED", "CONTRADICTED", "INSUFFICIENT_EVIDENCE", "AMBIGUOUS", "VERIFICATION_ERROR"]
    support_option_ids: list[str] = Field(default_factory=list)
    reason: str = Field(min_length=8)
    missing_information: str = ""
    scope_mismatch: str = ""
    confidence: float | None = Field(default=None, ge=0, le=1)


class Slot(BaseModel):
    id: str = Field(pattern=r"^[a-z][a-z0-9_]*$")
    type: str
    focus: str | None = None


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


class SlotResult(BaseModel):
    slot: Slot
    status: Literal["accepted", "dropped", "failed"]
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
    semantic_reports: list[SemanticReport] = Field(default_factory=list)
    verification_latencies_seconds: list[float] = Field(default_factory=list)
    provenance_errors: list[str] = Field(default_factory=list)


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


class ClaimsRecord(BaseModel):
    slot_id: str
    attempts: list[list[AtomicClaim]]


class EvidenceProvenanceRecord(BaseModel):
    slot_id: str
    errors: list[str]
    evidence: list[Evidence]


class SemanticRecord(BaseModel):
    slot_id: str
    attempts: list[SemanticReport]
    latencies_seconds: list[float]


class GroundingSummary(BaseModel):
    slots: int
    atomic_claims_evaluated: int
    verdict_counts: dict[str, int]
    verification_latency_seconds: float
    accepted_claims: int

