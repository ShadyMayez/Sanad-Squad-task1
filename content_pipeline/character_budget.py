"""Exact URL-inclusive character budgeting and replanning for marketing posts.

Directive: SANADSQUAD_V3_MARKETING_YIELD_PERFORMANCE_CLOSURE_01

Pre-calculates exact character budgets before generation:
- Platform limit: 280 characters
- Mandatory source URL (when required)
- Approved contextual CTA (when authorized)
- Required spacing and punctuation
- Safety margin against model variance (20 chars)

If a source URL or format renders the post impractical (< 110 chars for body prose),
replanning chooses a shorter allowlisted canonical URL or a format that does not
mandate a URL (e.g. differentiation or short-tip), never inventing fake shortened URLs.
"""
from __future__ import annotations

from typing import Any
from pydantic import BaseModel, Field


class CharacterBudget(BaseModel):
    max_total_chars: int = 280
    mandatory_url: str | None = None
    url_chars: int = 0
    approved_cta: str | None = None
    cta_chars: int = 0
    spacing_chars: int = 0
    safety_margin_chars: int = 20
    max_body_chars: int = 260
    target_body_chars_min: int = 140
    target_body_chars_max: int = 220
    is_practical: bool = True
    rejection_reason: str | None = None

    def budget_instruction(self) -> str:
        """Produce precise prompt guidance for the Writer."""
        parts = [
            f"EXACT PRE-CALCULATED CHARACTER BUDGET (Platform Limit: {self.max_total_chars} chars):"
        ]
        if self.mandatory_url:
            parts.append(
                f"- Mandatory Source URL: '{self.mandatory_url}' ({self.url_chars} chars + 1 space)"
            )
        else:
            parts.append("- Source URL: None required for this format.")

        if self.approved_cta:
            parts.append(
                f"- Approved Contact CTA: '{self.approved_cta}' ({self.cta_chars} chars + 1 space)"
            )
        else:
            parts.append("- Commercial CTA: None permitted.")

        parts.append(f"- Safety Margin: {self.safety_margin_chars} chars (protection against model length variance)")
        parts.append(
            f"- MAXIMUM ALLOWED BODY PROSE: {self.max_body_chars} characters! (Target: {self.target_body_chars_min}-{self.target_body_chars_max} chars)"
        )
        parts.append(
            f"CRITICAL: Your body copy MUST NOT exceed {self.max_body_chars} characters so the total tweet stays strictly under {self.max_total_chars} characters."
        )
        return "\n".join(parts)


def compute_character_budget(
    mandatory_url: str | None = None,
    approved_cta: str | None = None,
    safety_margin: int = 20,
    max_total: int = 280,
    min_viable_body: int = 110,
) -> CharacterBudget:
    """Compute exact pre-generation character budget."""
    clean_url = mandatory_url.strip() if mandatory_url else None
    url_len = len(clean_url) if clean_url else 0

    clean_cta = approved_cta.strip() if approved_cta else None
    cta_len = len(clean_cta) if clean_cta else 0

    spacing = 0
    if url_len > 0:
        spacing += 1
    if cta_len > 0:
        spacing += 1

    fixed_overhead = url_len + cta_len + spacing
    effective_margin = max(safety_margin, 60) if fixed_overhead == 0 else safety_margin
    max_body = max_total - fixed_overhead - effective_margin

    is_practical = (max_body >= min_viable_body)
    rejection_reason = None
    if not is_practical:
        rejection_reason = (
            f"Impractical character budget: fixed overhead is {fixed_overhead} chars "
            f"(URL: {url_len}, CTA: {cta_len}, Spacing: {spacing}), leaving only "
            f"{max_body} chars for body prose (minimum viable is {min_viable_body})."
        )

    target_max = max(min_viable_body, max_body)
    target_min = max(70, target_max - 50)

    return CharacterBudget(
        max_total_chars=max_total,
        mandatory_url=clean_url,
        url_chars=url_len,
        approved_cta=clean_cta,
        cta_chars=cta_len,
        spacing_chars=spacing,
        safety_margin_chars=safety_margin,
        max_body_chars=max_body,
        target_body_chars_min=target_min,
        target_body_chars_max=target_max,
        is_practical=is_practical,
        rejection_reason=rejection_reason,
    )


def replan_marketing_slot_for_budget(
    service_line: str,
    format_name: str,
    evidence_items: list[Any],
    approved_cta: str | None = None,
    safety_margin: int = 20,
) -> tuple[str, str | None, CharacterBudget, list[str]]:
    """Inspect proposed format and URLs; replan if budget is impractical.

    Returns (final_format, final_url, budget, replan_notes).
    """
    from .marketing_format import MarketingFormat, FORMAT_SPECS

    replan_notes: list[str] = []
    fmt_enum = MarketingFormat(format_name) if isinstance(format_name, str) else format_name
    spec = FORMAT_SPECS.get(fmt_enum)
    requires_link = spec.requires_link if spec else False

    # 1. Evaluate primary URL
    primary_url = None
    if requires_link and evidence_items:
        first_ev = evidence_items[0]
        primary_url = getattr(first_ev, "url", None) if hasattr(first_ev, "url") else first_ev.get("url")

    budget = compute_character_budget(
        mandatory_url=primary_url,
        approved_cta=approved_cta,
        safety_margin=safety_margin,
    )

    if budget.is_practical:
        return (fmt_enum.value, primary_url, budget, replan_notes)

    # 2. Replan Option A: Search for alternative shorter valid URL among evidence items
    if requires_link and len(evidence_items) > 1:
        for alt_ev in evidence_items[1:]:
            alt_url = getattr(alt_ev, "url", None) if hasattr(alt_ev, "url") else alt_ev.get("url")
            if alt_url and len(alt_url) < len(primary_url or ""):
                alt_budget = compute_character_budget(
                    mandatory_url=alt_url,
                    approved_cta=approved_cta,
                    safety_margin=safety_margin,
                )
                if alt_budget.is_practical:
                    replan_notes.append(
                        f"Replanned URL: Replaced long URL ({len(primary_url)} chars) with shorter verified URL "
                        f"'{alt_url}' ({len(alt_url)} chars) to preserve {fmt_enum.value} format."
                    )
                    return (fmt_enum.value, alt_url, alt_budget, replan_notes)

    # 3. Replan Option B: If CTA makes it impractical, drop CTA first before dropping link
    if approved_cta is not None:
        budget_no_cta = compute_character_budget(
            mandatory_url=primary_url,
            approved_cta=None,
            safety_margin=safety_margin,
        )
        if budget_no_cta.is_practical:
            replan_notes.append(
                f"Replanned CTA: Suppressed CTA ({len(approved_cta)} chars) to prioritize mandatory source URL "
                f"for {fmt_enum.value} format."
            )
            return (fmt_enum.value, primary_url, budget_no_cta, replan_notes)

    # 4. Replan Option C: If URL still makes format impractical, switch format to differentiation or short-tip
    # (formats that do not mandate links)
    fallback_fmt = MarketingFormat.DIFFERENTIATION if service_line in {"blockchain-security-audits", "penetration-testing"} else MarketingFormat.SHORT_TIP
    replan_notes.append(
        f"Replanned Format: Format '{fmt_enum.value}' with URL '{primary_url}' was impractical "
        f"({budget.rejection_reason}). Switched to '{fallback_fmt.value}' without mandatory URL to produce meaningful text."
    )
    fallback_budget = compute_character_budget(
        mandatory_url=None,
        approved_cta=approved_cta,
        safety_margin=safety_margin,
    )
    return (fallback_fmt.value, None, fallback_budget, replan_notes)


def build_precise_marketing_feedback(
    draft: Any,
    plan: Any,
    validation_errors: list[str],
    review_reasons: list[str] | None = None,
) -> list[dict[str, Any]]:
    """Build exact, actionable revision feedback for a marketing post draft.

    Directive Section 3 Requirements:
    - Exact number of excess characters.
    - Exact missing URL.
    - Required factual points.
    - Optional wording to remove.
    - Format-specific missing content.
    - Never general instructions like 'make it better'.
    """
    tweet_text = draft.tweets[0] if draft and hasattr(draft, "tweets") and draft.tweets else ""
    current_len = len(tweet_text)

    budget_dict = getattr(plan, "character_budget", {}) or {}
    max_body = budget_dict.get("max_body_chars", 180)
    mand_url = getattr(plan, "mandatory_url", None) or budget_dict.get("mandatory_url")

    # 1. Excess characters calculation
    excess_chars = max(0, current_len - 280)

    # 2. Missing URL check
    url_in_text = bool(mand_url and mand_url in tweet_text)
    missing_url = mand_url if (mand_url and not url_in_text) else None

    # 3. Format-specific missing items
    format_missing: list[str] = []
    forbidden_url_found = False
    for err in validation_errors:
        err_lower = err.lower()
        if "requires an authorized source link" in err_lower or "mandates link" in err_lower:
            format_missing.append(f"Format requires the verified source link: '{mand_url}'")
        elif "must not contain any links" in err_lower or "forbids links" in err_lower:
            forbidden_url_found = True
            format_missing.append("Format strictly forbids links. Remove all URLs from your tweet.")
        elif "news reaction format" in err_lower or "event marker" in err_lower:
            format_missing.append("Include an identifiable news/advisory event marker and source attribution.")
        elif "at most" in err_lower and "sentences" in err_lower:
            format_missing.append(err)
        elif "exceeds 280 character" in err_lower:
            pass
        elif "commercial cta" in err_lower or "contact" in err_lower:
            format_missing.append(err)
        elif "action" in err_lower or "recommendation" in err_lower:
            format_missing.append(err)

    # 4. Optional wording to remove (identify filler words or verbose patterns)
    words_to_remove: list[str] = []
    lower_text = tweet_text.lower()
    fillers = [
        ("excited to share", "Remove promotional filler 'excited to share'"),
        ("take a look", "Remove introductory filler 'take a look'"),
        ("check out", "Remove informal filler 'check out'"),
        ("in this post", "Remove self-referential filler 'in this post'"),
        ("it is important to note that", "Replace 'it is important to note that' with concise direct phrasing"),
        ("security teams must always remember", "Shorten 'security teams must always remember' to 'Security teams:'"),
        ("as reported by", "Shorten attribution to direct citation"),
    ]
    for pattern, advice in fillers:
        if pattern in lower_text:
            words_to_remove.append(advice)

    if excess_chars > 0 and not words_to_remove:
        words_to_remove.append(
            f"Cut introductory padding, redundant adjectives, or trailing clauses to reduce length by at least {excess_chars} characters."
        )
    elif forbidden_url_found:
        words_to_remove.append("Remove the URL and surrounding link phrases entirely.")

    # 5. Required factual points
    required_facts: list[str] = []
    if plan and hasattr(plan, "evidence_items") and plan.evidence_items:
        first_ev = plan.evidence_items[0]
        exc = getattr(first_ev, "excerpt", getattr(first_ev, "source_quote", ""))
        if exc:
            if len(exc) > 120 and "." in exc:
                exc = exc.split(".")[0].strip()
            required_facts.append(exc.strip())
    elif plan and hasattr(plan, "units") and plan.units:
        u = plan.units[0]
        if hasattr(u, "guidance") and u.guidance:
            required_facts.append(u.guidance.split("\n")[0])

    # Assemble precise feedback instructions
    feedback_lines = [
        "PRECISE MARKETING REVISION INSTRUCTIONS:",
        f"1. EXCESS CHARACTERS: Current length is {current_len} chars (platform limit: 280). "
        f"Your draft exceeds the limit by {excess_chars} characters. "
        f"Maximum allowed body prose before URL/CTA is {max_body} characters. "
        f"CRITICAL ACTION: Delete at least {excess_chars + 35} characters. Condense your text into ONE compact sentence (target under {max_body - 35} characters) before the URL so the final post is strictly under 240 characters.",
    ]
    if missing_url:
        feedback_lines.append(
            f"2. MISSING MANDATORY URL: You omitted '{missing_url}'. "
            f"You MUST include this exact URL in your tweet text AND set mandatory_link='{missing_url}'."
        )
    else:
        feedback_lines.append("2. SOURCE LINK: " + ("No link allowed for this format." if forbidden_url_found else "Link status OK."))

    if format_missing:
        feedback_lines.append(f"3. FORMAT-SPECIFIC MISSING CONTENT: {'; '.join(format_missing)}")

    if words_to_remove:
        feedback_lines.append(f"4. OPTIONAL WORDING TO REMOVE: {'; '.join(words_to_remove)}")

    if required_facts:
        feedback_lines.append(f"5. REQUIRED FACTUAL POINT: '{required_facts[0][:150]}'")

    if review_reasons:
        feedback_lines.append(f"6. REVIEWER AUDIT NOTES: {'; '.join(review_reasons[:2])}")

    app_cta = budget_dict.get("approved_cta")
    if not app_cta:
        feedback_lines.append(
            "7. CTA / CONTACT POLICY: Company contact details are NOT approved for this slot. "
            "Do NOT include any email addresses, phone numbers, or commercial CTAs in your revised draft. Focus purely on educational observation."
        )

    feedback_text = "\n".join(feedback_lines)

    return [
        {
            "unit_id": "MARKETING_REVISION",
            "verdict": "REVISION_REQUIRED",
            "failing_text": tweet_text,
            "exact_excess_chars": excess_chars,
            "missing_url": missing_url,
            "target_body_chars": max_body,
            "required_factual_points": required_facts,
            "optional_wording_to_remove": words_to_remove,
            "format_specific_missing": format_missing,
            "reasons": validation_errors + (review_reasons or []),
            "feedback": feedback_text,
        }
    ]

