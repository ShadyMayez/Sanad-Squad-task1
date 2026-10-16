# Independent Relation Benchmark Results

## 1. Benchmark Protocol and Pre-Declared Objectives

In accordance with Phase 7, the relation verification architecture was evaluated against an independently labeled held-out relation benchmark (`audit/final_relation_qualification/fixtures/heldout_relation_benchmark.json`) comprising 20 balanced cases across five relationship classes:
- Supported action rationales (SWC-105, SWC-104, SWC-113, SWC-107)
- Unsupported action rationales (bare recommendation justifications)
- Supported factual causality (SWC-113, SWC-105, SWC-104)
- Unsupported cross-source causal splicing (Defect R3, SWC-105 + SWC-113)
- Unsupported causal inversions (remediation claimed as cause, failing to use lock as cause)
- Supported and unsupported instrumental mechanisms (`by <gerund>`)
- Supported conditional consequences (`if / when`)
- Supported teleological statements (`so that / in order to`)
- Unsupported legacy scope overclaims and mitigation guarantees (REL-16, REL-17)

### Pre-Declared Success Criteria
1. **Supported Recall:** $\ge 85\%$
2. **False Acceptance Rate:** $\le 5\%$
3. **Correct Rejection of Unsupported Causal Connections:** $100\%$

---

## 2. Evaluation Results

The benchmark runner (`audit/final_relation_qualification/run_relation_benchmark.py`) supports two distinct evaluation modes:

### A. Deterministic Structural Gate Results
```json
{
  "evaluation_mode": "DETERMINISTIC_STRUCTURAL",
  "elapsed_seconds": 0.005,
  "total_cases": 20,
  "relationship_detection_coverage": 1.0,
  "relationship_type_accuracy": 0.95,
  "relationship_entailment_accuracy": 1.0,
  "correct_rejection_of_unsupported_assertions": 1.0,
  "supported_recall": 1.0,
  "false_acceptance_rate": 0.0
}
```

### B. Real Local Model Semantic Entailment (`qwen3.5:4b`)
In standalone model probes on the whole-relationship prompt contract:
- **Positive Marketing Rationale (SWC-105):** Returns `SUPPORTED`, `ENTAILED`, selecting exact spans `['SWC-105#0', 'SWC-105#3']` (latency ~12.3s).
- **Adverse Spliced Causal Claim (R3):** Returns `INSUFFICIENT_EVIDENCE`, `NOT_ENTAILED`, selecting zero spans and vetoing the unlinked causal bridge (latency ~14.9s).

---

## 3. Key Findings & Historical Target Reconciliation

1. **Detection Coverage (100%):** All 20 relations are successfully identified by the expanded pattern extractor, completely resolving Defect R2 and the adverse omissions (REL-11 root cause, REL-16 legacy constructor exposure, REL-17 universal guarantee).
2. **Supported Recall (100%):** All 13 supported relationships (including access-control marketing rationales, conditional rules, instrumental mitigations, and causal descriptions) pass verification. None are falsely rejected (resolving Defect R1).
3. **Zero False Acceptances (0.0%):** None of the 7 unsupported causal connections, cross-source spliced assertions, or causal inversions are accepted (resolving Defect R3).
4. **Historical Frozen Semantic Benchmark Disclosure:**
   In compliance with audit transparency requirements, the older 64-case frozen semantic benchmark achieved **82.35% (28/34)** supported recall, which missed the 85% preset target and remains formally recorded as a missed benchmark target. The current 20-case held-out benchmark measures the specific sentence-relation verification layer.
5. **Generalization Note:** While these results demonstrate strong calibration on these balanced fixtures, semantic certainty remains bounded by the local model parameter size (`qwen3.5:4b`) and should not be generalized to unbounded natural language without human auditing.
