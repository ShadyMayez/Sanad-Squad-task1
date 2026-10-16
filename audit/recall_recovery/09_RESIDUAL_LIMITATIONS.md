# Residual Limitations

**Directive ID:** `SANADSQUAD_SEMANTIC_RECALL_RECOVERY_05`
**Phase:** 9 — Residual Scientific and Operational Limitations
**Status:** Documented

---

## 1. Local Model Semantic Fragility (qwen3.5:4b)

The 4B-parameter local model exhibits structural limitations that the engineering corrections in this pass partially mitigate but cannot fully eliminate:

### 1.1 Pedantic Lexical Matching
The model's skeptical pass in Closure 04 rejected:
- "may call back" when source says "calls back" (modal narrowing treated as scope change)
- "while still active" when source says "before the first invocation is finished" (synonym treated as ambiguity)
- "loss of funds" when source says "loss of funds or data" (entailed subset treated as scope expansion)
- "before using it in contract logic" when source says "before use" (narrower application treated as unsupported)

**Status:** Partially addressed by skeptic prompt calibration (instructions/semantic-skeptic.md) and the bounded reconciliation pass. Fundamental model-side resolution requires either a larger model or few-shot prompt engineering not currently implemented.

### 1.2 Decision Variance at Temperature 0
Even with deterministic configuration, minor context changes between runs produced different decisions for 1 out of 10 supported claims between the initial frozen benchmark run and the code-replay run (5/10 → 4/10). This is a documented limitation of small-model inference.

### 1.3 Structured Output Schema Adherence
qwen3.5:4b occasionally returns relation fields inconsistent with the verdict (e.g., `verdict=SUPPORTED` with `relationship_verdict=NOT_ENTAILED`). The `assess_positive` gate catches and vetoes these structural inconsistencies, but they consume tokens and time.

---

## 2. Evaluation Sample Size Limitations

### 2.1 Frozen Benchmark Coverage
The 20-case frozen benchmark covers only two vulnerability categories (SWC-107 and SCWE-028) in detail. Generalization to all 16 KB vulnerabilities is not proven.

### 2.2 Independent Adjudication
Ground truth labels for all benchmark cases were authored by the implementing engineer based on exact source texts. Independent adjudication by an external smart contract security auditor was not performed. This limits confidence in cases where the "correct" label is ambiguous.

### 2.3 Target Metrics Confirmed on 64-Case Frozen Benchmark
The 64-case frozen held-out benchmark has been independently evaluated against real `qwen3.5:4b` inference (`audit/recall_recovery/heldout-benchmark-results.json`):
- **Recommendation paraphrase recall:** **87.5%** (7/8) — exceeds the $\ge 85\%$ target.
- **Overall supported recall:** **82.35%** (28/34) — recovered from 40% baseline; 100% precision.
- **Adverse false acceptance rate:** **0.0%** (0/30) — zero causal inversions or overclaims accepted.
- **Yield bounds:** The remaining ~17.6% supported false rejections (6 claims) reflect small-model (`qwen3.5:4b`) conservative bounds where the model fails closed on subtle paraphrases rather than risking hallucination.

---

## 3. Knowledge Base Finite Coverage

The pinned KB contains 16 smart contract vulnerability entries. Topics outside this set cannot be researched or verified. Live web search and dynamic KB expansion are disabled per directive requirements.

**Known gaps:**
- Newer ERC-4337 account abstraction vulnerabilities not yet represented
- Cross-chain bridge attack patterns not covered
- MEV (maximal extractable value) manipulation not covered
- Gas optimization vulnerabilities not covered

For these topics, the system correctly rejects unverified claims because no KB evidence exists to support them.

---

## 4. Content Generation Volume Limitation

Even with corrections applied, the system may not be able to ship all 6 weekly slots if:
1. The KB evidence for a topic is genuinely thin despite enrichment (e.g., SWC-106 has borderline coverage).
2. The local model produces claims with persistent structural issues that neither reconciliation nor revision can fix.
3. The evidence plan has fewer than 5 defensible points for a required 5-tweet minimum.

**This is by design.** The system is fail-closed: it is preferable to produce 0–3 verified pieces than to generate 6 pieces with fabricated or loosely-grounded content.

---

## 5. Performance and Scalability

- **Runtime:** 25 minutes for 6 slots on current hardware. With accepted slots (requiring visual spec generation), runtime increases.
- **Concurrency:** Enforced at 1 simultaneous Ollama call per directive. Parallel slot execution is not enabled.
- **Hardware cost:** Not instrumented. Local compute, electricity, and hardware depreciation excluded from reported costs.

---

## 6. Safety Boundary — Preserved

The following adversarial behaviors remain fully blocked by the deterministic gate (unchanged from Closure 04):
- Unsupported universal prevention guarantees
- Fabricated company statistics
- Source IDs that do not exist in KB
- Quotes not present in pinned evidence
- Unsupported causal relationships (causal inversion defect)
- Wrong vulnerability mechanisms
- Source-text prompt injection
- Reviewer decisions contradicting mandatory gates
- Accepted content with `VERIFICATION_ERROR` or `INSUFFICIENT_EVIDENCE` claims

**The safety boundary was not weakened by any change in this pass.**
