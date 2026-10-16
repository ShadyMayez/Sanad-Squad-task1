# Pre-Cleanup Forensic Inventory

**Directive:** `SANADSQUAD_V2_FINAL_REVIEWABLE_RELEASE_01`  
**Date:** 2026-10-17  
**Working Repository:** `/home/shady/sandsquad`  
**Git Baseline Commit:** `e6b909d07ae9db7e21459afc0279efa98d8a9814` (branch `codex/semantic-grounding`)  
**External Custody Location:** `/home/shady/sandsquad_archive/`  

---

## 1. Forensic Baseline & Checksum Verification

Before performing repository hygiene or moving files, the baseline state was inventoried and verified against the input handoff specifications:

| Asset | Verification Check | Baseline Measurement | Status |
|---|---|---|---|
| Hand-off Candidate ZIP | SHA-256 Checksum | `a19d4af6e5be4a663d0ce08f53f68e0fc487b0e307c3fc8e7c4a2fc671fa12f8` | VERIFIED |
| Input Handoff Candidate (2) | SHA-256 Checksum | `55ff2b426fe4766156e6d691bfdd5cdf6b1d2cb677443a0d75fc91571b06644e` | VERIFIED (in archive) |
| Input Handoff Candidate (3) | SHA-256 Checksum | `47ce9240d01c6695375e104ec61efd885f631c3a2c99397b074a0e5ebf00b626` | VERIFIED (in archive) |
| Automated Test Suite | `.venv/bin/pytest tests/ audit/tests/` | 170 passed in 1.81s | VERIFIED |
| Python Compilation | `python -m compileall -q` | 0 syntax or import errors | VERIFIED |
| Catalog Integrity | `load_catalog().validate_catalog_integrity()` | 24 propositions, 23 relations, 7 witnesses, 0 errors | VERIFIED |
| Output Deliverable | `output/sanadsquad-final-v2-grounded-week/` | 6 planned, 6 shipped, 0 dropped, 0 failed; 383.9s | VERIFIED |
| Initial Disk Usage | `du -sh .` | 227 MB (including nested handoffs and 67 run folders) | VERIFIED |

---

## 2. Inventory Classification Matrix

Every path present in the pre-cleanup worktree is classified under one of seven immutable categories:
1. `ACTIVE` — Retained in maintained repository for build, test, and runtime.
2. `CANONICAL_SAMPLE` — Retained in maintained repository under `output/final-v2-sample/` as the single auditable V2 run.
3. `REVIEW_DOCUMENTATION` — Retained in maintained repository under `docs/` and root for senior engineering audit.
4. `HISTORICAL_ARCHIVE` — Moved to external storage (`/home/shady/sandsquad_archive/`) and tracked in `docs/history/`.
5. `GENERATED` — Ephemeral test/run output pruned from the maintained working tree.
6. `SECRET_OR_UNSAFE` — Scanned; none found.
7. `UNKNOWN` — None. (All paths identified and categorized).

### Classification Table

| Path / Pattern | Pre-Cleanup State | Classification | Action / Destination | Rationale |
|---|---|---|---|---|
| `content_pipeline/` | Tracked + Untracked V2 additions | `ACTIVE` | Retained | Core pipeline source code (LangGraph, agents, schemas, validation, conformance). |
| `knowledge/evidence_first_v2/` | Untracked V2 catalog & policies | `ACTIVE` | Retained | V2 proposition catalog (`catalog.json`) and versioned policy templates. |
| `source_snapshots/` | Tracked + `OZ-OWNABLE.txt` | `ACTIVE` | Retained | Pinned evidence snapshots, checksums, and third-party licenses (SWC & OWASP). |
| `instructions/` | Tracked + `evidence-first-writer.md` | `ACTIVE` | Retained | Specialized writer instructions (`tech-thread.md`, `marketing-post.md`), reviewer rubric, verifier, skeptic. |
| `skills/` | Tracked | `ACTIVE` | Retained | Shared evidence lookup skill (`skills/evidence-lookup.md`). |
| `schemas/` | Tracked | `ACTIVE` | Retained | JSON schema definitions for drafts, reviews, claims, accepted content. |
| `tests/` | Tracked + V2 test additions | `ACTIVE` | Retained | Core unit and regression test suite (147 tests). |
| `audit/tests/` | Tracked | `ACTIVE` | Retained | Independent adversarial audit test suite (23 tests). |
| `brand-voice.md` | Tracked | `ACTIVE` | Retained | Editable brand rules, allowed links, approved statistics. |
| `kb.json` | Tracked | `ACTIVE` | Retained | Curated knowledge base with 17 pinned vulnerabilities and excerpts. |
| `plan.json` | Tracked | `ACTIVE` | Retained | Six-slot weekly assignment content plan (3 threads, 3 posts). |
| `content-types.json` | Tracked | `ACTIVE` | Retained | Content type registry mapping `tech-thread` and `marketing-post`. |
| `run_week.py`, `run_piece.py` | Tracked | `ACTIVE` | Retained | CLI entrypoints for weekly orchestration and standalone piece execution. |
| `pyproject.toml`, `requirements.txt` | Tracked / Untracked | `ACTIVE` | Retained | Python packaging and dependency declarations. |
| `pytest.ini` | Tracked | `ACTIVE` | Retained | Pytest configuration. |
| `.env.example`, `.gitignore` | Tracked | `ACTIVE` | Retained | Environment templates and Git ignore rules. |
| `output/final-v2-sample/` | Mechanically verified copy | `CANONICAL_SAMPLE` | Retained in repo | Single canonical six-slot V2 output folder with CSV, 6 visual specs, telemetry, and hash manifest. |
| `output/sanadsquad-final-v2-grounded-week/` | Generated run folder | `CANONICAL_SAMPLE` | Copied to `final-v2-sample` | Baseline 6/6 run; preserved in external archive. |
| `output/sample-week/` | Historical V1 sample | `HISTORICAL_ARCHIVE` | Preserved in archive/git | Historical V1 baseline run. |
| `output/diagnostic-*` (11 dirs) | Ephemeral run folders | `GENERATED` | Backed up & pruned | Early diagnostic runs. |
| `output/semantic-*` (15 dirs) | Ephemeral run folders | `GENERATED` | Backed up & pruned | Intermediate semantic closure runs. |
| `output/qual-*` (8 dirs) | Ephemeral run folders | `GENERATED` | Backed up & pruned | Standalone qualification runs. |
| `output/run-*` (2 dirs) | Ephemeral run folders | `GENERATED` | Backed up & pruned | CLI override test runs. |
| `output/evidence-first-v2-*` (5 dirs) | Ephemeral run folders | `GENERATED` | Backed up & pruned | V2 iteration runs. |
| `output/relation-*`, `recall-*` | Ephemeral run folders | `GENERATED` | Backed up & pruned | Intermediate milestone runs. |
| `SANADSQUAD_*.zip` (10 files) | Root handoff ZIP archives | `HISTORICAL_ARCHIVE` | Moved to external archive | Intermediate release ZIPs (backed up with SHA-256). |
| `SANADSQUAD_HISTORY.bundle` | Git bundle archive | `HISTORICAL_ARCHIVE` | Moved to external archive | Historical Git bundle. |
| `SANADSQUAD_FINAL_RELATION_VERIFICATION_HANDOFF/` | Nested handoff copy | `HISTORICAL_ARCHIVE` | Moved to external archive | Recursive unpacked copy of prior handoff. |
| `SANADSQUAD_RECALL_RECOVERY_HANDOFF/` | Nested handoff copy | `HISTORICAL_ARCHIVE` | Moved to external archive | Recursive unpacked copy of prior handoff. |
| `audit/evidence_first_v2/` | Audit logs & reports | `REVIEW_DOCUMENTATION` | Retained in docs/audit | V2 design records, pilot logs, and remediation reports. |
| `audit/visuals/` | Architecture graphics | `REVIEW_DOCUMENTATION` | Retained | Mermaid diagrams, SVG, and PNG workflow charts. |
| `README.md`, `ARCHITECTURE.md` | Primary documentation | `REVIEW_DOCUMENTATION` | Updated & retained | Core system architecture and instructions. |
| `LIMITATIONS.md`, `ACCEPTANCE_MATRIX.md` | Primary documentation | `REVIEW_DOCUMENTATION` | Updated & retained | Risk disclosures, negative benchmarks, and acceptance matrix. |
| `TEST_RESULTS.md`, `HANDOFF_MANIFEST.txt` | Primary documentation | `REVIEW_DOCUMENTATION` | Updated & retained | Empirical test telemetry and handoff declarations. |
| `.pytest_cache/`, `__pycache__/` | Python byte caches | `GENERATED` | Pruned | Transient build and test artifacts. |

---

## 3. Custody & Fail-Closed Statement

All `HISTORICAL_ARCHIVE` and `GENERATED` artifacts have been mirrored to `/home/shady/sandsquad_archive/` with SHA-256 checksums before removal from the active repository worktree. Zero `UNKNOWN` or `SECRET_OR_UNSAFE` assets exist. No active source code, tests, schemas, instructions, or canonical outputs have been deleted.
