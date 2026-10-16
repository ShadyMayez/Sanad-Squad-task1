# Stage 4 / Architecture: LangGraph Integration of Evidence-First V2

**Document ID:** `AUDIT_EVIDENCE_FIRST_V2_04_LANGGRAPH_INTEGRATION`  
**Date:** October 2026  
**System:** SanadSquad V2 Content Generation Engine  
**Status:** IMPLEMENTED AND QUALIFIED  

---

## 1. Executive Summary

In SanadSquad V1 (Closure 07), generation followed an unrestricted model realization path:
```text
Research -> Free-form Writer -> Claim Extraction -> Multi-pass Semantic Verification -> Reviewer -> Visual -> Export
```
This post-hoc extraction architecture suffered from semantic reconstruction divergence, high token consumption (~43.5k tokens/slot), long inference runtimes (~390s/slot), and fragile regex/keyword heuristics attempting to verify arbitrary prose after generation.

Evidence-First V2 integrates directly into the existing LangGraph state-graph architecture, replacing post-hoc claim recovery with an evidence-first factual planning and realization pipeline:
```text
Research / Evidence Lookup
   ↓
Proposition Selection & Sufficiency Preflight
   ↓
Evidence-First Content Plan
   ↓
Deterministic Plan Reference Validation
   ↓
Constrained Natural-Language Writer
   ↓
Plan-to-Text Conformance Verification
   ↓
Business Policy & Brand Validation
   ↓
Reviewer Agent
   ↓
Visual Agent (accepted only)
   ↓
Accepted-Only Export (posts.csv & JSON artifacts)
```

---

## 2. Graph Node Topologies & State Schemas

### 2.1 State Contract (`PieceState`)

The state schema preserves all historical fields required for export compatibility and provenance tracking, extended with typed V2 fields:

```python
class PieceState(TypedDict, total=False):
    slot: Slot
    index: int
    topic: Vulnerability
    topic_id: str
    plan_v2: EvidenceFirstPlan
    conformance_report: ConformanceReport
    business_policy: BusinessPolicy
    draft: Draft
    validation: list[str]
    review: Review
    attempt: int
    drafts: list[Draft]
    validations: list[list[str]]
    reviews: list[Review]
    prompt_tokens: int | None
    completion_tokens: int | None
    usage_measurements_complete: bool
    claims: list[AtomicClaim]
    atomic_claims: list[list[AtomicClaim]]
    sentence_relations: list[list[SentenceRelationRecord]]
    semantic_report: SemanticReport
    semantic_reports: list[SemanticReport]
    verification_latencies_seconds: list[float]
    provenance_errors: list[str]
    extraction_errors: list[str]
    error: str
    result: SlotResult
```

### 2.2 Node Breakdown

1. **`research`**:
   - Uses `EvidenceLookup.select` to resolve the vulnerability topic.
   - Executes `check_evidence_sufficiency(topic_id, slot.type, catalog)`.
   - If distinct factual concepts, mechanisms, consequences, and mitigations are inadequate for the slot type, returns `INSUFFICIENT_EVIDENCE` immediately—preventing expensive hallucination or model calls.

2. **`plan`**:
   - Constructs a typed `EvidenceFirstPlan` with explicit `ContentUnit`s.
   - Enforces slot constraints: exactly 1 unit combining hazard and mitigation for marketing posts; 5–7 units for technical threads.
   - Runs `validate_plan_references(catalog)` deterministically. Any ungrounded proposition ID or relation ID fails closed before invoking the Writer.

3. **`write`**:
   - Executes `EvidenceFirstWriterAgent.run()`.
   - The writer prompt provides the exact canonical text of approved propositions, approved relation edges, required qualifiers, and unit roles.
   - On revision (attempt 2), incorporates targeted feedback only for non-conforming units.
   - Deterministically binds `draft.claims` to the unit's approved evidence IDs, ensuring downstream Reviewer and validation integrity.

4. **`provenance`**:
   - Validates snapshot path, SHA-256 hash, and exact text offsets using `evidence_errors(item)`.

5. **`conformance`**:
   - Calls `verify_plan_conformance(plan, draft.tweets, catalog, model)`.
   - Validates that each tweet truthfully realizes its planned propositions, introduces no extra causal claims or unapproved quantitative data, and preserves modal scope.
   - Generates backward-compatible `AtomicClaim` and `SemanticReport` records for downstream auditability.

6. **`evaluate`**:
   - Executes deterministic checks:
     - `conformance_report.all_conforming`
     - `business_policy.check_hard_policy_compliance()` (approved sources, allowed topics, platform constraints, prohibited categories, mandatory disclaimers)
     - `brand_rules` checks (banned words, banned characters)
     - `provenance_errors`
   - Invokes `ReviewerAgent.run()` with the draft, evidence, and deterministic errors.

7. **`route`**:
   - Pure deterministic edge routing:
     - If `conformance_report.all_conforming`, `review.approved`, `len(validation) == 0`, and `not provenance_errors`: route to `visual`.
     - Else if `attempt < 2`: route to `write` (with targeted unit feedback).
     - Else: route to `drop`.

8. **`visual`**:
   - Invokes `VisualAgent.run()` strictly on accepted content. Produces clean markdown visual layout specifications without rendering heavy raster files.

9. **`drop` & `fail`**:
   - Aggregates structured reasons and records non-nullable `SlotResult`.

---

## 3. Dual-Mode Coexistence (`legacy` vs `evidence_first_v2`)

To ensure zero regression and preserve the historical test baseline, the LangGraph builder supports an explicit `mode` parameter:

```python
def build_week_graph(model, kb, registry, brand_text, brand_rules, mode: str | None = None):
    mode = mode or os.getenv("SANADSQUAD_MODE", "legacy")
    ...
    if mode == "evidence_first_v2":
        piece_app, _ = build_v2_piece_graph(model, kb, lookup, registry, brand_text, brand_rules)
    else:
        piece_app, _ = build_piece_graph(model, kb, lookup, registry, brand_text, brand_rules)
```

- When running existing regression suites (`tests/test_pipeline.py`, `tests/test_relation_integrity.py`, etc.), legacy mode executes unchanged.
- When `--mode evidence_first_v2` is supplied via CLI (`run_week.py` or `run_piece.py`), the evidence-first graph executes.
- Run summaries explicitly log `"pipeline_mode": "evidence_first_v2"` or `"pipeline_mode": "legacy"`.

---

## 4. Targeted Revision Loop

The 1-revision constraint is preserved strictly:
1. If initial generation fails conformance on Unit $U_k$ (e.g. overstating a mitigation into a 100% guarantee):
   - The feedback payload targets only $U_k$:
     ```json
     {
       "unit_id": "piece_1_u4",
       "tweet_index": 3,
       "failing_text": "...",
       "verdict": "SCOPE_VIOLATION",
       "reasons": ["Recommendation overstated as absolute guarantee."],
       "feedback": "Revise unit piece_1_u4 to strictly conform to canonical propositions. Do NOT overstate mitigations as absolute guarantees."
     }
     ```
2. The Writer re-realizes the text while conforming units remain stable.
3. If attempt 2 still fails conformance or hard business policy, the piece is dropped immediately with structured rationale. Uncontrolled retry loops are architecturally impossible.

---

## 5. Test Suite Verification

All 107 existing tests pass cleanly without modifications to historical assertions. 13 new dedicated V2 tests verify:
- Proposition catalog schema and invariant integrity.
- Typed relation constraints and directional typing.
- Sufficiency preflight logic (positive and negative controls).
- Plan generation and reference validation.
- Conformance report generation and honest verdicts.
- Business policy hard validation against all three synthetic profiles.
- Graph state transitions and 1-revision ceiling.
