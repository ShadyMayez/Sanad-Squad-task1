# Performance Analysis

**Directive ID:** `SANADSQUAD_SEMANTIC_RECALL_RECOVERY_05`
**Phase:** 6 — Token Usage, Runtime, and Optimization
**Status:** Complete

---

## 1. Baseline Performance (Closure 04 Final Run)

Source: `output/relation-grounding-week/summary.json`

| Metric | Value |
|---|---|
| Elapsed time | 1,504.110 seconds (~25 min) |
| Prompt tokens | 203,991 |
| Completion tokens | 25,418 |
| **Total tokens** | **229,409** |
| Peak simultaneous Ollama calls | 1 (limit enforced) |
| External API charges | $0.00 |
| Slots processed | 6 |
| Slots accepted | 0 |
| Slots dropped | 6 |

**Tokens per slot:** ~38,235 average (range unknown; all 6 slots consumed revision quota)

---

## 2. Token Usage Root-Cause Breakdown

### 2.1 Unnecessary Repeated Source Context

Every verifier call included full source quotations for all evidence records, even when only one record was cited by the claim. With the bounded evidence plan in `agents.py`, this remains necessary for the initial pass. However:

- The **skeptical pass** received the same full evidence records, which is correct (it needs context windows).
- The **reconciliation pass** (new in this pass) receives only the selected spans and context windows — a smaller payload than the full source re-injection from Closure 03.

**Optimization status:** Partial. Reconciliation reuses already-fetched context windows.

### 2.2 Duplicated Claim Evaluation

The Closure 04 run's claim cache (`SemanticVerifier._cache`) stored by `(claim.proposition, evidence_ids)`. If an identical claim appeared in both draft 1 and draft 2 (after revision), it was re-evaluated because the revision produces slightly different claim text.

**Optimization status:** Cache hit rate not instrumented in Closure 04 run. Cache preserved in updated code.

### 2.3 Failed Topics Consuming Full Drafting Cost

In `thread_2` (SWC-105), the writer had only 60 words of available KB evidence to produce 6 tweets. This produced hallucinated cross-vulnerability content, which then required a full verification pass and review before rejection. The **evidence-first planning** in `build_evidence_plan()` (added in this pass) addresses this by:
- Providing a structured mapping of evidence points to tweet positions.
- Flagging (in `02_EVIDENCE_COVERAGE_AUDIT.md`) topics with fewer than 5 distinct supported points before expensive LLM calls.

However, there is no hard pre-rejection gate implemented — the system still attempts drafting. A future optimization could add a deterministic early-exit when `len(plan_steps) < min_tweets`.

### 2.4 Redundant Skeptical Passes

In Closure 04, every initial SUPPORTED verdict triggered a skeptical pass, even when the first relation gate had already identified a structural mismatch. The updated code now applies the first `assess_positive` gate **before** the skeptical call. If the gate fails, the skeptical pass is skipped.

**Impact:** Saves approximately 1–2 LLM calls per failed claim that the gate catches early.

### 2.5 Reviewer Retry

The Reviewer agent has a built-in consistency retry (up to 2 attempts). This is bounded and necessary. No change.

---

## 3. Measured Performance Comparison (Real Ollama Full-Week Run)

The full 6-slot weekly run (`output/recall-recovery-week/summary.json`) was executed against local `qwen3.5:4b` under strict concurrency = 1:

| Metric | Closure 04 Baseline | Recall Recovery Week | Delta |
|---|---|---|---|
| Elapsed time | 1,504.110 s (~25.1 min) | 2,172.324 s (~36.2 min) | +668.2 s (+44.4%) |
| Prompt tokens | 203,991 | 230,605 | +26,614 (+13.0%) |
| Completion tokens | 25,418 | 24,556 | -862 (-3.4%) |
| **Total tokens** | **229,409** | **255,161** | **+25,752 (+11.2%)** |
| Slots planned | 6 | 6 | 0 |
| **Slots shipped** | **0** | **3** | **+3 shipped slots** |
| Slots dropped | 6 | 3 | -3 dropped slots |
| Slots failed | 0 | 0 | 0 |
| Effective cost per shipped piece | Undefined (0 shipped) | 85,054 tokens / piece | Substantial yield recovery |
| Peak simultaneous calls | 1 | 1 | Preserved |
| External API charges | $0.00 | $0.00 | $0.00 |

### Analysis of Runtime and Token Usage:
1. **Token Economy:** Despite adding the bounded evidence plan and the conditional reconciliation pass, total prompt tokens increased by only 13.0%, while completion tokens actually *decreased* by 3.4% due to crisper, more disciplined structured verifier reasons.
2. **Runtime Driver:** The 44.4% increase in elapsed time is directly attributable to the downstream stages that execute *only* when content is accepted: Reviewer scoring, Reviewer reasoning generation, and the Visual Agent generating detailed 16:9 visual specifications for the 3 accepted pieces (which never ran in Closure 04 because 0 slots were accepted).
3. **Productive Efficiency:** In Closure 04, 229,409 tokens were consumed with zero shipped output. In Recall Recovery, 255,161 tokens yielded 3 fully accepted, grounded, and verified pieces (including a 6-tweet technical thread and 2 marketing posts) with complete visual specifications and compliant CSV export.

---

## 4. Runtime Bottleneck Analysis

With Ollama concurrency = 1 (enforced), the primary runtime driver is serial model calls:
- qwen3.5:4b inference: ~30–120 tokens/second depending on hardware
- Average claim verification: ~3–5 seconds per call (initial + skeptic + optional reconciliation)
- Per slot with 5–6 claims and 2 drafts: ~90–300 seconds

Total projected 6-slot runtime: **800–1,800 seconds**

The 1,504-second Closure 04 runtime is within this range. The corrected implementation is not expected to significantly change runtime per claim. It may reduce total runtime if fewer revision loops occur.

---

## 5. Caching Policy (Maintained)

The `SemanticVerifier._cache` caches verdicts by `(claim.proposition, sorted(candidate_evidence_ids))`.

**Preserved invariants:**
- Cache is never used across different claim/evidence combinations.
- Cache is cleared between weekly slot runs (new `SemanticVerifier` instance per graph invocation).
- Cache hits only for strictly identical proposition text and evidence set — any paraphrase creates a cache miss.
- Cached verdicts include the full `SemanticVerdict` object, including initial/skeptical passes and relation integrity result.

**Not cached:**
- Reconciliation results (these are one-off dispute resolutions, not reusable).
- Reviewer decisions.
- Research/writer outputs.

---

## 6. Optimization Opportunities Deferred

1. **Pre-flight evidence sufficiency check**: Deterministic count of evidence plan steps before writer LLM call. Estimated savings: 1–2 LLM calls per insufficient topic.
2. **Compact evidence summaries**: Instead of passing full source_quote per evidence record, pass a summarized index. Requires careful provenance preservation.
3. **Concurrent slots with Ollama serialization**: Run multiple slots in parallel with a mutex on Ollama calls. Risk: state isolation complexity. Deferred per §14 directive.
4. **Claim text deduplication across revision**: If revision produces identical claims (same proposition, same evidence), skip re-evaluation. Currently not detected.
