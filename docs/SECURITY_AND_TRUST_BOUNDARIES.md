# Security Model, Trust Boundaries & Operational Governance

**System:** SanadSquad Content Generation & Verification Pipeline (Evidence-First V2)  
**Classification:** Senior Engineering Audit Document  
**Date:** 2026-10-17  

---

## 1. Threat Model & Untrusted Inputs

SanadSquad operates in a high-consequence technical publishing domain where publishing inaccurate smart contract security advice can lead to real-world smart contract exploits or brand reputation damage.

### Untrusted Input Vectors
1. **Free-Form LLM Output:** Local or external small models (`qwen3.5:4b`) cannot be trusted for factual authority. Small models frequently hallucinate domain-plausible extrapolations (e.g. claiming a DoS vulnerability drains funds).
2. **Adversarial / Manipulated Sources:** Upstream source documents or third-party web content could contain prompt injections, conflicting claims, or outdated recommendations.
3. **Model Reviewer Collusion:** Downstream model reviewers often share biases with the generating model and can rationalize ungrounded statements as "natural variations".
4. **Forged State / Status Injection:** Direct API callers or malformed graph state could attempt to pass an unreviewed draft into export.

---

## 2. Layered Trust Boundaries & Fail-Closed Architecture

SanadSquad enforces a strict separation of powers between **deterministic code authority** and **stochastic model generation**:

```
+---------------------------------------------------------------------------------------------------+
|                                       SECURITY ARCHITECTURE                                       |
+---------------------------------------------------------------------------------------------------+
|  [Untrusted Planner]                                                                              |
|         │                                                                                         |
|         ▼                                                                                         |
|  [Gate 1: Hard Catalog & Policy Preflight] ──(Fails Closed: INSUFFICIENT_EVIDENCE / UNAPPROVED)   |
|         │                                                                                         |
|         ▼                                                                                         |
|  [Bounded Generation: EvidenceFirstWriter] ──(Constrained by exact Proposition IDs & JSON schema) |
|         │                                                                                         |
|         ▼                                                                                         |
|  [Gate 2: Deterministic Plan-to-Text Conformance] ──(Preflight checks: mechanism, scope, topics)  |
|         │                                                                                         |
|         ▼                                                                                         |
|  [Gate 3: Deterministic Brand & Platform Gate] ──(Validates 280 chars, allowed URLs, CTAs)       |
|         │                                                                                         |
|         ▼                                                                                         |
|  [Gate 4: Two-Pass Semantic Verification] ──(Verifier + Independent Skeptic)                     |
|         │                                                                                         |
|         ▼                                                                                         |
|  [Gate 5: Deterministic Export Gate] ──(Re-verifies hashes, brand, specs before writing CSV)     |
|         │                                                                                         |
|         ▼                                                                                         |
|  [Final Artifact: posts.csv + visual_specs/]                                                      |
+---------------------------------------------------------------------------------------------------+
```

### Trust Boundary Details

#### Boundary 1: Pinned Source Snapshot Integrity
- Curated evidence records in `kb.json` and `catalog.json` are cryptographically bound to physical files in `source_snapshots/`.
- Every evidence record specifies `snapshot_sha256`, `quote_start`, `quote_end`, and `source_quote`.
- The pipeline recomputes SHA-256 digests on disk and checks that `snapshot[quote_start:quote_end] == source_quote`. If a file is tampered with or missing, the slot fails closed (`PROVENANCE_ERROR`) without generating ungrounded content.

#### Boundary 2: Proposition Catalog Authority
- In Evidence-First V2 (`--mode evidence_first_v2`), factual authority lives entirely in the vetted catalog (`knowledge/evidence_first_v2/catalog.json`).
- Writers are strictly forbidden from asserting concepts not represented in the catalog.
- In `--authorization-mode publication_eligible`, the planner and live graph enforce that all cited propositions and relations must carry `APPROVED` status, immediately failing closed on any pilot-only (`REVIEWED_FOR_PILOT`) entries.

#### Boundary 3: Deterministic Conformance Preflight
- Code gates in `content_pipeline/conformance.py` inspect generated text *before* model verification:
  - **Topic Isolation:** Vetoes alien vulnerability concepts (e.g., access control terms in a reentrancy thread).
  - **Instrumental Mechanism Check:** Vetoes unlicensed mechanisms (`prevent/stop execution from continuing on failure`).
  - **Universal Scope Check:** Vetoes universal generalizations (`all external calls`).
  - **Comparative Ranking Check:** Vetoes hyperbolic superlatives (`primary defense`, `most critical`).

#### Boundary 4: Brand & Link Allowlist Enforcement
- `brand.allowed_links: []` is deterministically enforced across single posts and threads. Any unauthorized URL immediately fails validation and is blocked at export.
- Hard platform limits (280 characters per tweet, 1 tweet for marketing posts, 5–10 tweets for technical threads) are validated both via Pydantic schema validation and deterministic string measurement.

#### Boundary 5: Independent Export Gate
- `content_pipeline/export.py` operates as an independent gate:
  - Re-evaluates deterministic brand and platform rules.
  - Verifies that every accepted piece has an associated non-empty visual specification.
  - Drops any slot where review scores fail thresholds, regardless of model approval flags.
  - Never exports drafts directly from memory without passing through export validation.

---

## 3. Human Approval & Production Governance

In enterprise security auditing workflows, automated AI generation must be subject to organizational policy controls:
- **Default Assignment Mode (`require_human_approval_for_ship = false`):** Runs fully autonomously, evaluating drafts via the AI Reviewer and deterministic code gates.
- **Strict Client Policy Mode (`require_human_approval_for_ship = true`):** Supported via `--policy security_audit_firm`. When enabled:
  - Accepted pieces are routed to `ready_for_human_review.json`.
  - Content is strictly withheld from `posts.csv` until an authorized human signs off.
  - Requires a cryptographically bound `HumanApprovalRecord` containing approver ID, timestamp, approved draft SHA-256 digest, policy ID, and policy version.

---

## 4. Container & Supply Chain Security

The offline Docker image (`sanadsquad:v2-offline`) adheres to production container hardening principles:
- **Zero Remote Network Access:** Executed with `--network none` in production/review to guarantee that no telemetry, training data, or external API calls leak.
- **Non-Root Execution:** Runs under an unprivileged application user (`appuser`, UID 1000) with minimal Linux capabilities.
- **No Embedded Secrets:** The image contains zero API keys, passwords, or cloud credentials. `.env` files are explicitly excluded via `.dockerignore`.
- **Read-Only Code & Data:** System code, proposition catalog, instructions, and source snapshots are mounted read-only during execution. Only the assigned output directory (`/app/output`) is writable.
- **Embedded Inference Isolation:** Ollama server runs locally within container userland on `localhost:11434`, never exposed to the host network interface.
