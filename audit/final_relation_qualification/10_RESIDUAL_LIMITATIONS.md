# Residual Limitations & Safety Boundaries

## 1. Local Model Semantic Boundaries (`qwen3.5:4b`)

While the corrected relationship-verification architecture successfully eliminates the demonstrated keyword-whitelist failure modes (R1, R2, R3) and recovers valid yield, several fundamental boundaries remain inherent to deploying a 4-billion parameter local model:

1. **Syntactic Sensitivity to Complex Compound Propositions:**
   `qwen3.5:4b` can occasionally become confused when a single sentence contains multiple nested clauses (e.g., combining a historical version qualification, a legacy vulnerability mechanism, and a multi-step remediation habit in one sentence). The pipeline mitigates this by restricting atomic claim extraction to at most 25 atomic claims per slot and decomposing sentences at natural clause boundaries.

2. **Absence of Real-World Common Knowledge:**
   The verifier and skeptical auditor are strictly instructed to evaluate entailment solely against pinned source context windows. When an author attempts to introduce domain knowledge that is standard in Ethereum development (e.g. OpenZeppelin `onlyOwner` mechanics) but not explicitly stated in an SWC record, the semantic gate correctly marks it `INSUFFICIENT_EVIDENCE`. This is a deliberate safety property, not a model bug.

3. **Inference Latency and Single Concurrency:**
   Due to local CPU/GPU resource constraints, `OLLAMA_MAX_CONCURRENCY` is pinned to `1`. Full weekly execution runs require approximately 25–35 minutes for six complete slots with multiple-pass semantic auditing and reviewer evaluations. Attempting concurrent model invocations triggers process lock timeouts.

---

## 2. Deterministic Verification vs. Probabilistic Judgment

The corrected architecture strictly adheres to proper separation of concerns:
- **Deterministic Python Gates:**
  - Hard schema validation (Pydantic).
  - Provenance offsets and SHA-256 snapshot hashes.
  - Sentence boundary parsing and version-number preservation.
  - Causal inversion vetoes (remediation cannot cause a vulnerability).
  - Dual-topic causal bridging (rejecting spliced cross-source claims).
  - Universal quantifier and absolute prevention suppression.
- **Probabilistic Semantic Model:**
  - Natural language domain paraphrasing.
  - Nuanced technical synonym evaluation.
  - Direction and context interpretation.

Deterministic Python checks act as non-overridable vetoes, but never manufacture positive support.

---

## 3. Pre-Declared Performance Metrics vs. Production Realities

In benchmark evaluations (`audit/recall_recovery/fixtures/heldout_benchmark.json` and `audit/final_relation_qualification/fixtures/heldout_relation_benchmark.json`), the system achieved:
- 100% rejection of unsupported causal connections.
- 0% false acceptance on relation fixtures.
- Over 85% supported recall on calibrated fixtures.

However, in autonomous weekly runs where the Writer model generates unconstrained novel technical prose, slight phrasing variations can still trigger skeptical vetos. The system operates strictly **fail-closed**: when semantic certainty cannot be established, content is dropped rather than shipped.
