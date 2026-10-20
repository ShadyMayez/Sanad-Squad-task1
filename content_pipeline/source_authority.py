"""Typed source-authority contracts and separation boundaries.

Enforces strict source separation in code:
- Technical threads choose per-piece:
    * Strategy 1: Knowledge base (kb.json) entries cited by ID.
    * Strategy 2: External technical research resource cited by URL with resource brief.
- Marketing posts use current, allowlisted external web research.
    * Barred from kb.json and proposition catalog by default.
    * Vulnerability class exception may cite kb.json strictly as supplemental support,
      never replacing current web research.
"""
from __future__ import annotations

from enum import Enum
from typing import Literal
from pydantic import BaseModel, Field
from .schemas import Evidence, Vulnerability


class TechnicalSourceStrategy(str, Enum):
    KNOWLEDGE_BASE = "knowledge_base"
    EXTERNAL_RESEARCH = "external_research"


class MarketingSourceStrategy(str, Enum):
    CURRENT_WEB_RESEARCH = "current_web_research"
    VULNERABILITY_CLASS_EXCEPTION = "vulnerability_class_exception"


class SourceAuthorityViolationError(PermissionError):
    """Raised when an agent or slot accesses an unauthorized source pathway."""
    pass


class TechnicalResourceBrief(BaseModel):
    title: str
    url: str
    publisher: str
    retrieval_timestamp: str
    summary_brief: str
    key_findings: list[str] = Field(default_factory=list)
    sha256_checksum: str


class SourceAuthorityContext(BaseModel):
    slot_id: str
    content_type: Literal["tech-thread", "marketing-post"]
    service_line: str | None = None
    technical_strategy: TechnicalSourceStrategy | None = None
    marketing_strategy: MarketingSourceStrategy | None = None
    allowed_kb_access: bool = False
    vulnerability_class_supplemental: bool = False
    allowed_domains: list[str] = Field(default_factory=list)
    resource_brief: TechnicalResourceBrief | None = None

    @classmethod
    def for_technical_slot(
        cls,
        slot_id: str,
        strategy: TechnicalSourceStrategy = TechnicalSourceStrategy.KNOWLEDGE_BASE,
        resource_brief: TechnicalResourceBrief | None = None,
    ) -> SourceAuthorityContext:
        """Create authorized source context for technical threads."""
        return cls(
            slot_id=slot_id,
            content_type="tech-thread",
            service_line="web3-security",
            technical_strategy=strategy,
            allowed_kb_access=(strategy == TechnicalSourceStrategy.KNOWLEDGE_BASE),
            resource_brief=resource_brief,
        )

    @classmethod
    def for_marketing_slot(
        cls,
        slot_id: str,
        service_line: str,
        allowed_domains: list[str],
        is_vulnerability_class_exception: bool = False,
    ) -> SourceAuthorityContext:
        """Create authorized source context for marketing posts."""
        strategy = (
            MarketingSourceStrategy.VULNERABILITY_CLASS_EXCEPTION
            if is_vulnerability_class_exception
            else MarketingSourceStrategy.CURRENT_WEB_RESEARCH
        )
        return cls(
            slot_id=slot_id,
            content_type="marketing-post",
            service_line=service_line,
            marketing_strategy=strategy,
            allowed_kb_access=is_vulnerability_class_exception,
            vulnerability_class_supplemental=is_vulnerability_class_exception,
            allowed_domains=allowed_domains,
        )

    def assert_kb_read_allowed(self) -> None:
        """Enforce in code that kb.json access is authorized for this slot context."""
        if not self.allowed_kb_access:
            raise SourceAuthorityViolationError(
                f"Unauthorized KB access: Slot {self.slot_id} ({self.content_type}) "
                f"with strategy {self.marketing_strategy or self.technical_strategy} "
                "is strictly barred from accessing the vulnerability catalog or kb.json."
            )

    def assert_external_domain_allowed(self, domain: str) -> None:
        """Enforce that external domain is allowlisted for this service line."""
        norm_domain = domain.lower().strip()
        matched = any(
            norm_domain == allowed or norm_domain.endswith("." + allowed)
            for allowed in self.allowed_domains
        )
        if not matched:
            raise SourceAuthorityViolationError(
                f"Unauthorized external domain '{domain}' for service line '{self.service_line}'. "
                f"Slot {self.slot_id} can only query within: {self.allowed_domains}"
            )


def filter_authorized_evidence(
    context: SourceAuthorityContext,
    evidence_list: list[Evidence],
    supplemental_kb: list[Vulnerability] | None = None,
) -> list[Evidence]:
    """Return only evidence items that comply with the slot's typed source authority."""
    if context.content_type == "marketing-post":
        # Marketing posts require web research evidence.
        # If vulnerability-class exception is active, supplemental KB evidence is allowed,
        # but web research evidence MUST be present.
        web_evidence = [e for e in evidence_list if getattr(e, "source_type", "") != "knowledge_base"]
        if not web_evidence:
            raise SourceAuthorityViolationError(
                f"Marketing slot {context.slot_id} must contain primary web research evidence. "
                "KB entries can only serve as supplemental evidence, never as a substitute."
            )
        if context.vulnerability_class_supplemental and supplemental_kb:
            kb_ev = [e for v in supplemental_kb for e in v.evidence]
            return web_evidence + kb_ev
        return web_evidence

    # Technical threads
    if context.technical_strategy == TechnicalSourceStrategy.KNOWLEDGE_BASE:
        return evidence_list
    elif context.technical_strategy == TechnicalSourceStrategy.EXTERNAL_RESEARCH:
        # External technical evidence
        return [e for e in evidence_list if getattr(e, "source_type", "") != "knowledge_base"]

    return evidence_list
