# Historical Archive Index & Evidence Custody

**Directive:** `SANADSQUAD_V2_FINAL_REVIEWABLE_RELEASE_01`  
**Date:** 2026-10-17  
**External Custody Location:** `/home/shady/sandsquad_archive/`  

---

## 1. Archived Handoff Packages (External Custody)

All historical handoff ZIP archives, nested handoffs, and Git bundles have been safely moved to `/home/shady/sandsquad_archive/`. Their SHA-256 digests and contents are recorded below:

| Archive Filename | SHA-256 Checksum | Size (Bytes) | Description |
|---|---|---|---|
| `SANADSQUAD_FINAL_CONTENT_YIELD_CLOSURE_HANDOFF.zip` | `a19d4af6e5be4a663d0ce08f53f68e0fc487b0e307c3fc8e7c4a2fc671fa12f8` | 13,791,274 | Accepted V2 candidate with findings B1 & B2 resolved and updated README. |
| `SANADSQUAD_EVIDENCE_FIRST_V2_REMEDIATED_HANDOFF.zip` | `a19d4af6e5be4a663d0ce08f53f68e0fc487b0e307c3fc8e7c4a2fc671fa12f8` | 13,791,274 | Synchronized mirror of the latest accepted handoff. |
| `SANADSQUAD_EVIDENCE_FIRST_V2_QUALIFIED_HANDOFF.zip` | `9af022fd71eccac7ede97031d38122e7f48ebd9edff9a5872c697d8d60aaa1ac` | 13,105,420 | Baseline Evidence-First V2 qualification archive (5/6 shipped). |
| `SANADSQUAD_FINAL_SHIPPED_CONTENT_INTEGRITY_HANDOFF.zip` | `a0fe5545ce1db8aebf54b6719128cab8f74ba1b450de24817a1182fe2ef04d6e` | 12,987,411 | Sentence-level causal linkage and legacy Solidity qualifier handoff. |
| `SANADSQUAD_FINAL_RELATION_VERIFICATION_HANDOFF.zip` | `3c6246c3f0715325b1af51aae4606250b1f2c80d5f4cb74cc2d7d7e015eda106` | 12,854,129 | Syntactic relation verification milestone handoff. |
| `SANADSQUAD_RECALL_RECOVERY_HANDOFF.zip` | `19186c13cbe16a9639d05c3cd5f755569d4697d99ab51af8336017a32f3b5a13` | 11,452,190 | Recall recovery and context windowing milestone handoff. |
| `SANADSQUAD_RELATION_GROUNDING_HANDOFF.zip` | `2179601b8fdcab1939460055d3594ec08fed5266b204128c3cc6a3c1478a0681` | 11,320,455 | Relation grounding and normative-causal separation handoff. |
| `SANADSQUAD_CONTEXT_QUALITY_HANDOFF.zip` | `dc75b3798fb445c8781211d80800ff0a528acfb5df4de3c4dc2cf65e72210f3e` | 10,876,211 | Context-aware verification milestone handoff. |
| `SANADSQUAD_SEMANTIC_GROUNDING_HANDOFF.zip` | `f487577f997d5b7ddd28be369e9bd3a26ee8ebc17fd564aa6663ec5b35e69136` | 10,214,560 | Initial two-pass semantic verifier handoff. |
| `SANADSQUAD_FINAL_AUDIT.zip` | `4c576505c91099043644f762391d11da3caabb203c795b5c513c72b89d0e4a10` | 9,842,150 | Initial baseline audit package. |
| `SANADSQUAD_HISTORY.bundle` | `3575a76624cd84e47568208e0ae29fd2024c94bb1ae5a1fb58e21e7bfd610738` | 14,892,104 | Complete historical Git commit bundle. |

---

## 2. Archived Historical Run Outputs

All 65+ intermediate diagnostic, benchmark, and qualification run outputs have been moved to `/home/shady/sandsquad_archive/output/`.

The single authoritative V2 sample run retained in the maintained repository is:
- [`output/final-v2-sample/`](../../output/final-v2-sample/) (Byte-identical copy of `output/sanadsquad-final-v2-grounded-week/`, SHA-256 verified via `HASH_MANIFEST.sha256`).
- Historical baseline [`output/sample-week/`](../../output/sample-week/) is preserved for V1 vs V2 auditability.
