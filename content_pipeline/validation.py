"""Central deterministic validation for brand, platform, writing quality, and marketing policies."""
from __future__ import annotations

import re
from .schemas import BrandRules, Draft, Evidence, WriterConfig
from .skills import EvidenceLookup
from .writing_quality import validate_writing_quality, WritingQualityReport
from .marketing_policy import (
    validate_marketing_claims,
    validate_editorial_semantic_conformance,
    validate_contact_cta,
    MarketingPolicy,
    load_marketing_policy,
)
from .contact_config import CompanyContactConfig, load_company_contact
from .marketing_format import validate_marketing_format, MarketingFormat


def check_marketing_action(text: str) -> bool:
    """Return True if text contains a genuine actionable reader-oriented security recommendation or review invitation.

    Must invite the reader to act (e.g. review, inspect, isolate, verify, ensure),
    not merely describe passive contract code behavior (e.g. 'don't check return values' or 'fails to verify').
    """
    text_clean = text.strip()

    action_patterns = [
        # Direct imperative at sentence/clause start or coordinate clause (e.g. "Review...", "Inspect...", ", so isolate...", "; isolate...")
        r"(?:^|[.!?;\n,]\s*)(?:Please\s+|so\s+)?(Review|Inspect|Audit|Examine|Assess|Verify|Validate|Isolate|Ensure|Check|Structure|Wrap|Implement)\b",
        # Purpose/mitigation clause leading to action: "To mitigate this risk, isolate each external call..."
        r"\bTo\s+(?:isolate|mitigate|prevent|avoid|address|handle|protect|reduce)[^,.]*,\s*(?:isolate|review|wrap|structure|implement|verify|check|ensure|inspect)\b",
        # Prevention clause: "Prevent this by ensuring..."
        r"\bPrevent this by\s+(?:ensuring|isolating|reviewing|verifying|implementing|structuring)\b",
        # Action directives / recommendations
        r"\b(?:make sure to|be sure to|recommend (?:reviewing|isolating|checking|verifying|auditing|implementing|using))\b",
        r"\b(?:developers should|teams should|contracts must (?:handle|check|verify|isolate|ensure))\b",
        r"\b(?:ensure (?:that\s+)?(?:return values|withdrawals|calls|contracts|each)\b)",
        r"\b(?:explicitly (?:verify|check)|verify the returned|check the returned)\b",
        # Direct verb-object actions: isolate each/external call, review contract/low-level call sites, etc.
        r"\b(?:isolate|review|audit|inspect|verify|check)\s+(?:each|all|the|your|external|low-level)\b",
    ]

    for pat in action_patterns:
        match = re.search(pat, text_clean, re.IGNORECASE)
        if match:
            start_pos = match.start()
            prefix = text_clean[max(0, start_pos - 30):start_pos].lower()
            if not re.search(r"\b(?:don't|doesn't|not|never|cannot|without|fails to|failing to)\s*$", prefix):
                return True

    return False


def validate_brand_and_platform(
    tweets: list[str],
    brand: BrandRules,
    spec: WriterConfig | None = None,
    allowed_run_links: list[str] | None = None,
    enforce_review_invitation: bool = True,
) -> list[str]:
    """Central deterministic validation for brand, platform, and content-type rules."""
    errors: list[str] = []

    # 1. Content-type tweet count and review invitation
    if spec:
        if not (spec.min_tweets <= len(tweets) <= spec.max_tweets):
            errors.append(f"Expected {spec.min_tweets}-{spec.max_tweets} tweets, got {len(tweets)}")
        if spec.require_review_invitation and enforce_review_invitation:
            full_text = " ".join(tweets)
            if not check_marketing_action(full_text):
                errors.append("Marketing post requires a practical security action")

    # 2. Duplicate tweets check
    normalized_tweets = [" ".join(tweet.casefold().split()) for tweet in tweets]
    if len(normalized_tweets) != len(set(normalized_tweets)):
        errors.append("Thread contains duplicate tweets")

    # 3. Per-tweet constraints: length, brand rules, banned characters, hashtags, banned words, unapproved links
    max_chars = spec.max_chars if spec else 280
    valid_links = set(brand.allowed_links)
    if allowed_run_links:
        valid_links.update(l.rstrip(".,;") for l in allowed_run_links)

    for i, tweet in enumerate(tweets, 1):
        if not tweet.strip():
            errors.append(f"Tweet {i} is empty")
        serialized_length = len(tweet) + (len(f"{i}/{len(tweets)} ") if len(tweets) > 1 else 0)
        if serialized_length > max_chars:
            errors.append(f"Tweet {i} exceeds {max_chars} characters")
        stat_clean_text = re.sub(r"(?:phone|tel):\s*[^\s|]+", "", tweet, flags=re.IGNORECASE)
        stat_clean_text = re.sub(r"https?://[^\s)]+", "", stat_clean_text)
        stat_clean_text = re.sub(r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b", "", stat_clean_text)
        sentences_for_stat = re.split(r"(?<=[.!?])\s+|\n+", stat_clean_text)
        for s in sentences_for_stat:
            if re.search(r"\bSanadSquad\b", s, re.IGNORECASE) and re.search(r"\b\d+(?:[.,]\d+)?\b", s):
                if not any(stat.casefold() in s.casefold() for stat in brand.approved_statistics):
                    errors.append(f"Tweet {i} contains an unapproved company statistic")
                    break
        for char in brand.banned_characters:
            if char in tweet:
                errors.append(f"Tweet {i} contains banned character {char!r}")
        if brand.forbid_hashtags and re.search(r"(?<!\w)#[\w]+", tweet):
            errors.append(f"Tweet {i} contains a hashtag")
        for word in brand.banned_words:
            if re.search(re.escape(word), tweet, flags=re.IGNORECASE):
                errors.append(f"Tweet {i} contains banned phrase {word!r}")
        links = re.findall(r"https?://[^\s)]+", tweet)
        for link in links:
            if link.rstrip(".,;") not in valid_links:
                errors.append(f"Tweet {i} contains unapproved link {link}")

    return errors


def validate_piece_deterministic(
    tweets: list[str],
    brand: BrandRules,
    spec: WriterConfig | None = None,
    allowed_run_links: list[str] | None = None,
    marketing_format: str | None = None,
    marketing_policy: MarketingPolicy | None = None,
    writing_rules: dict | None = None,
    contact_config: CompanyContactConfig | None = None,
    allow_cta: bool = False,
    content_type: str | None = None,
    enforce_review_invitation: bool = False,
    service_line: str | None = None,
    evidence: list[Evidence] | None = None,
) -> tuple[bool, list[str], WritingQualityReport]:
    """Execute all deterministic checks in sequence: brand/platform -> writing quality -> claims -> editorial semantic -> format -> contact CTA."""
    all_errors: list[str] = []

    # 1. Brand and platform rules
    is_marketing = bool(
        (content_type == "marketing-post") or (spec and spec.max_tweets == 1 and spec.min_tweets == 1)
    )
    should_enforce_invitation = enforce_review_invitation and not is_marketing
    bp_errors = validate_brand_and_platform(
        tweets,
        brand,
        spec,
        allowed_run_links=allowed_run_links,
        enforce_review_invitation=should_enforce_invitation,
    )
    all_errors.extend(bp_errors)

    # 2. Writing quality rules (anti-AI markers, banned vocabulary, hedging, variance)
    wq_report = validate_writing_quality(tweets, rules=writing_rules)
    if not wq_report.passed:
        all_errors.extend(wq_report.errors)

    # 3. Marketing policy, claims, and editorial semantic conformance if applicable
    if is_marketing:
        policy = marketing_policy or load_marketing_policy()
        claim_errors = validate_marketing_claims(tweets, policy=policy, service_line=service_line)
        all_errors.extend(claim_errors)

        editorial_errors = validate_editorial_semantic_conformance(
            tweets=tweets,
            service_line=service_line,
            fetched_urls=allowed_run_links,
            evidence=evidence,
        )
        all_errors.extend(editorial_errors)

        if marketing_format:
            fmt_errors = validate_marketing_format(
                tweets,
                selected_format=marketing_format,
                fetched_urls=allowed_run_links,
            )
            all_errors.extend(fmt_errors)

    # 4. Commercial contact CTA validation
    ctype = content_type or (spec.name if spec and hasattr(spec, "name") else ("marketing-post" if is_marketing else "tech-thread"))
    contact_errors = validate_contact_cta(
        tweets=tweets,
        contact_config=contact_config,
        allow_cta=allow_cta,
        content_type=ctype,
    )
    all_errors.extend(contact_errors)

    return len(all_errors) == 0, all_errors, wq_report


def validate_draft(
    draft: Draft,
    spec: WriterConfig,
    brand: BrandRules,
    evidence: list[Evidence],
    lookup: EvidenceLookup,
) -> list[str]:
    """Validate full draft including brand/platform rules and claim mappings."""
    allowed_links = [e.url for e in evidence if e.url]
    errors = validate_brand_and_platform(draft.tweets, brand, spec, allowed_run_links=allowed_links)

    mapped = {c.text.strip(): c for c in draft.claims}
    if len(mapped) != len(draft.claims):
        errors.append("Duplicate claim mappings")
    for claim in draft.claims:
        if not any(claim.text.strip() in tweet for tweet in draft.tweets):
            errors.append(f"Claim text is absent from tweets: {claim.text!r}")
        missing = lookup.verify_ids(evidence, claim.evidence_ids)
        if missing:
            errors.append(f"Claim cites unknown evidence IDs {missing}")
        cited_text = " ".join(item.source_quote or "" for item in evidence if item.id in claim.evidence_ids).casefold()
        for term in ("time-weighted", "twap", "threshold", "onlyowner", "msg.sender", "reentrancy lock", "circuit breaker", "flash loan", "checks-effects-interactions"):
            equivalent = term == "time-weighted" and "twap" in cited_text
            if term in claim.text.casefold() and term not in cited_text and not equivalent:
                errors.append(f"Claim uses technical term {term!r} absent from its cited evidence")
    for i, tweet in enumerate(draft.tweets, 1):
        sentences = re.split(r"(?<=[.!?])\s+", tweet.strip())
        for sentence in sentences:
            if sentence and not any(sentence in claim.text for claim in draft.claims):
                errors.append(f"Tweet {i} has an unmapped sentence: {sentence!r}")
    return errors
