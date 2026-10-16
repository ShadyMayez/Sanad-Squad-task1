"""Independent text coverage and conservative atomic-clause extraction.

Every clause is treated as factual or uncertain and sent to verification. This
does not depend on the Writer's claim list for deciding what text needs review.
"""
from __future__ import annotations

import re
from .schemas import AtomicClaim, Draft, Evidence, SentenceRelationRecord
from .relation_integrity import claim_relation_hints, HISTORICAL_QUALIFIER, LEGACY_CONSTRUCTOR, NORMATIVE_START, RECOMMENDATION
from .text_spans import sentence_matches

CLAUSE = re.compile(
    r",\s*(?:since|because|so that|in order to|as|due to|caused by|resulting in|leading to)\s+"
    r"|\s+(?:since|because|so that|in order to|due to)\s+"
    r"|,\s*by\s+"
    r"|\s+by\s+(?=[a-z]+ing\b)"
    r"|;\s*(?:therefore|consequently),?\s*"
    r"|\s+(?:and|but|while|whereas)\s+"
    r"|;\s*",
    re.IGNORECASE,
)
QUALIFIER = re.compile(r"\b(?:always|never|all|every|only|completely|guaranteed|may|can|if|unless|some|often|must|not|cannot|no|without|before|after|when|v\d+(?:\.\d+)*|\d+(?:\.\d+)?%?)\b", re.IGNORECASE)
CONNECTORS = re.compile(r"(?:and|but|while|whereas|since|because|so\s*that|in\s*order\s*to|by|as|due\s+to|caused\s+by|resulting\s+in|leading\s+to|leads\s+to|therefore|consequently)", re.IGNORECASE)

RELATION_PATTERNS = [
    # because
    (re.compile(r"^because\s+(.+?),\s*(.+)$", re.IGNORECASE), "because", "CAUSAL", True),
    (re.compile(r"^(.+?),\s*because\s+(.+)$", re.IGNORECASE), "because", "CAUSAL", False),
    (re.compile(r"^(.+?)\s+because\s+(.+)$", re.IGNORECASE), "because", "CAUSAL", False),
    # since
    (re.compile(r"^since\s+(.+?),\s*(.+)$", re.IGNORECASE), "since", "CAUSAL", True),
    (re.compile(r"^(.+?),\s*since\s+(.+)$", re.IGNORECASE), "since", "CAUSAL", False),
    (re.compile(r"^(.+?)\s+since\s+(.+)$", re.IGNORECASE), "since", "CAUSAL", False),
    # as (causal)
    (re.compile(r"^as\s+(.+?),\s*(.+)$", re.IGNORECASE), "as", "CAUSAL", True),
    (re.compile(r"^(.+?),\s*as\s+(.+)$", re.IGNORECASE), "as", "CAUSAL", False),
    # due to
    (re.compile(r"^due\s+to\s+(.+?),\s*(.+)$", re.IGNORECASE), "due to", "CAUSAL", True),
    (re.compile(r"^(.+?),\s*due\s+to\s+(.+)$", re.IGNORECASE), "due to", "CAUSAL", False),
    (re.compile(r"^(.+?)\s+due\s+to\s+(.+)$", re.IGNORECASE), "due to", "CAUSAL", False),
    # caused by
    (re.compile(r"^caused\s+by\s+(.+?),\s*(.+)$", re.IGNORECASE), "caused by", "CAUSAL", True),
    (re.compile(r"^(.+?),\s*(?:is\s+)?caused\s+by\s+(.+)$", re.IGNORECASE), "caused by", "CAUSAL", False),
    (re.compile(r"^(.+?)\s+(?:is\s+)?caused\s+by\s+(.+)$", re.IGNORECASE), "caused by", "CAUSAL", False),
    # resulting in
    (re.compile(r"^(.+?),\s*resulting\s+in\s+(.+)$", re.IGNORECASE), "resulting in", "CAUSAL", True),
    (re.compile(r"^(.+?)\s+resulting\s+in\s+(.+)$", re.IGNORECASE), "resulting in", "CAUSAL", True),
    # leading to / leads to
    (re.compile(r"^(.+?),\s*leading\s+to\s+(.+)$", re.IGNORECASE), "leading to", "CAUSAL", True),
    (re.compile(r"^(.+?)\s+(?:leading\s+to|leads\s+to)\s+(.+)$", re.IGNORECASE), "leading to", "CAUSAL", True),
    # by (instrumental)
    (re.compile(r"^by\s+([a-z]+ing\b.+?),\s*(.+)$", re.IGNORECASE), "by", "INSTRUMENTAL", True),
    (re.compile(r"^(.+?),\s*by\s+([a-z]+ing\b.+)$", re.IGNORECASE), "by", "INSTRUMENTAL", False),
    (re.compile(r"^(.+?)\s+by\s+([a-z]+ing\b.+)$", re.IGNORECASE), "by", "INSTRUMENTAL", False),
    # if / when (conditional)
    (re.compile(r"^(?:if|when)\s+(.+?),\s*(.+)$", re.IGNORECASE), "if", "CONDITIONAL", True),
    (re.compile(r"^(.+?)\s+(?:if|when)\s+(.+)$", re.IGNORECASE), "if", "CONDITIONAL", False),
    # so that / in order to (teleological)
    (re.compile(r"^(.+?),\s*(?:so\s+that|in\s+order\s+to)\s+(.+)$", re.IGNORECASE), "so that", "TELEOLOGICAL", False),
    (re.compile(r"^(.+?)\s+(?:so\s+that|in\s+order\s+to)\s+(.+)$", re.IGNORECASE), "so that", "TELEOLOGICAL", False),
    # therefore / consequently
    (re.compile(r"^(.+?)[;,]\s*(?:therefore|consequently),?\s*(.+)$", re.IGNORECASE), "therefore", "CAUSAL", True),
    # root cause / underlying cause
    (re.compile(r"^(?:the\s+)?(?:root\s+cause|core\s+risk|primary\s+cause|underlying\s+cause|cause)\s+of\s+(.+?)\s+is\s+(.+)$", re.IGNORECASE), "is", "CAUSAL", False),
    # authorization / exposure / re-initialization
    (re.compile(r"^(.+?)\s+(?:exposes)\s+(.+)$", re.IGNORECASE), "exposes", "CAUSAL", True),
    # mitigation guarantee / elimination
    (re.compile(r"^(.+?)\s+(?:completely\s+|totally\s+)?(?:eliminates|guarantees|prevents(?:\s+all)?|blocks(?:\s+all)?|stops(?:\s+all)?)\s+(.+)$", re.IGNORECASE), "eliminates", "CAUSAL", True),
]


def extract_sentence_relations_for_sentence(
    sentence: str, tweet_index: int, sentence_no: int, start: int, end: int, candidate_ids: list[str]
) -> list[SentenceRelationRecord]:
    relations: list[SentenceRelationRecord] = []
    seen = set()

    def _find_relations(text: str):
        for pattern, connector, rel_type, inverted in RELATION_PATTERNS:
            m = pattern.search(text)
            if m:
                if inverted:
                    premise = m.group(1).strip()
                    conclusion = m.group(2).strip()
                else:
                    conclusion = m.group(1).strip()
                    premise = m.group(2).strip()
                eff_rel_type = rel_type
                if rel_type == "CAUSAL" and (NORMATIVE_START.search(conclusion) or RECOMMENDATION.search(conclusion)) and not (NORMATIVE_START.search(premise) or RECOMMENDATION.search(premise)):
                    eff_rel_type = "ACTION_RATIONALE"
                key = (connector, premise, conclusion)
                if key not in seen:
                    seen.add(key)
                    rel_id = f"t{tweet_index + 1}s{sentence_no}rel{len(relations) + 1}"
                    relations.append(SentenceRelationRecord(
                        id=rel_id,
                        tweet_index=tweet_index,
                        sentence=sentence,
                        start=start,
                        end=end,
                        connector=connector,
                        premise=premise,
                        conclusion=conclusion,
                        relation_type=eff_rel_type,
                        candidate_evidence_ids=candidate_ids,
                        direction="premise_to_conclusion",
                        quantifiers=QUALIFIER.findall(sentence),
                        conditions=re.findall(r"\b(?:if|when|unless)\b.+?(?:,|$)", sentence, re.I),
                    ))
                _find_relations(premise)
                _find_relations(conclusion)
                break

    _find_relations(sentence)
    return relations


def extract_sentence_relations(draft: Draft, evidence: list[Evidence]) -> list[SentenceRelationRecord]:
    all_relations: list[SentenceRelationRecord] = []
    known = {item.id for item in evidence}
    for tweet_index, tweet in enumerate(draft.tweets):
        sentence_no = 0
        for sentence_match in sentence_matches(tweet):
            sentence_no += 1
            sentence = tweet[sentence_match.start():sentence_match.end()].strip()
            if not sentence:
                continue
            mappings = [mapping for mapping in draft.claims if sentence in mapping.text or mapping.text in sentence]
            candidate_ids = list(dict.fromkeys(id for mapping in mappings for id in mapping.evidence_ids if id in known))
            if not candidate_ids:
                candidate_ids = list(dict.fromkeys(id for mapping in draft.claims for id in mapping.evidence_ids if id in known))
            rels = extract_sentence_relations_for_sentence(
                sentence, tweet_index, sentence_no, sentence_match.start(), sentence_match.end(), candidate_ids
            )
            all_relations.extend(rels)
    return all_relations


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
            rels = extract_sentence_relations_for_sentence(
                sentence, tweet_index, sentence_no, sentence_match.start(), sentence_match.end(), candidate_ids
            )
            matched_rel = rels[0] if rels else None
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
                part_qualifiers = QUALIFIER.findall(part)
                if HISTORICAL_QUALIFIER.search(sentence):
                    part_qualifiers.append("historical_scope_qualified")
                if LEGACY_CONSTRUCTOR.search(part):
                    part_qualifiers.append("legacy_solidity_constructor")
                claims.append(AtomicClaim(
                    id=f"t{tweet_index + 1}s{sentence_no}c{part_no}", tweet_index=tweet_index,
                    start=local, end=end, span=part, proposition=part,
                    sentence=sentence, qualifiers=part_qualifiers,
                    claim_type="uncertain" if sentence.endswith("?") else "factual",
                    candidate_evidence_ids=candidate_ids,
                    relation_hints=claim_relation_hints(part),
                    sentence_relation=matched_rel,
                ))
        uncovered = "".join(ch for i, ch in enumerate(tweet) if not covered[i] and ch.isalnum())
        # Clause connectors are grammar rather than a separate factual assertion.
        if re.sub(CONNECTORS, "", uncovered):
            errors.append(f"Tweet {tweet_index + 1} contains uncovered substantive text: {uncovered!r}")
    if not claims:
        errors.append("No atomic claims extracted")
    if len(claims) > 25:
        errors.append("Too many atomic claims for one bounded verification pass (maximum 25)")
    return claims, errors
