# Release Cleanup Manifest

**Directive:** `SANADSQUAD_V2_FINAL_REVIEWABLE_RELEASE_01`  
**Execution Date:** 2026-10-17  
**Working Repository:** `/home/shady/sandsquad`  
**External Archive Storage:** `/home/shady/sandsquad_archive/`  
**Git Baseline Commit:** `e6b909d07ae9db7e21459afc0279efa98d8a9814`  

---

## 1. Before vs. After Summary

| Metric | Pre-Cleanup State | Post-Cleanup Maintained Tree | Difference / Reduction |
|---|---|---|---|
| **Total Non-VirtualEnv Disk Size** | 227 MB | ~32 MB | **-195 MB (-86%)** |
| **Root Archive ZIP Files** | 10 ZIP archives (71 MB) | 0 ZIP archives | **100% moved to external archive** |
| **Nested Historical Handoffs** | 2 large trees (~1,258 files) | 0 nested handoffs | **Preserved externally; 0 in repo** |
| **Ephemeral `output/` Folders** | 67 test/diagnostic runs | 2 folders (`final-v2-sample`, `sample-week`) | **65 ephemeral runs archived** |
| **Canonical Six-Slot Sample** | Under variable naming | `output/final-v2-sample/` (25 files) | **Standardized with SHA-256 manifest** |
| **Automated Test Suite** | 170 passing tests | 170 passing tests | **100% parity maintained** |
| **Core Architecture & Gates** | Evidence-First V2 | Evidence-First V2 | **Zero regression; all gates active** |

---

## 2. External Custody Manifest (`/home/shady/sandsquad_archive/`)

Before removing any file from the maintained Git worktree, complete external archives were established with SHA-256 integrity verification:

### Root Historical Archive ZIPs

| Filename | Size (bytes) | SHA-256 Checksum | Contents |
|---|---|---|---|
| `SANADSQUAD_FINAL_CONTENT_YIELD_CLOSURE_HANDOFF.zip` | 13,791,274 | `47ce9240d01c6695375e104ec61efd885f631c3a2c99397b074a0e5ebf00b626` | Final accepted 6/6 baseline submission |
| `SANADSQUAD_EVIDENCE_FIRST_V2_REMEDIATED_HANDOFF.zip` | 13,791,274 | `a19d4af6e5be4a663d0ce08f53f68e0fc487b0e307c3fc8e7c4a2fc671fa12f8` | Initial release candidate with complete run artifacts |
| `SANADSQUAD_EVIDENCE_FIRST_V2_QUALIFIED_HANDOFF.zip` | 14,634,138 | `9af022fd71eccac7ede97031d38122e7f48ebd9edff9a5872c697d8d60aaa1ac` | Baseline qualification run for Evidence-First V2 |
| `SANADSQUAD_FINAL_RELATION_VERIFICATION_HANDOFF.zip` | 4,610,247 | `55ff2b426fe4766156e6d691bfdd5cdf6b1d2cb677443a0d75fc91571b06644e` | Relation grounding qualification archive |
| `SANADSQUAD_RELATION_GROUNDING_HANDOFF.zip` | 5,764,740 | `18c27b33d34105c32822a2c36a312eb77f58965253ecddfb4a6513ed4b3e197e` | Relation grounding baseline suite |
| `SANADSQUAD_FINAL_SHIPPED_CONTENT_INTEGRITY_HANDOFF.zip`| 3,356,202 | `9add9d567bcae2098724c3c4cd850102eeda3152eb4ebebc893ae54e1a49fbd2` | Content integrity handoff |
| `SANADSQUAD_RECALL_RECOVERY_HANDOFF.zip` | 2,527,623 | `f94ba0d0879611b81fa3910c2830f065306ec4a02932fbb4e2f9d6575199bb63` | 28/34 holdout recall benchmark and recovery |
| `SANADSQUAD_CONTEXT_QUALITY_HANDOFF.zip` | 3,400,596 | `b0df57b32c69bc53e5e4faea80373df829140c83a7c644910cf941a54fae8eeb` | Context quality and window bounds audit |
| `SANADSQUAD_SEMANTIC_GROUNDING_HANDOFF.zip` | 6,655,636 | `a8eb2de05ee9fb143c72b22ec647702fef9bcad4600e1291845187e5b3818617` | Semantic grounding benchmark archive |
| `SANADSQUAD_FINAL_AUDIT.zip` | 1,342,846 | `cf79745a3068697669d652934cf5e282cb979f187a716c96894541cb91834ee5` | Initial audit package |

### Preserved Historical Git Bundles & Trees

- `SANADSQUAD_HISTORY.bundle`: Complete Git bundle (SHA-256: `3a4f6be43c3f87b80a7d976be0caeb4a7bfd5a5704bb8427f71f1146244cb3f9`) preserving all historical branches, tags, and commit trees.
- `SANADSQUAD_FINAL_RELATION_VERIFICATION_HANDOFF/`: 1,210 files preserving relation verification audit trials.
- `SANADSQUAD_RECALL_RECOVERY_HANDOFF/`: 48 files preserving negative holdout recall trials.
- `output/`: All 67 historical run directories (e.g., `diagnostic-week*`, `semantic-*`, `evidence-first-v2-*`).

---

## 3. Pruned vs. Maintained Working Tree

### Pruned Elements (Zero Evidence Loss)
1. **Redundant Root ZIPs:** Removed from repository root after verifying external copy.
2. **Nested Extraction Folders:** Removed `SANADSQUAD_FINAL_RELATION_VERIFICATION_HANDOFF/` and `SANADSQUAD_RECALL_RECOVERY_HANDOFF/` from worktree.
3. **Historical Run Folders:** Pruned 65 ephemeral test and diagnostic output folders from `output/`.
4. **Historical Schema Fixture Migration:** The backward-compatibility schema test `test_additive_schema_loads_historical_release_artifact` previously loaded `output/semantic-release-week/semantic_verification.json`. The fixture was safely relocated to `tests/fixtures/semantic_verification_historical.json` to keep `output/` clean without breaking any test.

### Maintained Elements
1. **Source Code (`content_pipeline/`):** Full Evidence-First V2 pipeline with graph orchestration, proposition catalog, relation integrity, business policies, and conformance checks.
2. **Instruction Sets (`instructions/`):** Separate instructions for technical threads, marketing posts, reviewer rubric, semantic verifier, skeptic, and visual agent.
3. **Source Snapshots (`source_snapshots/`):** Pinned authoritative vulnerability references (SWC-104, SWC-105, SWC-107, SWC-113, etc.), third-party licenses, and SHA-256 manifests.
4. **Knowledge Base (`knowledge/` & `kb.json`):** Proposition catalog, relation graphs, and curated vulnerability excerpts.
5. **Canonical Deliverable (`output/final-v2-sample/`):** Complete, independently audited six-slot V2 output folder with CSV (`posts.csv`), 6 visual specs, claims, provenance, review report, semantic verification, summary, and `HASH_MANIFEST.sha256`.
6. **Historical Sample (`output/sample-week/`):** Legacy sample preserved for comparison.
7. **Complete Test Suite (`tests/`, `audit/tests/`):** 170 unit, regression, adversarial, and audit tests.
8. **Senior Review Documentation (`docs/`, root):** Complete engineering evolution, security architecture, reproducibility guide, limitations, and acceptance matrices.

---

## 4. Preservation Invariants

1. **No Evidence Erasure:** Every experiment, negative benchmark (including the 28/34 holdout recall failure), audit finding, and historical draft is preserved in `/home/shady/sandsquad_archive/` and documented in `docs/history/`.
2. **No Silent Git History Rewriting:** Git history is untouched; no `git filter-branch` or force-pushes.
3. **No Unaudited Code Generation:** The maintained repository strictly reflects the accepted Evidence-First V2 implementation.
