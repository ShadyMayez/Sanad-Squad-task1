# Defect Reproduction Results: R1, R2, and R3

## 1. Reproduction Methodology

Before introducing any modifications to the codebase, automated reproduction probes were executed against the exact pre-correction implementation to verify and record the three independent findings.

---

## 2. Reproduction Results

### Defect R1 — Valid Marketing Rationale Falsely Rejected
- **Input Text:** `"Review how your contract restricts Ether withdrawals, since missing access controls allow malicious parties to withdraw funds from the contract account."`
- **Candidate Evidence:** SWC-105#0 (*"Due to missing or insufficient access controls, malicious parties can withdraw some or all Ether from the contract account."*)
- **Observed Pre-Fix Result:**
  ```python
  rels = extract_sentence_relations_for_sentence(text, 0, 1, 0, len(text), ["SWC-105"])
  # rels found: 1 (connector: 'since')
  assessment = verify_sentence_relation(rels[0], [span_0])
  # Output:
  # assessment.passed = False
  # assessment.reason = "The justification premise does not state a verifiable technical risk or mechanism"
  ```
- **Finding:** CONFIRMED REPRODUCED. The keyword whitelist in `verify_sentence_relation` failed to recognize the valid access-control hazard.

---

### Defect R2 — Missing Relationship Extraction
- **Case 1 (`X, as Y`):**
  - **Input Text:** `"Review contract logic, as failed calls can cause DoS."`
  - **Observed Pre-Fix Result:** `extract_sentence_relations_for_sentence(...)` returned `[]` (0 relations found).
- **Case 2 (`X since Y` without comma):**
  - **Input Text:** `"Review contract logic since failed calls can cause DoS."`
  - **Observed Pre-Fix Result:** `extract_sentence_relations_for_sentence(...)` returned `[]` (0 relations found).
- **Finding:** CONFIRMED REPRODUCED. Causal connectors with standard English variations were completely omitted from relationship extraction.

---

### Defect R3 — Cross-Source Causal Splicing Falsely Accepted
- **Input Text:** `"The contract can lose funds because external calls can fail."`
- **Supplied Spans:**
  - SWC-105#0: *"Due to missing or insufficient access controls, malicious parties can withdraw some or all Ether from the contract account."*
  - SWC-113#0: *"External calls can fail accidentally or deliberately, which can cause a DoS condition in the contract."*
- **Observed Pre-Fix Result:**
  ```python
  rels = extract_sentence_relations_for_sentence(text, 0, 1, 0, len(text), ["SWC-105", "SWC-113"])
  assessment = verify_sentence_relation(rels[0], [span_105_0, span_113_0])
  # Output:
  # assessment.passed = True
  # assessment.reason = "Sentence relation satisfies conservative relation gate"
  ```
- **Finding:** CONFIRMED REPRODUCED. The deterministic checker falsely declared PASS because premise words matched SWC-113, completely ignoring that no span linked external call failure to fund loss.

---

## 3. Post-Fix Verification

Following the architectural correction:
- **R1:** `verify_sentence_relation()` returns `passed: True`, reason: `"Sentence action rationale satisfies conservative relation gate"`.
- **R2:** Both `, as ` and unpunctuated `since` return `len(rels) == 1` with correct premise and conclusion.
- **R3:** `verify_sentence_relation()` returns `passed: False`, reason: `"Selected source spans independently support isolated clauses but do not establish the asserted causal relationship between premise and conclusion"`.

Automated regression coverage is codified in `tests/test_relation_integrity.py`:
- `test_reproduction_r1_valid_marketing_rationale_passes`
- `test_reproduction_r2_missing_relationship_connectors_extracted`
- `test_reproduction_r3_unrelated_claims_vetoed_by_deterministic_relation_checker`
