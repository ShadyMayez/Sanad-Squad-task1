# Legacy V1 Architecture & Historical Benchmarks

**Directive:** `SANADSQUAD_V2_FINAL_REVIEWABLE_RELEASE_01`  
**Date:** 2026-10-17  
**Archived Reference Commit:** `20e028a8906a1082f384aa8388b5b2a7d0181cb9`  
**Archival Storage Location:** `/home/shady/sandsquad_archive/`  

---

## 1. Overview of Legacy V1 (Generate-Then-Evaluate)

In the initial implementation of SanadSquad (V1), content creation was structured as a post-hoc generate-then-evaluate pipeline:

```
[Research Agent] -> [V1 WriterAgent] -> [Validator / ReviewerAgent] -> [VisualAgent] -> [CSV Export]
                          │                           │
                          └──── Free-form text ───────┘
```

### Components
1. **Research Agent:** Loaded vulnerability descriptions and raw Markdown excerpts from `kb.json`.
2. **Writer Agent:** Prompted with full natural-language instructions (`instructions/tech-thread.md` or `instructions/marketing-post.md`), generating multi-tweet drafts freely based on KB text.
3. **Reviewer Agent:** An LLM-based agent tasked with reading the generated draft, scoring it against a six-dimension rubric (1–5), and verifying claims against quoted evidence.
4. **Visual Agent:** Wrote 16:9 visual specifications for approved pieces.
5. **CSV Exporter:** Formatted accepted tweets into `posts.csv`.

---

## 2. Why V1 Failed: Structural & Factual Deficiencies

### Finding 1: Reviewer-Writer Collusion
In the baseline sample (`output/sample-week/`), the LLM Reviewer awarded perfect 5/5 scores to drafts containing unevidenced or inaccurate claims:
- Asserting Checks-Effects-Interactions is the *sole root cause* of reentrancy (deriving causality from a normative guideline).
- Expanding unchecked call return checks from low-level calls to *all external calls*.
- Promising multi-source aggregation is *the primary defense* against oracle attacks.
- Claiming failed calls *drain contract funds*.

Because small models (4B parameters) lack deep deductive reasoning, the reviewer model could not reliably catch subtle epistemic exaggerations produced by the writer model.

### Finding 2: The Two-Pass Skeptic Bottleneck (Milestone 02 & 03)
To address model collusion, an atomic claim extraction step and an independent `SemanticSkepticAgent` were introduced:
- **Result:** Factual precision improved, but **positive yield collapsed**.
- **Yield Collapse:** On full 6-slot runs, the pipeline dropped 3 or 4 slots per week due to over-conservative skepticism rejecting valid paraphrases.
- **Runtime Explosion:** Token consumption soared to **203,991 tokens** per week (taking over 25 minutes per run).

### Finding 3: Negative Empirical Benchmarks
Extensive frozen holdout benchmarks on `qwen3.5:4b` exposed the hard limits of relying on small models to judge semantic entailment:
1. **64-Case Frozen Holdout Benchmark:**
   - Supported Recall: **82.35% (28/34)** — FAILED the 85% target.
   - 6 supported technical recommendations were falsely rejected.
2. **20-Case Relation Grounding Benchmark:**
   - Supported Recall: **40.0% (4/10)**.
   - Valid Recommendation Paraphrase Recall: **25.0% (1/4)**.
   - Same input produced divergent model decisions across runs due to stochastic temperature variance.

---

## 3. The Evidence-First V2 Solution

These negative benchmarks conclusively demonstrated that **relying on a small language model to judge semantic entailment after free-form text generation is inherently unstable**.

Evidence-First V2 inverted this paradigm:
1. Shifted factual authority into a structured **Proposition Catalog** (`catalog.json`) containing 24 vetted propositions and 23 typed relations.
2. Formatted generation as **constrained proposition realization**, eliminating the need for post-hoc semantic speculation.
3. Enforced deterministic code preflight checks, reducing weekly token usage to **39,776 tokens (-80.5%)** and runtime to **383.9 seconds (-74.5%)** while achieving **100% grounded yield (6/6 shipped)**.
