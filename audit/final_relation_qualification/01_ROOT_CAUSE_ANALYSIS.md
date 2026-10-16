# Root-Cause Analysis: Semantic Relation Verification Deficiencies

## 1. Executive Summary

Directive `SANADSQUAD_RELATION_VERIFICATION_CORRECTION_06` investigated the complete pipeline failure in the preceding run (`0/6` shipped, `6/6` dropped), despite 106 automated tests passing and all 18 pinned KB evidence records passing provenance checks.

The investigation demonstrated that asking keyword regex whitelists to make natural language entailment decisions created a dual failure mode:
1. **Severe False Rejections (Over-strictness):** Valid marketing rationales and technical explanations (e.g. access-control review rationales in SWC-105) were rejected because their wording lacked specific words present in an arbitrary 12-word regex whitelist (`fail|exception|continue|resume|behaviour...`).
2. **False Permissiveness (Under-strictness):** Unrelated cross-vulnerability claims (e.g. connecting SWC-113 external-call failures to SWC-105 withdrawal losses) passed deterministic checks because the checker checked word overlap against *any* causal span without verifying that the *same* span bridged both premise and conclusion.

---

## 2. Independent Root-Cause Decomposition

### Defect R1: Valid Marketing Rationale Falsely Rejected
- **Statement:** *"Review how your contract restricts Ether withdrawals, since missing access controls allow malicious parties to withdraw funds from the contract account."*
- **Evidence:** SWC-105#0 (*"Due to missing or insufficient access controls, malicious parties can withdraw some or all Ether from the contract account."*).
- **Mechanism:** In `content_pipeline/relation_integrity.py`, `assess_positive` and `verify_sentence_relation` enforced:
  ```python
  has_concern = bool(re.search(r"\b(?:fail|exception|continue|resume|behaviour|unexpected|loss|unauthorized|risk|drain|bug|unhandled|vulnerab)\b", premise, re.I))
  if not has_concern:
      return RelationAssessment(roles, False, False, "The justification premise does not state a verifiable technical risk or mechanism")
  ```
- **Root Cause:** A brittle regex whitelist attempted to judge whether an English clause describes a technical hazard. In R1, the premise stated `"missing access controls allow malicious parties to withdraw funds from the contract account"`. None of the 12 whitelist terms were present (`missing`, `access`, `controls`, `parties`, `withdraw`, `funds` are not in the whitelist). Consequently, valid, source-grounded copy was rejected.

### Defect R2: Missing Causal and Connective Extraction
- **Statement Forms:**
  - `X, as Y`: *"Review contract logic, as failed calls can cause DoS."*
  - `X since Y` without comma: *"Review contract logic since failed calls can cause DoS."*
  - `X due to Y` / `Due to Y, X`
  - `X caused by Y` / `Caused by Y, X`
  - `X, resulting in Y` / `X resulting in Y`
  - `X, leading to Y` / `X leads to Y`
  - `If X, Y` / `X if Y`
  - `X; therefore, Y` / `X, consequently Y`
- **Mechanism:** In `content_pipeline/claim_extraction.py`, `RELATION_PATTERNS` only matched comma-delimited `,\s*since` and mid-sentence `\s+because\s+`. It lacked patterns for `, as `, unpunctuated `since`, `due to`, `caused by`, `resulting in`, `leading to`, and conditionals.
- **Root Cause:** Incomplete coverage of standard technical English conjunctive patterns caused the extractor to return an empty relation list (`[]`), failing to establish structured relationship records for whole-sentence verification.

### Defect R3: Cross-Source Causal Splicing Falsely Accepted
- **Statement:** *"The contract can lose funds because external calls can fail."*
- **Supplied Evidence:** SWC-105#0 (withdrawal loss from missing access controls) + SWC-113#0 (DoS from external call failures).
- **Mechanism:** In `content_pipeline/relation_integrity.py`:
  ```python
  premise_words = set(re.findall(r"\b[a-zA-Z]{4,}\b", rel.premise.lower())) - STOPWORDS
  bridging_spans = [span for span in selected_spans if DIRECT_CAUSAL.search(span) and not NORMATIVE_START.search(span)]
  links_premise = any(any(w in span.lower() for w in premise_words) for span in bridging_spans)
  ```
- **Root Cause:** The check only verified whether *any* word from the premise appeared in *any* causal span. SWC-113#0 contained `"calls"` and `"fail"`, so `links_premise` evaluated to `True`. Crucially, the check never tested whether the conclusion (*"The contract can lose funds"*) was connected to that same causal span. Because SWC-105 mentioned fund loss and SWC-113 mentioned call failure, the two unrelated excerpts were spliced together, falsely passing deterministic verification.

### Defect R4: Version Number Parsing in Sentence Splitter
- **Symptom:** `thread_2` dropped with `Tweet 3 contains uncovered substantive text: 'IfconstructorcodeendsupinruntimebytecodeSolidity04'`.
- **Root Cause:** In `content_pipeline/text_spans.py`, `SENTENCE = re.compile(r"[^.!?]+(?:[.!?](?!\S)|$)")` split version strings like `Solidity < 0.4.22` at `0.` and `.22`. The sentence boundary was broken mid-version, leading atomic claim extraction to miss substrings and fail the coverage invariant.
