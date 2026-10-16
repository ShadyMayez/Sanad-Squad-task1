# Stage 1: Structured Evidence Model Implementation

**Directive ID:** `SANADSQUAD_EVIDENCE_FIRST_V2_IMPLEMENTATION_01`  
**Workspace:** `/home/shady/sandsquad`  
**Date:** 2026-10-16  

---

## 1. Objective & Scope

Stage 1 replaces narrative, unstructured text blobs with a typed Pydantic evidence catalog:
- Versioned factual propositions (`VerifiedProposition`) with explicit epistemic modality, kind, and applicability scopes.
- Typed semantic relationships (`TypedRelation`) with source, target, direction, and evidence span bindings.
- Cryptographic evidence witnesses (`EvidenceWitness`) bound to immutable snapshot files and SHA-256 hashes.

The pilot covers all required pilot domains:
1. **SWC-107** (Reentrancy)
2. **SWC-104** (Unchecked Call Return Value)
3. **SWC-113** (DoS with Failed Call)
4. **SWC-105 & OZ-OWNABLE** (Unprotected Ether Withdrawal & Access Control)
5. **SCWE-028 & OWASP-SC03** (Price Oracle Manipulation)

---

## 2. Artifacts Produced

1. **Schema & Models:** [`content_pipeline/proposition_catalog.py`](file:///home/shady/sandsquad/content_pipeline/proposition_catalog.py)
   - `VerifiedProposition`, `TypedRelation`, `EvidenceWitness`, `PropositionCatalog`
   - Built-in validation method `validate_catalog_integrity(root_dir)` ensuring referential integrity, span bounds, and snapshot SHA-256 verification.
2. **JSON Catalog:** [`knowledge/evidence_first_v2/catalog.json`](file:///home/shady/sandsquad/knowledge/evidence_first_v2/catalog.json)
   - 24 verified propositions
   - 23 typed relations
   - 7 cryptographic evidence witnesses
3. **JSON Schema:** [`knowledge/evidence_first_v2/catalog.schema.json`](file:///home/shady/sandsquad/knowledge/evidence_first_v2/catalog.schema.json)
4. **Detailed Technical Review:** [`knowledge/evidence_first_v2/catalog_review.md`](file:///home/shady/sandsquad/knowledge/evidence_first_v2/catalog_review.md)
   - Full audit trail from each proposition and relation to exact pinned snapshot spans.
   - Explicit `REVIEWED_FOR_PILOT` status.

---

## 3. Stage 1 Acceptance Verification

```python
from content_pipeline.proposition_catalog import load_catalog
catalog = load_catalog()
```

- **Pinned Support:** Every proposition maps to verified span IDs in `source_snapshots/`.
- **Material Relation Witnessing:** Every relation has an explicit evidence witness.
- **No Causal Inversions:** Mitigations link via `MITIGATES` or `ACTION_RATIONALE`, never `CAUSES`.
- **Structured Scope Qualification:** `PROP_SWC105_LEGACY_CONSTRUCTOR` embeds `applicability: {"solidity_version": "<0.4.22"}`.
- **Fail-Closed Verification:** Corrupted span IDs, unknown references, or mismatched hashes fail closed with explicit validation errors.
- **Existing Provenance Intact:** Zero modifications to `content_pipeline/provenance.py` or existing source snapshots.

**STAGE 1 GATE: PASS.**
Cleared to proceed to **Stage 2 (Controlled Architecture Feasibility Experiment)**.
