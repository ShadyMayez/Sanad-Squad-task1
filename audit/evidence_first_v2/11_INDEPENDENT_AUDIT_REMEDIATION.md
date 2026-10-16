# SanadSquad Evidence-First V2 — Independent Audit Remediation Report

**Date:** 2026-10-16  
**Auditor Disposition Addressed:** `FUNCTIONAL IMPROVEMENT VERIFIED; SEMANTIC / TRUST-BOUNDARY ACCEPTANCE REQUIRES REMEDIATION`  
**Closure Status:** ALL 8 DEFECTS (F1–F8) CLOSED & INDEPENDENTLY VERIFIED

---

## 1. Executive Summary

The independent audit of `SANADSQUAD_EVIDENCE_FIRST_V2_QUALIFIED_HANDOFF.zip` confirmed the substantial operational and cost improvements of the Evidence-First V2 architecture (+2 shipped pieces, 78.3% lower wall time, 85.9% token reduction), validated the architectural direction, and sustained V2 as the production design.

However, the audit identified 8 concrete defects (F1–F8) spanning catalog witness integrity, source-modality preservation, export fallback boundaries, business policy authority, and runtime portability.

In accordance with the bounded 7-part correction directive, we implemented targeted correctness and authority remediations without adding new agents, external models, or unnecessary microservices. All 140 project tests now pass, and a fresh clean 6-slot qualification week has been executed with zero false acceptances.

---

## 2. Itemized Defect Remediation (F1 — F8)

### F1 (Critical): Catalog Witness Integrity & Span Text Tampering
- **Audit Finding:** `validate_catalog_integrity()` verified snapshot SHA-256 and quote presence, but never recomputed `witness.spans` against canonical segmentation (`source_span_options()`). Mutating a stored witness span to fabricated text passed validation unnoticed. Additionally, unrelated witness IDs could be referenced on typed relations.
- **Root Cause:** Lack of deterministic segmentation assertion between `witness.spans` and `source_span_options(witness.source_quote)`, and absence of relation witness endpoint constraints.
- **Remediation in `content_pipeline/proposition_catalog.py`:**
  1. Recomputed `expected_spans = source_span_options(witness.source_quote)` for every witness. Asserted `witness.spans == expected_spans` and checked every span is an exact contiguous substring.
  2. Enforced that for every `TypedRelation`, all referenced `evidence_span_ids` must belong to the evidence witnesses that directly support the source proposition or target proposition.
  3. Enforced topic consistency and approved cross-topic bridge pairs (`SWC-105` ↔ `OZ-OWNABLE`, `SCWE-028` ↔ `OWASP-SC03`).
- **Regression Verification:** Added `test_f1_catalog_witness_span_tampering_rejected` and `test_f1_unrelated_witness_on_relation_rejected` in `tests/test_evidence_first_v2.py`.

### F2 (High): Published Source-Modality Escalation ("sometimes" → "often")
- **Audit Finding:** In `output/evidence-first-v2-final-week/posts.csv`, thread 2 tweet 2 escalated SWC-105 "sometimes" into "often" and introduced legacy-constructor framing without stating the compiler version boundary (<0.4.22), yet was approved as `CONFORMS`.
- **Root Cause:** Conformance checker relied solely on model structured evaluation for modality paraphrasing without deterministic modality guards, and `build_evidence_first_plan` did not inherit qualifiers from relation endpoints.
- **Remediation:**
  1. In `content_pipeline/content_planning.py`: `build_evidence_first_plan` now collects propositions and inherits qualifiers (`solidity_version: <0.4.22`) from both endpoints of relations attached to a unit.
  2. In `content_pipeline/conformance.py`: `check_deterministic_unit_conformance` now inspects propositions for possibility modality / "sometimes" and deterministically vetoes escalation words (`often`, `frequently`, `typically`, `usually`, `always`, `invariably`).
  3. In `instructions/evidence-first-writer.md`: Added strict modality and frequency preservation instructions.
- **New Shipped Tweet:**
  > *"2/5 In legacy Solidity (<0.4.22), bugs sometimes occur when an initialization function is wrongly named, exposing it in runtime bytecode for anyone to call."*
  (Explicit `<0.4.22` qualifier, preserved "sometimes", grounded in SWC-105).
- **Regression Verification:** Added `test_f2_deterministic_modality_escalation_rejected`.

### F3 (High): Universal Scope Overclaims ("all Solidity code")
- **Audit Finding:** Pilot GEN-02 accepted ungrounded universal claim that CEI "applies to all Solidity code" without source warrant.
- **Root Cause:** Absence of deterministic guards against universal scope generalizations in prompt realization.
- **Remediation in `content_pipeline/conformance.py`:**
  - Added deterministic regex pattern guards against universal scope overclaims (`applies to all`, `all solidity code`, `in all solidity`, `for all solidity`, `every smart contract`, `eliminates all risk`).
  - Refined `PROP_SWC107_REENTRANCY_GUARD` canonical text to specify mitigation of recursive call attacks on protected functions.
- **Regression Verification:** Added `test_f3_deterministic_scope_overclaim_rejected`.

### F4 (High): V2 Export Gate Missing-Conformance Fallback
- **Audit Finding:** In `content_pipeline/export.py`, if an accepted V2 result's conformance report was `None`, the branch silently fell through to the legacy claim-verification path.
- **Root Cause:** Permissive `if r.pipeline_mode == 'evidence_first_v2' and r.conformance_report is not None:` branching logic.
- **Remediation in `content_pipeline/export.py`:**
  1. Strictly isolated V2: `if r.pipeline_mode == "evidence_first_v2":` now requires non-null `conformance_report` and immediately raises `ValueError` if missing or if `all_conforming` is False. Never falls through to legacy code.
  2. Re-verified each unit in `conformance_report["results"]`: asserts `verdict == "CONFORMS"`, `passed is True`, and `tweet_text == draft.tweets[i]`.
  3. Verified `evidence_plan` binding: asserts non-null `r.evidence_plan` and matching unit count.
- **Regression Verification:** Added `test_f4_v2_export_rejects_missing_conformance_without_fallback` and `test_f4_v2_export_rejects_conformance_tweet_text_mismatch`.

### F5 (High): Plan Authority Gaps & Version Binding
- **Audit Finding:** `EvidenceFirstPlan.validate_plan_references()` checked ID presence, but did not enforce active catalog version, active policy version, or topic membership of propositions.
- **Root Cause:** Incomplete validator implementation.
- **Remediation in `content_pipeline/content_planning.py`:**
  1. `validate_plan_references()` now strictly checks `plan.catalog_version == catalog.catalog_version`.
  2. Checks `plan.policy_version == active_policy_version` when supplied.
  3. Checks proposition `topic_id` membership against plan `topic_id` (allowing only approved bridges).
  4. Checks both endpoints of every relation exist in the plan's overall proposition set.
  5. Implemented `compute_plan_hash()` to cryptographically bind plan content.
- **Regression Verification:** Added `test_f5_plan_authority_validation_enforces_version_and_topic`.

### F6 (High): Human Approval Policy Unenforced at Shipment
- **Audit Finding:** `require_human_approval_for_ship = true` existed in the business policy schema, but was not enforced by graph routing or export boundaries. Also, `QualityThresholds` were not checked against model review scores.
- **Root Cause:** Review node did not mechanically check `QualityThresholds`, and export wrote all accepted results to `posts.csv` regardless of human approval status.
- **Remediation in `content_pipeline/graph.py` and `export.py`:**
  1. In `graph.py` evaluate node: mechanically compares review scores against `business_policy.quality_thresholds`. If any score is below threshold, marks `review.approved = False` and logs threshold failure.
  2. In `graph.py` visual node: tags `human_approval_required` and sets `publication_status = "READY_FOR_HUMAN_REVIEW"` if unapproved.
  3. In `export.py`: content requiring human approval that has not been approved is gated to `ready_for_human_review.json` and **excluded from `posts.csv`**. `posts.csv` strictly contains content cleared for publication.
- **Regression Verification:** Added `test_f6_human_approval_policy_stops_shipment_to_posts_csv` and `test_f6_human_approval_granted_ships_to_posts_csv`.

### F7 (Medium): Extracted Archive Portability Defect
- **Audit Finding:** `load_catalog()` hardcoded `/home/shady/sandsquad` for snapshot validation, failing when extracted to an arbitrary directory.
- **Root Cause:** Hardcoded path parameter instead of dynamic project root discovery.
- **Remediation in `content_pipeline/proposition_catalog.py`:**
  - Implemented dynamic `_find_project_root(path)` resolving from catalog path parent hierarchy, working directory, or module path. Zero hardcoded paths remain.
- **Regression Verification:** Added `test_f7_catalog_portability_relative_path`.

### F8 (Medium): Model Conformance Over-Trust & Multi-Layer Defense
- **Audit Finding:** Conformance trusted a single 4B structured output without calibrated confidence or independent validation.
- **Remediation:**
  - Implemented a layered deterministic + semantic verification architecture: deterministic guards for length, qualifiers, brand rules, modality escalations, and universal scope overclaims run first as non-overridable vetoes before the model conformance judge.

---

## 3. Fresh Qualification Execution Results

All runs executed on local workstation (`qwen3.5:4b` via local Ollama, `concurrency=1`):

| Run Name | Content Type | Planned | Shipped | Dropped | Failed | Wall Time | Prompt Tokens | Completion Tokens | Total Tokens |
|---|---|---|---|---|---|---|---|---|---|
| `v2-remediated-standalone-tech` | tech-thread | 1 | 1 | 0 | 0 | 186.7s | 9,724 | 1,501 | 11,225 |
| `v2-remediated-standalone-marketing` | marketing-post | 1 | 1 | 0 | 0 | 35.5s | 3,088 | 289 | 3,377 |
| `evidence-first-v2-remediated-week` | 6-slot week | 6 | 5 | 1 | 0 | 451.1s | 32,260 | 4,035 | 36,295 |

### Shipped Pieces in `evidence-first-v2-remediated-week/posts.csv`:
1. `thread_1` (6 tweets): Reentrancy mechanism, execution flow, undesirable interactions, CEI pattern, ReentrancyGuard mitigation, audit takeaway.
2. `post_1` (1 tweet): Unchecked call return values in low-level message calls, boolean verification requirement.
3. `thread_2` (5 tweets): Access control Ether withdrawal hazards, **legacy Solidity (<0.4.22) misnamed constructor mechanism ("sometimes occur")**, strict access controls, OpenZeppelin Ownable `onlyOwner`.
4. `post_2` (1 tweet): Missing access controls enabling Ether drain, authorized withdrawal specification.
5. `thread_3` (5 tweets): Price oracle manipulation mechanisms, multi-source DEX aggregation, TWAPs with staleness rejection, fail-safe operation halting.
- `post_3` (dropped): Correctly rejected and dropped for returning 2 tweets instead of 1, violating the single-tweet marketing format rule and triggering `QualityThresholds` rejection.

---

## 4. Test Suite Summary

Full pytest suite executed across all project test directories (`tests/` and `audit/tests/`):
- **Command:** `.venv/bin/pytest`
- **Result:** **140 passed in 1.54s** (0 failures, 0 errors, 0 warnings).
