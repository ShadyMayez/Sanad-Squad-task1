"""Weekly marketing planner and diversity constraint validation.

Directive: SANADSQUAD_V3_OFFICIAL_BRAND_INTEGRATION_01

Maps the 5 official SanadSquad commercial services:
1. Blockchain security audits (blockchain-security-audits)
2. Penetration testing (penetration-testing)
3. Agentic security tooling (agentic-security-tooling)
4. Agentic payments (agentic-payments)
5. Security consulting (security-consulting)

to the 4 canonical research categories:
- web3-security
- pentesting
- agentic-security
- agentic-payments
"""
from __future__ import annotations

import re
import threading
from typing import Any
from pydantic import BaseModel, Field, model_validator
from .marketing_format import MarketingFormat, FORMAT_SPECS
from .marketing_policy import detect_commercial_cta
from .schemas import Slot, SlotResult

# Five official commercial services advertised on sanadsquad.com
OFFICIAL_COMMERCIAL_SERVICES = [
    "blockchain-security-audits",
    "penetration-testing",
    "agentic-security-tooling",
    "agentic-payments",
    "security-consulting",
]

# Canonical mapping from 5 commercial services (and legacy aliases) to 4 research categories
COMMERCIAL_TO_RESEARCH_TAXONOMY: dict[str, str] = {
    "blockchain-security-audits": "web3-security",
    "penetration-testing": "pentesting",
    "agentic-security-tooling": "agentic-security",
    "agentic-payments": "agentic-payments",
    "security-consulting": "web3-security",
    # Legacy aliases
    "web3-security": "web3-security",
    "pentesting": "pentesting",
    "agentic-security": "agentic-security",
    "consulting": "web3-security",
}

# Reverse mapping from research categories to primary commercial services
RESEARCH_TAXONOMY_TO_COMMERCIAL: dict[str, str] = {
    "web3-security": "blockchain-security-audits",
    "pentesting": "penetration-testing",
    "agentic-security": "agentic-security-tooling",
    "agentic-payments": "agentic-payments",
}


def normalize_commercial_service(service_or_alias: str) -> str:
    """Normalize any service line or alias to the official commercial service name."""
    s = service_or_alias.lower().strip()
    s_hyphen = s.replace(" ", "-")
    if s in OFFICIAL_COMMERCIAL_SERVICES:
        return s
    if s_hyphen in OFFICIAL_COMMERCIAL_SERVICES:
        return s_hyphen
    if s in ("web3-security", "web3", "smart-contract-audits", "audit", "blockchain security audits"):
        return "blockchain-security-audits"
    if s in ("pentesting", "pentest", "web2-pentesting", "web2", "penetration testing"):
        return "penetration-testing"
    if s in ("agentic-security", "tooling", "ai-security-tooling", "ai-tooling", "agentic security tooling", "agentic tooling"):
        return "agentic-security-tooling"
    if s in ("agentic-payments", "payments", "x402", "mpp", "agentic payments"):
        return "agentic-payments"
    if s in ("security-consulting", "consulting", "architecture-review", "security consulting"):
        return "security-consulting"
    return s



def map_service_to_research_category(service: str) -> str:
    """Map commercial service to the 4 canonical research categories."""
    norm = normalize_commercial_service(service)
    return COMMERCIAL_TO_RESEARCH_TAXONOMY.get(norm, "web3-security")


class MarketingSlotMetadata(BaseModel):
    slot_id: str
    commercial_service: str | None = None
    service_line: str = "blockchain-security-audits"
    research_category: str | None = None
    research_angle: str
    selected_format: MarketingFormat
    requires_link: bool
    forbids_link: bool
    has_cta: bool
    topic_fingerprint: str
    source_freshness_status: str = "fresh"
    evidence_references: list[str] = Field(default_factory=list)

    @model_validator(mode="after")
    def _sync_service_fields(self) -> MarketingSlotMetadata:
        if not self.commercial_service:
            self.commercial_service = normalize_commercial_service(self.service_line)
        if not self.research_category:
            self.research_category = map_service_to_research_category(self.commercial_service)
        return self


class WeeklyMarketingPlan(BaseModel):
    slots: list[MarketingSlotMetadata]

    def validate_constraints(self) -> list[str]:
        """Validate weekly diversity and balance constraints across marketing slots."""
        errors: list[str] = []
        if not self.slots:
            return errors

        n_slots = len(self.slots)

        # 1. Commercial service diversity (no duplicate commercial services in plan)
        norm_services = [normalize_commercial_service(s.commercial_service or s.service_line) for s in self.slots]
        if len(norm_services) != len(set(norm_services)):
            duplicates = [sl for sl in norm_services if norm_services.count(sl) > 1]
            errors.append(f"Weekly mix violation: duplicate service lines in plan: {set(duplicates)}")

        # 2. Format diversity (no format appearing more than twice)
        formats = [s.selected_format for s in self.slots]
        for fmt in set(formats):
            if formats.count(fmt) > 2:
                errors.append(f"Weekly mix violation: format '{fmt.value}' appears {formats.count(fmt)} times (max 2).")

        # 3. Link requirements: at least 1 with link, at least 1 without link
        link_counts = sum(1 for s in self.slots if s.requires_link)
        no_link_counts = sum(1 for s in self.slots if not s.requires_link)
        if link_counts < 1:
            errors.append("Weekly mix violation: at least 1 marketing post must require a source link.")
        if no_link_counts < 1:
            errors.append("Weekly mix violation: at least 1 marketing post must have no link.")

        # 4. CTA limits: Maximum one CTA across three weekly marketing posts (and <= 1/3 of posts)
        cta_counts = sum(1 for s in self.slots if s.has_cta)
        max_ctas = 1 if n_slots <= 3 else max(1, n_slots // 3)
        if cta_counts > max_ctas:
            errors.append(
                f"Weekly mix violation: {cta_counts} marketing posts contain CTAs (max allowed is {max_ctas} for {n_slots} posts)."
            )

        # 5. Topic similarity fingerprinting
        fingerprints = [s.topic_fingerprint for s in self.slots]
        if len(fingerprints) != len(set(fingerprints)):
            errors.append("Weekly mix violation: duplicate topic fingerprints detected among marketing slots.")

        return errors


def compute_topic_fingerprint(text: str) -> str:
    """Compute normalized token fingerprint for topic deduplication."""
    tokens = re.findall(r"\b[a-z]{3,}\b", text.lower())
    stop_words = {"the", "and", "for", "with", "this", "that", "from", "are", "can"}
    meaningful = sorted(list(set(t for t in tokens if t not in stop_words)))
    return "_".join(meaningful[:6]) or "general_topic"


class MarketingSlotPlanner:
    """Thread-safe global planner for assigning diverse, non-colliding marketing slots."""

    _lock = threading.Lock()

    @classmethod
    def plan_weekly_slots(
        cls,
        slots: list[Slot],
    ) -> WeeklyMarketingPlan:
        """Create a coordinated weekly marketing plan for marketing-post slots."""
        with cls._lock:
            marketing_slots = [s for s in slots if s.type == "marketing-post"]
            planned_meta: list[MarketingSlotMetadata] = []

            # Canonical default rotation across official services for up to 5 marketing slots
            service_rotation = [
                ("blockchain-security-audits", "post-audit deployment drift and invariant testing", MarketingFormat.DIFFERENTIATION, False, False),
                ("agentic-security-tooling", "AI agent prompt injection and custom PR reviewer detectors", MarketingFormat.NEWS_REACTION, True, False),
                ("agentic-payments", "x402 versus MPP settlement mechanics and facilitator trust", MarketingFormat.LEARNING_RESOURCE, True, True),
                ("penetration-testing", "API security and CI/CD pipeline infrastructure attack surface", MarketingFormat.NEWS_REACTION, True, False),
                ("security-consulting", "Pre-implementation architecture design and security by default", MarketingFormat.SHORT_TIP, False, False),
            ]

            from .contact_config import load_company_contact
            contact_cfg = load_company_contact()
            contact_approved = bool(contact_cfg and contact_cfg.is_operational() and contact_cfg.approved)

            # Track assigned services to prevent duplicates
            assigned_services: set[str] = set()

            for idx, slot in enumerate(marketing_slots):
                if idx < len(service_rotation):
                    c_service, angle, fmt, req_link, has_cta = service_rotation[idx]
                else:
                    c_service, angle, fmt, req_link, has_cta = service_rotation[idx % len(service_rotation)]

                # If slot has explicit focus, deduce commercial service
                if slot.focus:
                    angle = slot.focus
                    focus_lower = slot.focus.lower()
                    if "consult" in focus_lower or "design review" in focus_lower or "architecture before code" in focus_lower:
                        c_service = "security-consulting"
                    elif "tool" in focus_lower or "detector" in focus_lower or "pr reviewer" in focus_lower or "monitoring agent" in focus_lower:
                        c_service = "agentic-security-tooling"
                    elif "pentest" in focus_lower or "cloud" in focus_lower or "api" in focus_lower or "infra" in focus_lower or "cicd" in focus_lower or "pipeline" in focus_lower:
                        c_service = "penetration-testing"
                    elif "agent" in focus_lower and "pay" in focus_lower:
                        c_service = "agentic-payments"
                    elif "agent" in focus_lower or "prompt" in focus_lower or "llm" in focus_lower:
                        c_service = "agentic-security-tooling"
                    elif "contract" in focus_lower or "reentrancy" in focus_lower or "access" in focus_lower or "web3" in focus_lower or "defi" in focus_lower or "invariant" in focus_lower or "audit" in focus_lower:
                        c_service = "blockchain-security-audits"

                # Check if explicit service_line is requested on slot
                if hasattr(slot, "service_line") and slot.service_line:
                    c_service = normalize_commercial_service(slot.service_line)

                # Ensure non-colliding service selection if default collides
                if c_service in assigned_services:
                    for fallback_service, f_angle, f_fmt, f_req_link, f_has_cta in service_rotation:
                        if fallback_service not in assigned_services:
                            c_service = fallback_service
                            angle = f_angle
                            fmt = f_fmt
                            req_link = f_req_link
                            break

                assigned_services.add(c_service)

                # Fail-closed: Never plan commercial contact CTA if contact approval is missing
                if not contact_approved:
                    has_cta = False

                spec = FORMAT_SPECS[fmt]
                fp = compute_topic_fingerprint(f"{c_service} {angle}")
                res_cat = map_service_to_research_category(c_service)

                meta = MarketingSlotMetadata(
                    slot_id=slot.id,
                    commercial_service=c_service,
                    service_line=c_service,
                    research_category=res_cat,
                    research_angle=angle,
                    selected_format=fmt,
                    requires_link=spec.requires_link,
                    forbids_link=spec.forbids_link,
                    has_cta=has_cta,
                    topic_fingerprint=fp,
                )
                planned_meta.append(meta)

            plan = WeeklyMarketingPlan(slots=planned_meta)
            errors = plan.validate_constraints()
            if errors:
                raise ValueError(f"Failed to generate compliant weekly marketing plan: {errors}")
            return plan


def validate_weekly_marketing_results(results: list[SlotResult]) -> list[str]:
    """Validate weekly constraints across final accepted marketing results."""
    marketing_results = [r for r in results if r.slot.type == "marketing-post" and r.status == "accepted"]
    if not marketing_results:
        return []

    errors: list[str] = []
    service_lines = []
    links_present = 0
    no_links_present = 0
    cta_count = 0

    for r in marketing_results:
        if not r.drafts:
            continue
        text = " ".join(r.drafts[-1].tweets)
        has_cta, count, _ = detect_commercial_cta(text)
        from .contact_config import EMAIL_PATTERN
        has_contact = bool(EMAIL_PATTERN.search(text) or "phone:" in text.lower())
        if has_cta or has_contact:
            cta_count += 1

        # Service line from slot or result
        sl = getattr(r.slot, "service_line", None) or getattr(r, "service_line", None)
        if not sl and r.evidence:
            for ev in r.evidence:
                if ev.scope and "service_line:" in ev.scope:
                    sl = ev.scope.split("service_line:")[1].strip()
                    break
        if sl:
            norm_sl = normalize_commercial_service(sl)
            service_lines.append(norm_sl)

        links = re.findall(r"https?://[^\s)]+", text)
        if links:
            links_present += 1
        else:
            no_links_present += 1

    # Check service line duplicates (normalized)
    if len(service_lines) != len(set(service_lines)):
        errors.append(f"Weekly accepted marketing results contain duplicate service lines: {service_lines}")

    # Check links
    if len(marketing_results) >= 2:
        if links_present < 1:
            errors.append("Weekly accepted marketing results must include at least 1 post with a source link.")
        if no_links_present < 1:
            errors.append("Weekly accepted marketing results must include at least 1 post with no link.")

    # Check CTAs (maximum one CTA across three weekly marketing posts)
    max_ctas = 1 if len(marketing_results) <= 3 else max(1, len(marketing_results) // 3)
    if cta_count > max_ctas:
        errors.append(
            f"Weekly accepted marketing results contain {cta_count} posts with CTAs "
            f"(maximum allowed is {max_ctas} across {len(marketing_results)} posts)."
        )

    return errors
