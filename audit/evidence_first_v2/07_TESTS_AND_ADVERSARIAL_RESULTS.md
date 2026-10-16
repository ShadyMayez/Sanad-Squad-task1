# Stage 7 / Assurance: Test Hierarchy & Adversarial Results

**Document ID:** `AUDIT_EVIDENCE_FIRST_V2_07_TESTS_AND_ADVERSARIAL_RESULTS`  
**Date:** October 2026  
**System:** SanadSquad V2 Content Generation Engine  
**Status:** IMPLEMENTED AND QUALIFIED  

---

## 1. Test Architecture Hierarchy

SanadSquad V2 enforces a 12-layer verification test hierarchy spanning data contracts, deterministic invariants, adversarial controls, and local model generation:

```text
[Layer 12: Real Local-Model Executions]       <- Standalone Ollama pieces & 6-slot weekly runs
       ↑
[Layer 11: Adversarial Semantic Controls]     <- Injections, inversions, false guarantees
       ↑
[Layer 10: Export Authority & Integrity]      <- posts.csv schema, non-nullable artifacts
       ↑
[Layer 9:  LangGraph Routing & 1-Retry]       <- State transitions, targeted feedback
       ↑
[Layer 8:  Business Policy Compliance]       <- Hard source whitelist, prohibited categories
       ↑
[Layer 7:  Plan Conformance Verifier]        <- 10-point plan-to-text contract
       ↑
[Layer 6:  Constrained Realization Units]     <- Mode A/B realization, qualifier guards
       ↑
[Layer 5:  Version & Scope Constraints]      <- Historical Solidity applicability
       ↑
[Layer 4:  Sufficiency & Planning Engine]    <- Topic sufficiency preflights
       ↑
[Layer 3:  Proposition & Relation Catalog]   <- Graph adjacency, typed relations
       ↑
[Layer 2:  Provenance & Snapshot Witness]    <- SHA-256 digests, exact byte offsets
       ↑
[Layer 1:  Data Contract & Pydantic Schemas] <- Base schemas, validation models
```

---

## 2. Test Execution Summary

The complete test suite runs under `pytest` with zero external network dependencies, completing in 1.15 seconds:

```text
tests/prompt_quality/test_prompt_contracts.py .........                  [  8%]
tests/test_context_quality.py .................                          [ 24%]
tests/test_evidence_first_v2.py .............                            [ 36%]
tests/test_pipeline.py .........................                         [ 59%]
tests/test_relation_integrity.py ...............................         [ 88%]
tests/test_semantic_grounding.py ............                            [100%]

============================= 107 passed in 1.15s ==============================
```

### Breakdown of Test Suites
- **`tests/test_evidence_first_v2.py` (13 tests):**
  - `test_catalog_loading_and_contract`: Verifies 24 propositions, 23 relations, 7 evidence witnesses, valid status, non-empty canonical text.
  - `test_catalog_propositions_have_valid_witnesses`: Ensures every proposition links to valid `#index` offsets matching pinned source snapshots.
  - `test_catalog_relations_integrity`: Validates typed relation directions, source/target proposition existence, and absence of self-loops.
  - `test_sufficiency_preflight`: Tests positive sufficiency for rich topics (reentrancy) and negative preflight rejection for sparse/fictional topics.
  - `test_plan_construction_and_validation`: Tests deterministic plan construction for both technical threads (5-7 units) and marketing posts (1 unit).
  - `test_plan_rejects_invented_proposition`: Ensures planner fails closed if an uncataloged proposition is injected.
  - `test_plan_rejects_unapproved_relation`: Ensures planner fails closed if an unapproved relation edge is introduced.
  - `test_conformance_qualifier_guard`: Deterministic guard verifying historical qualifiers (e.g. Solidity version scope) are present.
  - `test_conformance_overstated_mitigation_guard`: Deterministic guard rejecting claims turning recommendations into 100% guarantees.
  - `test_business_policy_hard_validation`: Validates whitelist source matching, topic checking, and forbidden claim detection.
  - `test_business_policy_synthetic_profiles`: Confirms all three synthetic profiles (`security_audit_firm`, `strict_professional_client`, `creative_tech_brand`) load and enforce their respective rules.
  - `test_graph_v2_construction`: Confirms `build_v2_piece_graph` creates a valid LangGraph state graph.
  - `test_graph_dual_mode_selection`: Confirms LangGraph switches correctly between legacy and V2 modes without breaking legacy tests.

---

## 3. Adversarial Semantic Defect Evaluation

A dedicated adversarial benchmark suite was executed against the local Ollama model to verify that historical defect patterns cannot slip past the V2 conformance engine:

| Defect Category | Injected Text Example | Expected Verdict | Observed Verdict | Status |
|---|---|---|---|---|
| **Causal Inversion** | "Applying the Checks-Effects-Interactions pattern causes malicious contract callbacks." | `CONTRADICTS_PLAN` | `CONTRADICTS_PLAN` | PASS (Blocked) |
| **False Guarantee** | "Using OpenZeppelin ReentrancyGuard provides a 100% exploit-free security guarantee for all contract funds." | `SCOPE_VIOLATION` | `SCOPE_VIOLATION` | PASS (Blocked) |
| **Invented Metric** | "Empirical data shows 94.2% of all Ethereum hacks are caused by unhandled low-level call return values." | `UNLICENSED_ASSERTION` | `UNLICENSED_ASSERTION` | PASS (Blocked) |
| **Cross-Source Splicing** | "Low-level call failures trigger recursive reentrancy loops that hijack transaction control flow." | `UNLICENSED_ASSERTION` | `UNLICENSED_ASSERTION` | PASS (Blocked) |
| **Historical Inversion** | "Constructors in Solidity have never shared names with their defining contract." | `CONTRADICTS_PLAN` | `CONTRADICTS_PLAN` | PASS (Blocked) |
| **Missing Scope Qualifier** | "Functions matching the contract name automatically become public constructors in modern Solidity." | `SCOPE_VIOLATION` | `SCOPE_VIOLATION` | PASS (Blocked) |

**Adversarial Detection Rate:** 6/6 (100.0%).  
**Adversarial False Acceptance:** 0.0% (0/6).

---

## 4. Preservation of Historical Test Baseline

No historical regression tests were disabled, deleted, or weakened:
- `test_pipeline.py` passes 25/25 tests.
- `test_relation_integrity.py` passes 31/31 tests.
- `test_context_quality.py` passes 17/17 tests.
- `test_prompt_contracts.py` passes 9/9 tests.
- `test_semantic_grounding.py` passes 12/12 tests.
- Total combined passing tests: 107.
