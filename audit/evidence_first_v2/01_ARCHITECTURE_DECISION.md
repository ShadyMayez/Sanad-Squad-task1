# Architecture Decision Record (ADR) — Evidence-First V2 Architecture

**Directive:** `SANADSQUAD_EVIDENCE_FIRST_V2_IMPLEMENTATION_01`  
**Status:** ACCEPTED (Supported by Stage 2 Feasibility Evidence)  
**Date:** 2026-10-16  
**Context:** Local Workstation (~16 GB RAM, 4 GB VRAM), Ollama `qwen3.5:4b`, LangGraph Orchestration.

---

## 1. Context and Problem Statement

SanadSquad operates under strict local compute constraints while generating professional smart contract security threads and marketing posts for X. In Closure 07 (and prior iterations Closure 01–06), the architecture relied on a **post-hoc factual reconstruction** model:
1. The Writer agent generated unconstrained natural language copy from raw source quotes.
2. A downstream regex/LLM pipeline attempted to extract individual atomic factual claims and relational assertions from the realized text.
3. Multiple verification layers (initial verifier, skeptic pass, reconciliation pass, relation integrity gate) attempted to prove semantic entailment against pinned KB evidence records.

This post-hoc reconstruction model caused chronic system failure:
- **Excessive token inflation:** In `final-relation-week`, 261,046 tokens were consumed across 6 slots (~43,500 tokens/slot).
- **Extreme latency:** A 6-slot weekly execution took 39 minutes (2,340 seconds).
- **Unstable yield:** Accepted weekly pieces fluctuated between 0/6 and 3/6 due to false rejections caused by sentence fragmentation, dangling conjunctions, and rigid regex patterns attempting semantic reasoning.
- **Defect recurrence:** Minor changes in phrasing frequently inverted causal direction, converted recommendations into absolute guarantees, or spliced disparate vulnerability mechanics (e.g. historical `post_3` defect).

---

## 2. Decision: Evidence-First Planning & Plan-to-Text Conformance

We adopt an **Evidence-First Content-Generation Architecture** that shifts factual validation *before* natural language realization:

```text
TRUSTED SOURCE EVIDENCE (Pinned Snapshots + Cryptographic Witnesses)
         |
         v
VERSIONED FACTUAL PROPOSITIONS (VerifiedProposition)
         |
         v
APPROVED TYPED RELATIONSHIPS (TypedRelation)
         |
         v
EVIDENCE-FIRST CONTENT PLANNER (EvidenceFirstPlan & ContentUnit)
         |
         v
DETERMINISTIC PLAN VALIDATION (Catalog integrity & Version boundaries)
         |
         v
CONSTRAINED NATURAL-LANGUAGE WRITER (Realization Modes A/B)
         |
         v
PLAN-TO-TEXT CONFORMANCE VERIFICATION (Deterministic + Semantic)
         |
         v
BUSINESS POLICY + FORMAT VALIDATION (Hard vs. Soft rules)
         |
         v
INDEPENDENT EDITORIAL REVIEWER
         |
         v
HUMAN REVIEW WHERE REQUIRED (Approval gate)
         |
         v
VISUAL SPECIFICATION (Accepted-only)
         |
         v
ACCEPTED-ONLY EXPORT + AUDIT (posts.csv & JSON logs)
```

---

## 3. Core Principles & Boundaries

1. **Factual Meanings Are Pre-Selected, Not Post-Extracted:**
   - The system only realizes propositions (`VerifiedProposition`) and relations (`TypedRelation`) that already have pinned, reviewed evidence witnesses in `catalog.json`.
   - The LLM Writer does not choose what facts are true; it realizes approved structural units into natural, engaging security copy.
2. **Relationships Require Explicit Witnesses:**
   - A proposition's existence does not authorize arbitrary relations involving it. Two true propositions (e.g., $P_1$: "External calls can fail", $P_2$: "Missing access control allows draining") cannot be causally connected unless an explicit `TypedRelation` exists in the catalog.
3. **Plan-to-Text Conformance Replaces Open-Ended Entailment:**
   - The verifier does not search a broad knowledge base to prove an arbitrary sentence. It answers a closed, well-posed semantic question: *Does this realized sentence faithfully express the planned propositions without introducing unapproved extra claims, causal inversions, or dropped qualifiers?*
4. **Deterministic Pre-Filtering:**
   - Character counts, brand violations, and compiler version boundaries (e.g. `Solidity < 0.4.22`) are enforced deterministically in Python (0.00s latency) before spending LLM tokens.
5. **One-Revision Target Feedback:**
   - If a specific unit in a plan fails conformance, targeted feedback is sent to revise only that unit, preserving stable conforming units.
6. **Dual-Mode Preserved LangGraph Engine:**
   - The pipeline supports both `legacy` and `evidence_first_v2` execution modes via configuration. Legacy code is preserved for continuous comparison and rollback safety.

---

## 4. Consequences and Verification

### Positive Consequences
- **96.0% Token Reduction:** Dropped from ~43,500 tokens/slot to ~1,736 tokens/slot.
- **9x Speedup:** Slot latency dropped from 6.5 minutes to 43 seconds.
- **100% Conformance & 100% Adversarial Defect Rejection:** Validated in Stage 2 across 12 independent test cases.
- **Predictable Yield:** Structural preflight guarantees that content is only attempted when sufficient evidence exists.

### Negative Consequences / Trade-offs
- Writing requires structured proposition catalogs: Curating `catalog.json` requires initial review (`REVIEWED_FOR_PILOT` or `APPROVED`). Uncataloged topics fail closed at preflight rather than producing hallucinated content.
- Phrasing freedom is constrained to approved facts: The Writer cannot invent historical anecdotes, specific exploit numbers, or broad generalities not grounded in the catalog.
