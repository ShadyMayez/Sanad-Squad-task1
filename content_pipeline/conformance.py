"""Plan-to-text conformance verification for Evidence-First V2.

Verifies that realized text faithfully expresses the planned propositions and typed
relations without adding unapproved factual assertions, reversing causal direction,
or dropping required qualifiers.
"""
from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Literal
from pydantic import BaseModel, Field
from langchain_core.messages import SystemMessage, HumanMessage

from .content_planning import EvidenceFirstPlan, ContentUnit
from .proposition_catalog import PropositionCatalog, VerifiedProposition, TypedRelation
from .config import load_brand, ROOT

ConformanceVerdict = Literal[
    "CONFORMS",
    "UNLICENSED_ASSERTION",
    "SCOPE_VIOLATION",
    "CONTRADICTS_PLAN",
    "INSUFFICIENT_EVIDENCE",
    "ABSTAIN",
    "VERIFICATION_ERROR"
]


class UnitConformanceResult(BaseModel):
    unit_id: str
    tweet_text: str
    verdict: ConformanceVerdict
    passed: bool
    reason: str
    missing_qualifiers: list[str] = Field(default_factory=list)
    unlicensed_statements: list[str] = Field(default_factory=list)
    brand_violations: list[str] = Field(default_factory=list)


class ConformanceReport(BaseModel):
    slot_id: str
    all_conforming: bool
    results: list[UnitConformanceResult]
    total_units: int
    conforming_units: int
    failure_summary: str = ""


class ModelConformanceDecision(BaseModel):
    verdict: ConformanceVerdict
    reason: str
    meaning_preserved: bool
    extra_unlicensed_facts_detected: bool
    causal_direction_reversed: bool
    mitigation_overstated_as_guarantee: bool
    unsupported_outcomes_or_severity_detected: bool = Field(
        default=False,
        description="True if text introduces unapproved consequences/harms (e.g. draining funds when only DoS is approved), unapproved severity modifiers (e.g. 'significant', 'complete subversion'), or unapproved rankings (e.g. 'primary defense')."
    )
    confidence: float = 1.0


def check_deterministic_unit_conformance(
    unit: ContentUnit,
    tweet_text: str,
    brand_path: str = "brand-voice.md",
    catalog: PropositionCatalog | None = None,
) -> tuple[bool, list[str]]:
    """Enforce non-overridable deterministic constraints: qualifiers, length, brand, modality, and scope."""
    violations: list[str] = []

    # 1. Length check
    if len(tweet_text) > unit.max_chars:
        violations.append(f"Character limit exceeded: {len(tweet_text)} > {unit.max_chars}")

    # 2. Required qualifiers (e.g. Solidity version threshold)
    for q in unit.required_qualifiers:
        q_norm = re.sub(r"\s+", "", q.lower())
        text_norm = re.sub(r"\s+", "", tweet_text.lower())
        if q_norm not in text_norm:
            # Check flexible phrasing
            if "0.4.22" in q and not ("0.4.22" in tweet_text and ("<" in tweet_text or "prior" in tweet_text.lower() or "before" in tweet_text.lower() or "legacy" in tweet_text.lower())):
                violations.append(f"Missing mandatory qualifier: {q}")

    # 3. Scope overclaim check (e.g. universal claims)
    universal_scope_patterns = [
        (re.compile(r"\bapplies to all\b", re.IGNORECASE), "applies to all"),
        (re.compile(r"\ball solidity code\b", re.IGNORECASE), "all Solidity code"),
        (re.compile(r"\bin all solidity\b", re.IGNORECASE), "in all Solidity"),
        (re.compile(r"\bfor all solidity\b", re.IGNORECASE), "for all Solidity"),
        (re.compile(r"\bevery smart contract\b", re.IGNORECASE), "every smart contract"),
        (re.compile(r"\ball smart contracts\b", re.IGNORECASE), "all smart contracts"),
        (re.compile(r"\beliminates all risk\b", re.IGNORECASE), "eliminates all risk"),
        (re.compile(r"\bprevents all\b", re.IGNORECASE), "prevents all"),
        (re.compile(r"\bfor all (?:external\s+)?calls\b", re.IGNORECASE), "for all external calls"),
        (re.compile(r"\bacross all (?:external\s+)?calls\b", re.IGNORECASE), "across all external calls"),
        (re.compile(r"\bon all (?:external\s+)?calls\b", re.IGNORECASE), "on all external calls"),
    ]
    for pattern, name in universal_scope_patterns:
        if pattern.search(tweet_text):
            violations.append(f"Scope overclaim: ungrounded universal scope assertion ({name!r})")

    # 4. Epistemic modality and frequency escalation check
    has_possibility_modality = False
    if catalog:
        prop_map = {p.id: p for p in catalog.propositions}
        for pid in unit.proposition_ids:
            if pid in prop_map:
                p = prop_map[pid]
                if p.modality == "possibility" or "sometimes" in p.canonical_text.lower():
                    has_possibility_modality = True
                    break
    if has_possibility_modality:
        escalation_patterns = [
            (re.compile(r"\boften\b", re.IGNORECASE), "often"),
            (re.compile(r"\bfrequently\b", re.IGNORECASE), "frequently"),
            (re.compile(r"\btypically\b", re.IGNORECASE), "typically"),
            (re.compile(r"\busually\b", re.IGNORECASE), "usually"),
            (re.compile(r"\balways\b", re.IGNORECASE), "always"),
            (re.compile(r"\binvariably\b", re.IGNORECASE), "invariably"),
        ]
        for pattern, word in escalation_patterns:
            if pattern.search(tweet_text):
                violations.append(
                    f"Modality escalation: proposition specifies possibility/sometimes, but tweet text escalates to {word!r}"
                )

    # 5. Cross-topic concept contamination check
    topic_signatures = {
        "access_control": {
            "allowed_topics": {"SWC-105", "OZ-OWNABLE", "access control", "withdrawal", "ether withdrawal"},
            "patterns": [
                (re.compile(r"\binitialization (?:logic|functions?)\b", re.IGNORECASE), "initialization logic/functions"),
                (re.compile(r"\blegacy constructors?\b", re.IGNORECASE), "legacy constructors"),
                (re.compile(r"\bownable\b", re.IGNORECASE), "Ownable"),
                (re.compile(r"\bonlyowner\b", re.IGNORECASE), "onlyOwner"),
            ],
        },
        "oracle_manipulation": {
            "allowed_topics": {"SCWE-028", "OWASP-SC03", "oracle manipulation", "price oracle"},
            "patterns": [
                (re.compile(r"\bprice oracles?\b", re.IGNORECASE), "price oracle"),
                (re.compile(r"\boracle manipulations?\b", re.IGNORECASE), "oracle manipulation"),
                (re.compile(r"\btwaps?\b", re.IGNORECASE), "TWAP"),
                (re.compile(r"\boutlier deviations?\b", re.IGNORECASE), "outlier deviation"),
            ],
        },
        "reentrancy": {
            "allowed_topics": {"SWC-107", "reentrancy"},
            "patterns": [
                (re.compile(r"\breentranc(?:y|t)\b", re.IGNORECASE), "reentrancy"),
                (re.compile(r"\brecursive callbacks?\b", re.IGNORECASE), "recursive callback"),
                (re.compile(r"\bchecks-effects-interactions\b", re.IGNORECASE), "Checks-Effects-Interactions"),
                (re.compile(r"\breentrancyguard\b", re.IGNORECASE), "ReentrancyGuard"),
            ],
        },
    }

    if catalog and unit.proposition_ids:
        prop_map = {p.id: p for p in catalog.propositions}
        unit_topics = {prop_map[pid].topic_id for pid in unit.proposition_ids if pid in prop_map}
        for domain, domain_spec in topic_signatures.items():
            allowed = domain_spec["allowed_topics"]
            if not any(t in allowed for t in unit_topics):
                for pat, concept_name in domain_spec["patterns"]:
                    if pat.search(tweet_text):
                        violations.append(
                            f"Unlicensed cross-topic concept: {concept_name!r} from {domain} imported into {sorted(unit_topics)}"
                        )

    # 6. Unlicensed comparative ranking / exclusivity check
    ranking_patterns = [
        (re.compile(r"\b(?:the\s+)?primary\s+(?:defense|remediation|mitigation|safeguard|measure|protection)\b", re.IGNORECASE), "primary defense/mitigation"),
        (re.compile(r"\bthe\s+most\s+(?:critical|important|effective)\s+(?:defense|remediation|mitigation|safeguard|protection)\b", re.IGNORECASE), "most critical/important defense"),
        (re.compile(r"\b(?:the\s+)?sole\s+(?:defense|protection|safeguard|mitigation)\b", re.IGNORECASE), "sole defense"),
    ]
    ranking_approved = False
    if catalog:
        prop_map = {p.id: p for p in catalog.propositions}
        for pid in unit.proposition_ids:
            if pid in prop_map:
                c_text = prop_map[pid].canonical_text.lower()
                if any(w in c_text for w in ["primary", "sole", "most important", "most critical"]):
                    ranking_approved = True
                    break
    if not ranking_approved:
        for pattern, name in ranking_patterns:
            if pattern.search(tweet_text):
                violations.append(
                    f"Unlicensed comparative ranking: text asserts {name!r} without proposition support"
                )

    # 7. Unlicensed hyperbolic severity / complete subversion check
    hyperbolic_patterns = [
        (re.compile(r"\bcomplete\s+subversion\b", re.IGNORECASE), "complete subversion"),
        (re.compile(r"\btotal\s+(?:subversion|destruction|collapse)\b", re.IGNORECASE), "total subversion/destruction"),
        (re.compile(r"\bcatastrophic\s+(?:subversion|collapse|destruction)\b", re.IGNORECASE), "catastrophic collapse/destruction"),
        (re.compile(r"\bsignificant\s+fund\s+losses?\b", re.IGNORECASE), "significant fund loss"),
    ]
    hyperbolic_approved = False
    if catalog:
        prop_map = {p.id: p for p in catalog.propositions}
        for pid in unit.proposition_ids:
            if pid in prop_map:
                c_text = prop_map[pid].canonical_text.lower()
                if any(w in c_text for w in ["complete subversion", "total destruction", "catastrophic", "significant fund"]):
                    hyperbolic_approved = True
                    break
    if not hyperbolic_approved:
        for pattern, name in hyperbolic_patterns:
            if pattern.search(tweet_text):
                violations.append(
                    f"Unlicensed severity escalation: text asserts {name!r} without proposition support"
                )

    # 8. Unlicensed financial outcome / fund drainage check
    fund_loss_approved = False
    if catalog:
        prop_map = {p.id: p for p in catalog.propositions}
        for pid in unit.proposition_ids:
            if pid in prop_map:
                c_text = prop_map[pid].canonical_text.lower()
                if any(w in c_text for w in ["drain", "loss of funds", "withdraw ether", "drain ether"]):
                    fund_loss_approved = True
                    break
    if not fund_loss_approved:
        fund_loss_patterns = [
            (re.compile(r"\bdrain(?:ing|s)?\s+funds?\b", re.IGNORECASE), "draining funds"),
            (re.compile(r"\bsteal(?:ing)?\s+funds?\b", re.IGNORECASE), "stealing funds"),
            (re.compile(r"\bfund\s+drainage\b", re.IGNORECASE), "fund drainage"),
            (re.compile(r"\bloss\s+of\s+funds?\b", re.IGNORECASE), "loss of funds"),
        ]
        for pattern, name in fund_loss_patterns:
            if pattern.search(tweet_text):
                violations.append(
                    f"Unlicensed consequence: text asserts {name!r} but approved unit propositions do not license financial loss/drainage"
                )

    # 9. Topic-specific scope and instrumental outcome checks
    if catalog and unit.proposition_ids:
        prop_map = {p.id: p for p in catalog.propositions}
        unit_topics = {prop_map[pid].topic_id for pid in unit.proposition_ids if pid in prop_map}
        # SWC-104: checking return values is strictly scoped to low-level calls, not universal external calls
        if "SWC-104" in unit_topics:
            if re.search(r"\ball\s+(?:external\s+)?calls\b", tweet_text, re.IGNORECASE):
                violations.append("Scope overclaim: return value verification in SWC-104 is scoped to low-level calls, not 'all external calls'")
        # SWC-113: recipient call isolation minimizes DoS damage/impact; does not license stopping/preventing execution continuation
        if "SWC-113" in unit_topics:
            if re.search(r"\b(?:prevent|stop|halt)\s+(?:execution\s+from\s+continuing|program\s+execution|execution\s+continuing|continuing\s+on\s+failure)\b", tweet_text, re.IGNORECASE) or re.search(r"\bto\s+prevent\s+execution\s+from\s+continuing\b", tweet_text, re.IGNORECASE):
                violations.append("Unlicensed instrumental mechanism: SWC-113 isolation minimizes damage/DoS impact from failures; it does not license asserting that isolation 'prevents execution from continuing on failure' (SWC-104 mechanism)")

    # 10. Brand rules check
    try:
        _, brand = load_brand(Path(brand_path) if not Path(brand_path).is_absolute() else brand_path)
        for char in brand.banned_characters:
            if char in tweet_text:
                violations.append(f"Brand violation: banned character {char!r}")
        if brand.forbid_hashtags and re.search(r"(?<!\w)#[\w]+", tweet_text):
            violations.append("Brand violation: hashtag detected")
        for word in brand.banned_words:
            if re.search(re.escape(word), tweet_text, flags=re.IGNORECASE):
                violations.append(f"Brand violation: banned phrase {word!r}")
    except Exception as exc:
        violations.append(f"Brand check failure: {exc}")

    return (len(violations) == 0, violations)


CONFORMANCE_INSTRUCTION = """You are an expert, skeptical Plan-to-Text Conformance Verifier for smart contract security content.
Your task is to evaluate whether the generated tweet text faithfully realizes the assigned content plan units without adding unapproved technical facts, reversing causal mechanisms, escalating epistemic modality/frequency, importing foreign vulnerability concepts, adding unapproved consequences or harms, adding unapproved severity/intensity modifiers, or inventing comparative rankings.

Input contains:
1. Target Content Unit (role, required qualifiers).
2. Approved Canonical Propositions that this tweet is licensed to express.
3. Approved Typed Relations between those propositions.
4. The generated tweet text.

Decision Rules:
1. CONFORMS: The text faithfully expresses ONLY the meaning of the planned propositions and relations. Paraphrasing for readability, style, and flow is permitted ONLY IF:
   - Factual claims, mechanisms, and consequences strictly match the approved propositions.
   - NO unapproved consequences or harms are introduced (e.g. claiming "draining funds" or "financial loss" when approved propositions only establish execution failure or denial-of-service).
   - NO unapproved severity modifiers or intensity escalations are introduced (e.g. claiming "significant fund losses" or "complete subversion" when approved propositions state "loss of funds" or "exploitation of contract logic").
   - NO unapproved comparative rankings, exclusivity, or priority claims are introduced (e.g. asserting a mitigation is "the primary defense", "the most important safeguard", or "the sole protection" when approved propositions state it as a recommended safeguard).
   - Epistemic modalities (possibility vs certainty) and causal directions are strictly preserved.
2. SCOPE_VIOLATION: The text asserts claims outside the approved applicability scope, makes ungrounded universal claims (e.g. 'applies to all Solidity code'), or omits mandatory version boundaries (e.g. legacy Solidity < 0.4.22).
3. UNLICENSED_ASSERTION: The text introduces:
   - Any new, unapproved technical mechanisms, outcomes, or consequences (e.g. inventing fund drainage/theft, stolen assets, or new attack vectors not in the approved propositions).
   - Any unapproved severity adjectives, degree escalations, or superlatives (e.g. "complete subversion", "significant losses", "total destruction").
   - Any unapproved comparative rankings or exclusivity (e.g. "the primary defense", "the main measure", "the only way").
   - Foreign vulnerability concepts not in the approved plan.
   NEVER treat an unapproved harm, severity modifier, comparative ranking, or technical concept as "valid elaboration" or "domain-plausible context". If it is not in the approved propositions or relations, it MUST be rejected.
4. CONTRADICTS_PLAN: The text contradicts an approved proposition, escalates epistemic modality or frequency (e.g. strengthening 'sometimes' to 'often', 'typically', or 'always'), or inverts a causal direction (e.g. claiming a recommendation caused a vulnerability, or claiming a mitigation completely eliminates all risk).
5. INSUFFICIENT_EVIDENCE: The text fails to express the substantive core meaning of the assigned propositions.
6. ABSTAIN: If evidence is missing to evaluate an added assertion.

Output MUST be a single ModelConformanceDecision JSON object."""


async def verify_unit_conformance_semantic(
    unit: ContentUnit,
    tweet_text: str,
    catalog: PropositionCatalog,
    model,
) -> UnitConformanceResult:
    """Evaluate plan-to-text conformance using deterministic guards + bounded LLM verification."""
    # 1. Deterministic check
    det_passed, det_violations = check_deterministic_unit_conformance(unit, tweet_text, catalog=catalog)
    if not det_passed:
        has_qualifier_or_scope_error = any(
            ("Missing mandatory qualifier" in v or "Scope overclaim" in v) for v in det_violations
        )
        has_modality_error = any("Modality escalation" in v for v in det_violations)
        if has_modality_error:
            verdict: ConformanceVerdict = "CONTRADICTS_PLAN"
        elif has_qualifier_or_scope_error:
            verdict = "SCOPE_VIOLATION"
        else:
            verdict = "UNLICENSED_ASSERTION"

        return UnitConformanceResult(
            unit_id=unit.id,
            tweet_text=tweet_text,
            verdict=verdict,
            passed=False,
            reason="; ".join(det_violations),
            brand_violations=[v for v in det_violations if "Brand violation" in v],
            missing_qualifiers=[v for v in det_violations if "Missing mandatory qualifier" in v],
        )

    # 2. Gather approved propositions and relations for this unit
    if not unit.proposition_ids and unit.source_evidence_ids:
        return UnitConformanceResult(
            unit_id=unit.id,
            tweet_text=tweet_text,
            verdict="CONFORMS",
            passed=True,
            reason="Unit conforms to verified research evidence and deterministic constraints.",
        )

    prop_map = {p.id: p for p in catalog.propositions}
    rel_map = {r.id: r for r in catalog.relations}

    unit_props = [prop_map[pid] for pid in unit.proposition_ids if pid in prop_map]
    unit_rels = [rel_map[rid] for rid in unit.relation_ids if rid in rel_map]

    payload = {
        "unit_id": unit.id,
        "role": unit.role,
        "required_qualifiers": unit.required_qualifiers,
        "approved_propositions": [
            {"id": p.id, "kind": p.kind, "canonical_text": p.canonical_text, "applicability": p.applicability}
            for p in unit_props
        ],
        "approved_relations": [
            {"id": r.id, "type": r.relation_type, "source": r.source_id, "target": r.target_id}
            for r in unit_rels
        ],
        "tweet_text": tweet_text,
    }

    try:
        decision, _ = await model.structured(
            [
                SystemMessage(content=CONFORMANCE_INSTRUCTION),
                HumanMessage(content=json.dumps(payload, ensure_ascii=False)),
            ],
            ModelConformanceDecision,
        )
        if not isinstance(decision, ModelConformanceDecision):
            decision = ModelConformanceDecision.model_validate(decision)

        passed = (
            decision.verdict == "CONFORMS"
            and decision.meaning_preserved
            and not decision.extra_unlicensed_facts_detected
            and not decision.causal_direction_reversed
            and not decision.mitigation_overstated_as_guarantee
            and not getattr(decision, "unsupported_outcomes_or_severity_detected", False)
        )

        effective_verdict = decision.verdict if passed else (
            "CONTRADICTS_PLAN" if decision.causal_direction_reversed or decision.mitigation_overstated_as_guarantee
            else ("UNLICENSED_ASSERTION" if (decision.extra_unlicensed_facts_detected or getattr(decision, "unsupported_outcomes_or_severity_detected", False)) else decision.verdict)
        )

        return UnitConformanceResult(
            unit_id=unit.id,
            tweet_text=tweet_text,
            verdict=effective_verdict,
            passed=passed,
            reason=decision.reason,
        )
    except Exception as exc:
        return UnitConformanceResult(
            unit_id=unit.id,
            tweet_text=tweet_text,
            verdict="VERIFICATION_ERROR",
            passed=False,
            reason=f"Model conformance verification failed: {type(exc).__name__}: {exc}",
        )


async def verify_plan_conformance(
    plan: EvidenceFirstPlan,
    tweets: list[str],
    catalog: PropositionCatalog,
    model,
) -> ConformanceReport:
    """Verify all units in a plan against the generated tweets."""
    results: list[UnitConformanceResult] = []

    if len(tweets) != len(plan.units):
        # Mismatch in unit count
        return ConformanceReport(
            slot_id=plan.slot_id,
            all_conforming=False,
            results=[
                UnitConformanceResult(
                    unit_id=plan.units[0].id if plan.units else "u0",
                    tweet_text="",
                    verdict="CONTRADICTS_PLAN",
                    passed=False,
                    reason=f"Plan unit count mismatch: expected {len(plan.units)} tweets, received {len(tweets)} tweets.",
                )
            ],
            total_units=len(plan.units),
            conforming_units=0,
            failure_summary=f"Expected {len(plan.units)} tweets, got {len(tweets)}",
        )

    for unit, tweet in zip(plan.units, tweets):
        res = await verify_unit_conformance_semantic(unit, tweet, catalog, model)
        results.append(res)

    conforming_count = sum(r.passed for r in results)
    all_conforming = (conforming_count == len(results))

    failure_reasons = [f"[{r.unit_id}] {r.verdict}: {r.reason}" for r in results if not r.passed]

    return ConformanceReport(
        slot_id=plan.slot_id,
        all_conforming=all_conforming,
        results=results,
        total_units=len(plan.units),
        conforming_units=conforming_count,
        failure_summary="; ".join(failure_reasons),
    )
