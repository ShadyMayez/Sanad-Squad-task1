from __future__ import annotations

from typing import Literal
from pydantic import BaseModel, Field, model_validator


class Evidence(BaseModel):
    id: str
    url: str = Field(pattern=r"^https://[^\s]+$")
    excerpt: str = Field(min_length=12)


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
        return self


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

