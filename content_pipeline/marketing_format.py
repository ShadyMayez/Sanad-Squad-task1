"""Marketing post format definitions and deterministic format validation."""
from __future__ import annotations

import re
from enum import Enum
from pydantic import BaseModel, Field


class MarketingFormat(str, Enum):
    SHORT_TIP = "short-tip"
    DIFFERENTIATION = "differentiation"
    SERVICE_OVERVIEW = "service-overview"
    NEWS_REACTION = "news-reaction"
    LEARNING_RESOURCE = "learning-resource"
    MARKETING_THREAD = "marketing-thread"  # Reserved future format


class FormatSpec(BaseModel):
    format_name: MarketingFormat
    min_sentences: int = 1
    max_sentences: int | None = None
    requires_link: bool = False
    forbids_link: bool = False
    max_tweets: int = 1
    description: str = ""


FORMAT_SPECS: dict[MarketingFormat, FormatSpec] = {
    MarketingFormat.SHORT_TIP: FormatSpec(
        format_name=MarketingFormat.SHORT_TIP,
        min_sentences=1,
        max_sentences=3,
        requires_link=False,
        forbids_link=True,
        max_tweets=1,
        description="One to three sentences. A single concrete observation or review habit. No link. No preamble.",
    ),
    MarketingFormat.DIFFERENTIATION: FormatSpec(
        format_name=MarketingFormat.DIFFERENTIATION,
        min_sentences=1,
        requires_link=False,
        forbids_link=False,
        max_tweets=1,
        description="Evidence-backed gap between contract-only audits and connected attack surface.",
    ),
    MarketingFormat.SERVICE_OVERVIEW: FormatSpec(
        format_name=MarketingFormat.SERVICE_OVERVIEW,
        min_sentences=1,
        requires_link=False,
        forbids_link=False,
        max_tweets=1,
        description="What a service line actually covers and why it matters now.",
    ),
    MarketingFormat.NEWS_REACTION: FormatSpec(
        format_name=MarketingFormat.NEWS_REACTION,
        min_sentences=1,
        requires_link=True,
        forbids_link=False,
        max_tweets=1,
        description="Recent event plus SanadSquad technical interpretation. Source link mandatory.",
    ),
    MarketingFormat.LEARNING_RESOURCE: FormatSpec(
        format_name=MarketingFormat.LEARNING_RESOURCE,
        min_sentences=1,
        requires_link=True,
        forbids_link=False,
        max_tweets=1,
        description="Attributed useful article, doc, or roadmap with rationale. Working link mandatory.",
    ),
    MarketingFormat.MARKETING_THREAD: FormatSpec(
        format_name=MarketingFormat.MARKETING_THREAD,
        min_sentences=3,
        requires_link=False,
        forbids_link=False,
        max_tweets=7,
        description="Reserved future format (3-7 tweets). Not authorized under single-tweet marketing-post.",
    ),
}


def validate_marketing_format(
    tweets: list[str],
    selected_format: MarketingFormat | str,
    fetched_urls: list[str] | None = None,
) -> list[str]:
    """Validate that draft tweets conform to the selected marketing format and link policy."""
    errors: list[str] = []
    fmt_enum = MarketingFormat(selected_format) if isinstance(selected_format, str) else selected_format

    if fmt_enum == MarketingFormat.MARKETING_THREAD:
        errors.append(
            "Format 'marketing-thread' is a reserved future content type and is NOT authorized "
            "under the current single-tweet marketing-post contract."
        )
        return errors

    spec = FORMAT_SPECS.get(fmt_enum)
    if not spec:
        errors.append(f"Unknown marketing format '{selected_format}'")
        return errors

    # Check tweet count
    if len(tweets) != 1:
        errors.append(
            f"Marketing format '{spec.format_name.value}' requires exactly 1 tweet (platform limit), "
            f"got {len(tweets)} tweets."
        )

    for i, tweet in enumerate(tweets, 1):
        if len(tweet) > 280:
            errors.append(f"Tweet {i} exceeds 280 character limit: {len(tweet)} characters.")

    full_text = " ".join(tweets).strip()

    # Sentence count check for short-tip
    sentences = [s.strip() for s in re.split(r"(?<=[.!?])\s+", full_text) if s.strip()]
    if spec.max_sentences and len(sentences) > spec.max_sentences:
        errors.append(
            f"Format '{spec.format_name.value}' allows at most {spec.max_sentences} sentences, "
            f"found {len(sentences)}."
        )

    # Link extraction
    found_links = re.findall(r"https?://[^\s)]+", full_text)
    clean_links = [l.rstrip(".,;") for l in found_links]

    if spec.forbids_link and clean_links:
        errors.append(f"Format '{spec.format_name.value}' must not contain any links (strictly forbids links), but found: {clean_links}")

    if spec.requires_link and not clean_links:
        errors.append(f"Format '{spec.format_name.value}' requires an authorized source link (mandates link), but none was found.")

    # Validate that any present link was retrieved during the current run
    if clean_links and fetched_urls is not None:
        fetched_set = {u.rstrip(".,;") for u in fetched_urls}
        for link in clean_links:
            if link not in fetched_set:
                errors.append(
                    f"Post link '{link}' was not retrieved during this run. "
                    f"Only run-fetched, authorized source links are permitted."
                )

    # Substantive format checks
    if fmt_enum == MarketingFormat.NEWS_REACTION:
        # A news-reaction must contain:
        # 1. A specific retrieved event or announcement marker
        # 2. An attributable source and date/timeframe
        # 3. A relevant interpretation
        has_event = bool(re.search(
            r"\b(reported|reports|disclosed|disclosure|advisory|advisories|incident|incidents|breach|breaches|vulnerability|vulnerabilities|released|releases|published|publishes|announced|announces|update|updates|findings?|uncovered|discovered)\b",
            full_text,
            re.IGNORECASE,
        ))
        has_attribution = bool(re.search(
            r"\b(OWASP|Solana|Ethereum|OpenZeppelin|Coinbase|Stripe|NIST|CVE|researchers?|team|foundation|consortium|working group|blog|documentation|this week|recently|latest|202[3-6]|Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\b",
            full_text,
            re.IGNORECASE,
        ))
        has_interpretation = bool(re.search(
            r"\b(shows|highlights|means|demonstrates|signals|indicates|reveals|proves|underscores|takeaway|lesson|implication|mitigation|countermeasure|why this matters)\b",
            full_text,
            re.IGNORECASE,
        ))

        missing_elements = []
        if not has_event:
            missing_elements.append("specific event/announcement marker (e.g. reported, disclosed, released, breach)")
        if not has_attribution:
            missing_elements.append("attributable source or date/timeframe")
        if not has_interpretation:
            missing_elements.append("analytical interpretation (e.g. shows, highlights, demonstrates, lesson)")

        if missing_elements:
            errors.append(
                f"Format 'news-reaction' failure: Post lacks required components: {', '.join(missing_elements)}. "
                "Generic security advice with a URL is not a valid news-reaction."
            )

    elif fmt_enum == MarketingFormat.LEARNING_RESOURCE:
        # A learning-resource must link to a verified resource and explain why it is worth reading
        has_learning_rationale = bool(re.search(
            r"\b(deep dive|guide|breakdown|explains?|walkthrough|overview|specification|spec|mechanics|frameworks?|reference|primer|worth reading|essential reading|details? (?:how|on|in)|analyzes?|covers?|study)\b",
            full_text,
            re.IGNORECASE,
        ))
        if not has_learning_rationale:
            errors.append(
                "Format 'learning-resource' failure: Post must explain why the linked resource is worth reading "
                "(e.g. breakdown, guide, specification mechanics, walkthrough). Generic security advice with a link is not a learning-resource."
            )

    return errors
