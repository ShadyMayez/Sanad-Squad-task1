"""Independent text coverage and conservative atomic-clause extraction.

Every clause is treated as factual or uncertain and sent to verification. This
does not depend on the Writer's claim list for deciding what text needs review.
"""
from __future__ import annotations

import re
from .schemas import AtomicClaim, Draft, Evidence
from .text_spans import sentence_matches

CLAUSE = re.compile(r"\s+(?:and|but|while|whereas)\s+|;\s*", re.IGNORECASE)
QUALIFIER = re.compile(r"\b(?:always|never|all|every|only|completely|guaranteed|may|can|if|unless|some|often|must|not|cannot|no|without|before|after|when|v\d+(?:\.\d+)*|\d+(?:\.\d+)?%?)\b", re.IGNORECASE)


def extract_claims(draft: Draft, evidence: list[Evidence]) -> tuple[list[AtomicClaim], list[str]]:
    claims: list[AtomicClaim] = []
    errors: list[str] = []
    known = {item.id for item in evidence}
    for tweet_index, tweet in enumerate(draft.tweets):
        covered = [False] * len(tweet)
        sentence_no = 0
        for sentence_match in sentence_matches(tweet):
            sentence_no += 1
            sentence = tweet[sentence_match.start():sentence_match.end()].strip()
            if not sentence:
                continue
            separators = list(CLAUSE.finditer(sentence))
            starts = [0] + [m.end() for m in separators]
            ends = [m.start() for m in separators] + [len(sentence)]
            parts = [sentence[start:end].strip() for start, end in zip(starts, ends)]
            if not all(parts):
                parts = [sentence]
            mappings = [mapping for mapping in draft.claims if sentence in mapping.text or mapping.text in sentence]
            candidate_ids = list(dict.fromkeys(id for mapping in mappings for id in mapping.evidence_ids))
            if not mappings:
                errors.append(f"Tweet {tweet_index + 1} sentence {sentence_no} has no Writer evidence mapping")
            unknown = [id for id in candidate_ids if id not in known]
            if unknown:
                errors.append(f"Tweet {tweet_index + 1} sentence {sentence_no} cites unknown evidence IDs {unknown}")
            if not candidate_ids:
                # No implicit evidence substitution. Still record a coverage error.
                continue
            search_from = sentence_match.start()
            for part_no, part in enumerate(parts, 1):
                local = tweet.find(part, search_from, sentence_match.end())
                if local < 0:
                    errors.append(f"Cannot locate atomic span {part!r}")
                    continue
                end = local + len(part)
                for i in range(local, end):
                    covered[i] = True
                search_from = end
                claims.append(AtomicClaim(
                    id=f"t{tweet_index + 1}s{sentence_no}c{part_no}", tweet_index=tweet_index,
                    start=local, end=end, span=part, proposition=part,
                    sentence=sentence, qualifiers=QUALIFIER.findall(part),
                    claim_type="uncertain" if sentence.endswith("?") else "factual",
                    candidate_evidence_ids=candidate_ids,
                ))
        uncovered = "".join(ch for i, ch in enumerate(tweet) if not covered[i] and ch.isalnum())
        # Clause connectors are grammar rather than a separate factual assertion.
        if re.sub(r"(?:and|but|while|whereas)", "", uncovered, flags=re.IGNORECASE):
            errors.append(f"Tweet {tweet_index + 1} contains uncovered substantive text: {uncovered!r}")
    if not claims:
        errors.append("No atomic claims extracted")
    if len(claims) > 25:
        errors.append("Too many atomic claims for one bounded verification pass (maximum 25)")
    return claims, errors
