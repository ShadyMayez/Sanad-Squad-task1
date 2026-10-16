"""Conservative source-to-claim relation checks, separate from model opinion.

These checks can veto a positive entailment but never create one. Classification is
auditable metadata, not proof. Exact source spans remain the only accepted proof.
"""
from __future__ import annotations

import re
from dataclasses import dataclass

from .schemas import AtomicClaim, ClaimRelation, ModelSemanticDecision, SentenceRelationRecord

ROOT_CAUSE = re.compile(r"\b(?:root cause|core risk|underlying cause|(?:the )?cause of|caused by|due to|stems from|arises from|results from|because of|the reason (?:is|for))\b", re.I)
RECOMMENDATION = re.compile(r"\b(?:source recommends?|recommend(?:s|ed)?|best practice|to (?:avoid|prevent|mitigate)|make sure|review|check|validate|perform|use|isolate)\b", re.I)
SOURCE_ATTRIBUTION = re.compile(r"\b(?:the source|source text|the guidance|the documentation|the reference)\s+(?:recommends?|advises?|instructs?)\b|\baccording to (?:the )?(?:source|guidance|documentation)\b", re.I)
NORMATIVE_EVIDENCE = re.compile(r"\b(?:remediation|recommend(?:s|ed|ation)?|should|must|best practice|to (?:avoid|prevent|mitigate)|make sure|consider)\b", re.I)
EFFECTIVENESS = re.compile(r"\b(?:guarantees?|eliminates?|will prevent|prevents? all|ensures?|reduces?|limits?|stops?)\b", re.I)
CONSEQUENCE = re.compile(r"\b(?:can|may|could)\s+(?:lead to|cause|result in)\b|\bloss of\b|\bdenial.of.service\b", re.I)
MECHANISM = re.compile(r"\b(?:control flow|call(?:s)? back|reenter|reentrancy|invocation|bytecode|execution resumes)\b", re.I)
CONDITION = re.compile(r"\b(?:if|unless|when|only if)\b", re.I)
DIRECT_CAUSAL = re.compile(r"\b(?:due to|caused by|stems from|arises from|because|causes?|leads? to|results? in|allows?|enables?|triggers?)\b|\bby\s+\w+(?:\s+\w+){0,8}\s*,", re.I)
INSTRUMENTAL = re.compile(r"\bby\s+(?:\w+\s+){0,2}[a-z]+ing\b", re.I)
CAUSAL_CONNECTIVE = re.compile(r"\b(?:because|since)\b", re.I)
NORMATIVE_START = re.compile(r"^(?:remediation\b\s*)?(?:make sure|use|perform|check|review|validate|implement|consider|isolate|avoid|leverage|ensure|update)\b|^remediation\b", re.I)
STRONG_CERTAINTY = re.compile(r"\b(?:guarantees?|eliminates?|always|never|completely|prevents? all)\b", re.I)

LEGACY_CONSTRUCTOR = re.compile(
    r"\b(?:wrongly\s+nam(?:ing|ed)|misnam(?:ing|ed)|mis-nam(?:ing|ed))\s+(?:a\s+)?(?:function|constructor)\b"
    r"|\b(?:function|constructor)\s+(?:is\s+)?(?:wrongly\s+named|misnamed)\b"
    r"|\bexpos(?:e|es|ing)\s+constructor\b"
    r"|\bconstructor\s+(?:code\s+)?(?:ends\s+up\s+in|in)\s+runtime\s+byte\s*code\b"
    r"|\bcall(?:ed)?\s+by\s+anyone\s+to\s+re-?initialize\b",
    re.I,
)
HISTORICAL_QUALIFIER = re.compile(
    r"\b(?:legacy|historical|pre-0\.4\.22|prior\s+to\s+(?:Solidity\s+)?0\.4\.22|older(?:\s+versions?)?|earlier\s+versions?|Solidity\s*<\s*0\.4\.22|before\s+0\.4\.22)\b",
    re.I,
)
# Universal-scope phrases that indicate a claim is making an absolute assertion
# over an entire category. These are reliable signals of scope expansion beyond
# what any single source span can entail. The reconciliation pass is suppressed
# when present to prevent a 3rd model call from reversing a correct skeptical veto.
UNIVERSAL_QUANTIFIER = re.compile(
    r"\b(?:every(?:\s+\w+){0,4}|all\s+(?:\w+\s+){0,3}(?:manipulation|attack|call|contract|vulnerability|case|instance|oracle)"
    r"|always\b|never\b|completely\s+\w|destroys?\s+all|removes?\s+all|eliminates?\s+all|prevents?\s+all|blocks?\s+all"
    r"|stops?\s+all|ensures?\s+all)\b",
    re.I,
)
# Bare prevention verbs in a claim (e.g. "A lock prevents X from Y") signal an
# effectiveness assertion even when no absolute quantifier is present. The pattern
# requires a non-modal verb form (prevents/blocks/stops) to avoid matching hedged
# claims ("may prevent", "can block"). Reconciliation is suppressed for such claims.
ABSOLUTE_PREVENTION = re.compile(
    r"\b(?:prevent(?:s|ed)|block(?:s|ed)|stop(?:s|ped))\s+(?:the\s+)?\w",
    re.I,
)
# This names an explicit relation to the claim. Generic appearances of
# "contradict" do not trigger the gate (e.g. "does not contradict").
EXPLICIT_OPPOSITION = re.compile(r"\b(?<!not )(?:directly\s+)?contradict(?:s|ed|ing)?\s+(?:the\s+)?(?:claim|assertion|proposition)(?:'s)?\b|\bincompatible with (?:the )?(?:claim|assertion|proposition)\b", re.I)


def source_span_relation_hints(text: str) -> list[str]:
    """Auditable syntax hints about a selected span, never proof of entailment."""
    roles = []
    if NORMATIVE_START.search(text) or re.search(r"\b(?:remediation|recommended to|best practice)\b", text, re.I):
        roles.append("RECOMMENDATION")
    if DIRECT_CAUSAL.search(text) and not NORMATIVE_START.search(text):
        roles.append("CAUSAL_DESCRIPTION")
    if STRONG_CERTAINTY.search(text):
        roles.append("ABSOLUTE_EFFECTIVENESS")
    if re.search(r"\b(?:may|might|could|can)\b", text, re.I):
        roles.append("POSSIBILITY")
    return roles or ["DESCRIPTION"]


def claim_relation_hints(text: str) -> list[ClaimRelation]:
    """Extract high-confidence role hints; other roles remain model judgments."""
    roles: list[ClaimRelation] = []
    for expression, role in ((ROOT_CAUSE, "ROOT_CAUSE"), (RECOMMENDATION, "MITIGATION_RECOMMENDATION"),
            (EFFECTIVENESS, "MITIGATION_EFFECTIVENESS"), (CONSEQUENCE, "CONSEQUENCE"),
            (MECHANISM, "EXECUTION_MECHANISM"), (CONDITION, "CONDITIONAL_CLAIM"),
            (INSTRUMENTAL, "EXECUTION_MECHANISM")):
        if expression.search(text):
            roles.append(role)
    return roles or ["DESCRIPTIVE_FACT"]


@dataclass(frozen=True)
class RelationAssessment:
    roles: list[ClaimRelation]
    passed: bool
    invalid: bool
    reason: str


RELATION_STOPWORDS = {
    "that", "with", "from", "into", "their", "each", "this", "have", "been", "when",
    "also", "your", "more", "some", "such", "than", "then", "were", "will", "does",
    "done", "doing", "what", "which", "where", "could", "would", "should", "might",
    "must", "contract", "contracts", "because", "since", "about", "other", "occur",
    "occurs", "occurring", "allow", "allows", "make", "sure", "these", "those"
}


def substantive_relation_tokens(text: str) -> set[str]:
    """Extract substantive topical tokens for causal bridging checks."""
    return set(re.findall(r"\b[a-zA-Z]{4,}|\b[A-Z]{3}\b", text.lower())) - RELATION_STOPWORDS


CLAUSE_BOUNDARY = re.compile(r"(?:(?<=[a-z0-9])\.\s+(?=[A-Z])|;\s*|,\s*(?i:whereas|while|but)\s+)")


SYNONYMS: dict[str, set[str]] = {
    "fund": {"fund", "ether", "asset", "balance", "token"},
    "funds": {"fund", "ether", "asset", "balance", "token"},
    "ether": {"fund", "ether", "asset", "balance"},
    "lose": {"lose", "loss", "drain", "withdraw"},
    "loss": {"lose", "loss", "drain", "withdraw"},
}


def matches_tokens(span_text: str, tokens: set[str]) -> bool:
    s = span_text.lower()
    for tok in tokens:
        if tok[:4] in s:
            return True
        if tok in SYNONYMS:
            if any(syn in s for syn in SYNONYMS[tok]):
                return True
    return False


def check_dual_topic_causal_bridging(premise: str, conclusion: str, bridging_spans: list[str]) -> bool:
    """Ensure at least one causal span substantively connects premise and conclusion topics within a unified clause (preventing R3 splicing)."""
    p_tokens = substantive_relation_tokens(premise)
    c_tokens = substantive_relation_tokens(conclusion)
    if not p_tokens or not c_tokens:
        return bool(bridging_spans)
    for span in bridging_spans:
        segments = [s.strip() for s in CLAUSE_BOUNDARY.split(span) if s.strip()]
        for seg in segments:
            if matches_tokens(seg, p_tokens) and matches_tokens(seg, c_tokens):
                return True
    return False


def assess_positive(decision: ModelSemanticDecision, claim: AtomicClaim, selected_spans: list[str]) -> RelationAssessment:
    """Veto a model-positive relation mismatch; never manufacture support."""
    roles = list(dict.fromkeys([*claim_relation_hints(claim.proposition), *decision.claim_relations]))
    if decision.verdict != "SUPPORTED":
        return RelationAssessment(roles, False, False, "Model did not assert support")
    if (decision.relationship_verdict != "ENTAILED" or decision.contradiction_detected
            or decision.uncertainty_detected or decision.evidence_relation in
            {"INSUFFICIENT_RELATION", "CONTRADICTORY_RELATION", "AMBIGUOUS_RELATION"}):
        return RelationAssessment(roles, False, True, "Positive semantic verdict conflicts with structured relation fields")
    if EXPLICIT_OPPOSITION.search(decision.reason) and not re.search(r"\b(?:does not|do not|cannot)\s+contradict", decision.reason, re.I):
        return RelationAssessment(roles, False, True, "Positive verdict explicitly says the evidence contradicts the claim")
    if not selected_spans:
        return RelationAssessment(roles, False, True, "Positive verdict has no selected source spans")
    if LEGACY_CONSTRUCTOR.search(claim.proposition):
        if not (HISTORICAL_QUALIFIER.search(claim.proposition) or HISTORICAL_QUALIFIER.search(claim.sentence)):
            return RelationAssessment(roles, False, False, "Claim asserts legacy constructor-naming behavior without required historical/version qualification (Solidity < 0.4.22)")
    if "ROOT_CAUSE" in roles:
        if decision.evidence_relation not in {"DIRECT_CAUSAL_SUPPORT", "DIRECT_DESCRIPTIVE_SUPPORT"}:
            return RelationAssessment(roles, False, False, "Root-cause claim lacks direct causal evidence relation")
        if not any(DIRECT_CAUSAL.search(span) and not NORMATIVE_START.search(span) for span in selected_spans):
            return RelationAssessment(roles, False, False, "Selected spans provide recommendation or description, not direct causal support for root cause")
    if CAUSAL_CONNECTIVE.search(claim.proposition):
        premise, conclusion = "", ""
        if m := re.search(r"^(?:since|because)\s+(.+?),\s*(.+)$", claim.proposition, re.I):
            premise, conclusion = m.group(1).strip(), m.group(2).strip()
        elif m := re.search(r"^(.+?)\s+(?:because|since)\s+(.+)$", claim.proposition, re.I):
            conclusion, premise = m.group(1).strip(), m.group(2).strip()
        if premise and conclusion:
            is_conclusion_normative = bool(NORMATIVE_START.search(conclusion) or RECOMMENDATION.search(conclusion))
            is_premise_normative = bool(
                NORMATIVE_START.search(premise)
                or re.search(r"\b(?:it is (?:better|recommended)|recommend(?:s|ed)?|should|must|isolate|check|validate|review)\b", premise, re.I)
            )
            is_conclusion_adverse = bool(
                re.search(r"\b(?:fail|failure|vulnerability|risk|DoS|loss|bug|drain|attack|exploit|accidental|deliberate)\b", conclusion, re.I)
            )
            if is_conclusion_normative:
                if is_premise_normative:
                    return RelationAssessment(roles, False, False, "The justification premise for an action must describe a technical concern or mechanism, not another bare recommendation")
            else:
                if is_premise_normative and is_conclusion_adverse:
                    return RelationAssessment(roles, False, False, "A remediation recommendation cannot be asserted as the causal reason for vulnerability occurrence")
                has_causal_span = any(DIRECT_CAUSAL.search(span) and not NORMATIVE_START.search(span) for span in selected_spans)
                if not has_causal_span:
                    return RelationAssessment(roles, False, False, "Selected spans do not provide causal evidence for the asserted relationship")
                bridging_spans = [span for span in selected_spans if DIRECT_CAUSAL.search(span) and not NORMATIVE_START.search(span)]
                if not check_dual_topic_causal_bridging(premise, conclusion, bridging_spans):
                    return RelationAssessment(roles, False, False, "Selected source spans independently support isolated clauses but do not establish the asserted causal relationship between premise and conclusion")
    if INSTRUMENTAL.search(claim.proposition):
        if not any((INSTRUMENTAL.search(span) or (DIRECT_CAUSAL.search(span) and not NORMATIVE_START.search(span))) for span in selected_spans):
            return RelationAssessment(roles, False, False, "Claim asserts an instrumental mechanism ('by ...-ing') not established by the selected source spans")
    if SOURCE_ATTRIBUTION.search(claim.proposition):
        if decision.evidence_relation not in {"DIRECT_RECOMMENDATION", "CONTEXTUAL_SUPPORT"}:
            return RelationAssessment(roles, False, False, "Source recommendation claim lacks a direct recommendation relation")
        if not any(NORMATIVE_START.search(span) or NORMATIVE_EVIDENCE.search(span) for span in selected_spans):
            return RelationAssessment(roles, False, False, "Selected spans describe facts but do not make the attributed recommendation")
    elif "MITIGATION_RECOMMENDATION" in decision.claim_relations:
        if decision.evidence_relation not in {"DIRECT_RECOMMENDATION", "DIRECT_DESCRIPTIVE_SUPPORT", "CONTEXTUAL_SUPPORT"}:
            return RelationAssessment(roles, False, False, "Recommendation claim lacks supporting evidence relation")
    if EFFECTIVENESS.search(claim.proposition) and decision.evidence_relation == "DIRECT_RECOMMENDATION":
        return RelationAssessment(roles, False, False, "A recommendation alone does not establish claimed mitigation effectiveness")
    if "MITIGATION_EFFECTIVENESS" in roles and not any(EFFECTIVENESS.search(span) and not NORMATIVE_START.search(span) for span in selected_spans):
        return RelationAssessment(roles, False, False, "Selected spans do not establish stated mitigation effectiveness")
    if STRONG_CERTAINTY.search(claim.proposition) and not any(STRONG_CERTAINTY.search(span) for span in selected_spans):
        return RelationAssessment(roles, False, False, "Selected spans do not establish the claim's absolute certainty")
    return RelationAssessment(roles, True, False, "Structured relation and selected spans satisfy the conservative relation gate")


def verify_sentence_relation(rel: SentenceRelationRecord, selected_spans: list[str]) -> RelationAssessment:
    """Explicitly verify whole asserted sentence-level causal, instrumental, or teleological relationship."""
    roles: list[ClaimRelation] = ["ROOT_CAUSE"] if rel.relation_type in {"CAUSAL", "ACTION_RATIONALE"} else ["EXECUTION_MECHANISM"]
    if not selected_spans:
        return RelationAssessment(roles, False, True, "No selected source spans provided for sentence relation")

    # Scope and qualification guards
    if (LEGACY_CONSTRUCTOR.search(rel.sentence) or LEGACY_CONSTRUCTOR.search(rel.premise) or LEGACY_CONSTRUCTOR.search(rel.conclusion)):
        if not (HISTORICAL_QUALIFIER.search(rel.sentence) or HISTORICAL_QUALIFIER.search(rel.premise) or HISTORICAL_QUALIFIER.search(rel.conclusion)):
            return RelationAssessment(roles, False, False, "Claim asserts legacy constructor-naming behavior without required historical/version qualification (Solidity < 0.4.22)")

    if STRONG_CERTAINTY.search(rel.sentence) and not any(STRONG_CERTAINTY.search(span) for span in selected_spans):
        return RelationAssessment(roles, False, False, "Selected spans do not establish the claim's absolute certainty")

    if UNIVERSAL_QUANTIFIER.search(rel.sentence) and not any(UNIVERSAL_QUANTIFIER.search(span) for span in selected_spans):
        return RelationAssessment(roles, False, False, "Selected spans do not support universal quantifier scope across all contracts")

    # Substantive token grounding checks
    p_tokens = substantive_relation_tokens(rel.premise)
    c_tokens = substantive_relation_tokens(rel.conclusion)
    if p_tokens and not any(matches_tokens(span, p_tokens) for span in selected_spans):
        return RelationAssessment(roles, False, False, f"The {rel.relation_type.lower()} premise has no substantive evidence in the selected source spans")
    if c_tokens and not any(matches_tokens(span, c_tokens) for span in selected_spans):
        return RelationAssessment(roles, False, False, f"The {rel.relation_type.lower()} conclusion has no substantive evidence in the selected source spans")

    is_conclusion_normative = bool(NORMATIVE_START.search(rel.conclusion) or RECOMMENDATION.search(rel.conclusion))
    is_premise_normative = bool(
        NORMATIVE_START.search(rel.premise)
        or re.search(r"\b(?:it is (?:better|recommended)|recommend(?:s|ed)?|should|must|isolate|check|validate|review)\b", rel.premise, re.I)
    )

    if rel.relation_type == "ACTION_RATIONALE" or (rel.relation_type == "CAUSAL" and is_conclusion_normative):
        if is_premise_normative:
            return RelationAssessment(roles, False, False, "The justification premise for an action must describe a technical concern or mechanism, not another bare recommendation")
        return RelationAssessment(roles, True, False, "Sentence action rationale satisfies conservative relation gate")

    if rel.relation_type == "CAUSAL":
        is_conclusion_adverse = bool(
            re.search(r"\b(?:fail|failure|vulnerability|risk|DoS|loss|bug|drain|attack|exploit|accidental|deliberate)\b", rel.conclusion, re.I)
        )
        if is_premise_normative and is_conclusion_adverse:
            return RelationAssessment(roles, False, False, "A remediation recommendation cannot be asserted as the causal reason for vulnerability occurrence")

        has_causal_span = any(DIRECT_CAUSAL.search(span) and not NORMATIVE_START.search(span) for span in selected_spans)
        if not has_causal_span:
            return RelationAssessment(roles, False, False, "Selected source spans do not provide causal evidence for the asserted relationship")

        bridging_spans = [span for span in selected_spans if DIRECT_CAUSAL.search(span) and not NORMATIVE_START.search(span)]
        if not check_dual_topic_causal_bridging(rel.premise, rel.conclusion, bridging_spans):
            return RelationAssessment(roles, False, False, "Selected source spans independently support isolated clauses but do not establish the asserted causal relationship between premise and conclusion")

    if rel.relation_type == "INSTRUMENTAL":
        has_instrumental = any(
            INSTRUMENTAL.search(span) or DIRECT_CAUSAL.search(span)
            for span in selected_spans
        )
        if not has_instrumental:
            return RelationAssessment(roles, False, False, f"Claim asserts an instrumental mechanism ('by {rel.premise}') not established by the selected source spans")
        bridging_spans = [span for span in selected_spans if INSTRUMENTAL.search(span) or DIRECT_CAUSAL.search(span)]
        if not check_dual_topic_causal_bridging(rel.premise, rel.conclusion, bridging_spans):
            return RelationAssessment(roles, False, False, f"Selected source spans do not connect the instrumental action ('by {rel.premise}') with the stated outcome")

    return RelationAssessment(roles, True, False, "Sentence relation satisfies conservative relation gate")
