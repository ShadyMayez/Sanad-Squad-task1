# Deterministic Test Results

## 1. Test Suite Execution Summary

- **Total Automated Tests:** 115 (expanded from 106, 110, and 114)
- **Status:** 115 passed, 0 failed, 0 errors
- **Execution Time:** ~1.70 seconds
- **Test Invariants:** All existing prompt contracts, context quality metrics, pipeline assertions, semantic grounding controls, and independent audit tests remain fully passing.

---

## 2. Test Breakdown by Module

| Test Module | Tests | Status | Focus Area |
| :--- | :---: | :---: | :--- |
| `tests/prompt_quality/test_prompt_contracts.py` | 9 | PASS | Schema, contract, and role isolation tests |
| `tests/test_context_quality.py` | 17 | PASS | Bounded context, truncation flags, byte budgeting |
| `tests/test_pipeline.py` | 25 | PASS | Pipeline flow, graph routing, schema validation |
| `tests/test_relation_integrity.py` | 29 | PASS | Causal inversion, legacy scope, R1-R3, adversarial conditional/purpose/splicing, 4 review probes |
| `tests/test_semantic_grounding.py` | 12 | PASS | Pinned sources, exact quote offsets, SHA-256 checks |
| `audit/tests/test_independent_audit.py` | 23 | PASS | KB integrity, evidence provenance, export gates |
| **Total** | **115** | **PASS** | **100% Suite Passing** |

---

## 3. Dedicated Reproduction & Adversarial Tests

In `tests/test_relation_integrity.py`:
1. `test_reproduction_r1_valid_marketing_rationale_passes`: Confirms valid marketing rationale (SWC-105 access controls) passes deterministic relation check and full export gate.
2. `test_reproduction_r2_missing_relationship_connectors_extracted`: Confirms extraction of `, as `, unpunctuated `since`, `due to`, `resulting in`, and `if / when`.
3. `test_reproduction_r3_unrelated_claims_vetoed_by_deterministic_relation_checker`: Confirms cross-source causal splicing (external call failure -> fund loss) is deterministically vetoed.
4. `test_phase5_balanced_relation_fixtures`: Confirms 8 balanced positive and adverse fixtures covering causal descriptions, legacy constructor scopes, mitigation guarantees, and recommendation paraphrases.
5. `test_conditional_relation_positive_and_negative`: Tests valid low-level call conditional vs alien condition ("flying dinosaurs") and unqualified legacy scope.
6. `test_teleological_purpose_relation_positive_and_negative`: Tests valid access control teleological purpose vs alien goal ("delete backups") and universal guarantee overclaims.
7. `test_combined_but_unlinked_causal_source_paragraph_vetoed`: Tests that a fabricated single span combining distinct true causes across clauses cannot pass causal bridging.
8. `test_expanded_relation_extraction_and_veto_of_unsupported_material_assertions`: Tests that root-cause assertions (REL-11), unqualified legacy constructor exposures (REL-16), and universal mitigation guarantees (REL-17) are extracted and vetoed.
9. `test_closure_06_independent_review_four_probes`: Directly exercises all four specific probes from the Closure 06 Independent Review (purple space toaster, flying dinosaurs, delete backups, spliced dual-topic causal span) and confirms deterministic veto.
