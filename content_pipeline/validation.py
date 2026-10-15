from __future__ import annotations

import re
from .schemas import BrandRules, Draft, Evidence, WriterConfig
from .skills import EvidenceLookup


def validate_draft(draft: Draft, spec: WriterConfig, brand: BrandRules, evidence: list[Evidence], lookup: EvidenceLookup) -> list[str]:
    errors: list[str] = []
    if not spec.min_tweets <= len(draft.tweets) <= spec.max_tweets:
        errors.append(f"Expected {spec.min_tweets}-{spec.max_tweets} tweets, got {len(draft.tweets)}")
    if spec.require_review_invitation and not re.search(r"\b(review|check|audit|examine|inspect)\b", " ".join(draft.tweets), re.IGNORECASE):
        errors.append("Marketing post requires a practical invitation to review or inspect the contract")
    mapped = {c.text.strip(): c for c in draft.claims}
    if len(mapped) != len(draft.claims):
        errors.append("Duplicate claim mappings")
    for claim in draft.claims:
        if not any(claim.text.strip() in tweet for tweet in draft.tweets):
            errors.append(f"Claim text is absent from tweets: {claim.text!r}")
        missing = lookup.verify_ids(evidence, claim.evidence_ids)
        if missing:
            errors.append(f"Claim cites unknown evidence IDs {missing}")
        cited_text = " ".join(item.excerpt for item in evidence if item.id in claim.evidence_ids).casefold()
        for term in ("time-weighted", "twap", "threshold", "onlyowner", "msg.sender", "reentrancy lock", "circuit breaker", "flash loan", "checks-effects-interactions"):
            if term in claim.text.casefold() and term not in cited_text:
                errors.append(f"Claim uses technical term {term!r} absent from its cited evidence")
    for i, tweet in enumerate(draft.tweets, 1):
        if not tweet.strip():
            errors.append(f"Tweet {i} is empty")
        serialized_length = len(tweet) + (len(f"{i}/{len(draft.tweets)} ") if len(draft.tweets) > 1 else 0)
        if serialized_length > spec.max_chars:
            errors.append(f"Tweet {i} exceeds {spec.max_chars} characters")
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
            if link.rstrip(".,") not in brand.allowed_links:
                errors.append(f"Tweet {i} contains unapproved link {link}")
        sentences = re.split(r"(?<=[.!?])\s+", tweet.strip())
        for sentence in sentences:
            if sentence and not any(sentence in claim.text for claim in draft.claims):
                errors.append(f"Tweet {i} has an unmapped sentence: {sentence!r}")
    return errors

