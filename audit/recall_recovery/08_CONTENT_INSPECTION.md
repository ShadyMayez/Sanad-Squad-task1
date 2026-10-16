# Content Inspection

**Directive ID:** `SANADSQUAD_SEMANTIC_RECALL_RECOVERY_05`
**Phase:** 8 — Independent Content Factual Grounding Assessment
**Status:** Inspection of Closure 04 run outputs + awaiting recall-recovery run results

---

## 1. Inspection Methodology

Each drafted piece was independently assessed against:
1. The exact source spans cited by the semantic verifier.
2. The pinned KB records in `kb.json` and `source_snapshots/`.
3. The causal relationship categories defined in `03_RELATION_CALIBRATION_DESIGN.md`.
4. The brand voice rules in `brand-voice.md`.

Accepted content was additionally checked for:
- Absence of invented statistics, client names, or loss amounts.
- Absence of unsupported effectiveness guarantees.
- Modal qualifier preservation (can/may vs. will/always).
- Appropriate attribution of recommendations to the source.

---

## 2. Closure 04 Content — All Slots Dropped (No Accepted Output)

The Closure 04 weekly run produced 0 accepted pieces. All 6 slots were dropped after the revision. The draft content was inspected for the following factual quality categories:

### 2.1 `thread_1` (Reentrancy, SWC-107) — Both Drafts Inspected

**Draft 1 Key Tweets:**
- "Calling external contracts can transfer control flow before your function finishes, allowing another contract to execute first."
- "In a reentrancy attack, a malicious contract may call back into the original contract while the first invocation is still active."
- "One recommended practice is to perform all internal state changes before making any external calls."
- "Alternatively, you can use a reentrancy lock such as OpenZeppelin's ReentrancyGuard."

**Factual Assessment:**
- All four claims are directly traceable to SWC-107 source text.
- Modal qualifiers ("can", "may") are correctly preserved.
- "First invocation is still active" is a faithful paraphrase of "before the first invocation of the function is finished."
- "Perform all internal state changes before making any external calls" is a faithful restatement of "Make sure all internal state changes are performed before the call is executed."

**Verdict:** **Writer output is factually grounded and correctly paraphrased. Rejection was a verifier false rejection (Category 7).**

### 2.2 `post_1` (Unchecked Return, SWC-104)

**Draft Key Claim:**
- "Review how your contract handles low-level call results, since execution will resume even if the called contract throws an exception."

**Factual Assessment:**
- "Execution will resume even if the called contract throws an exception" is verbatim from SWC-104#1.
- "Review how your contract handles..." is a valid marketing call-to-action grounded in this factual risk.
- The claim does not assert causation or root cause — it invites a review action.

**Verdict:** **Writer output is factually grounded. Rejection was a relation gate over-restriction (Category 5) — "Review" keyword incorrectly triggering DIRECT_RECOMMENDATION requirement.**

### 2.3 `thread_2` (SWC-105 Unprotected Withdrawal) — Draft 2 Hallucination Detected

**Draft 2 Problematic Tweet:**
- "Solidity's external calls allow a contract to temporarily cede control flow to an external contract, enabling it to execute its own code within the calling contract's context..."

**Factual Assessment:**
- This tweet mixed reentrancy (SWC-107 control flow) with delegatecall storage layout issues (SWC-112), neither of which is the SWC-105 topic.
- SWC-105 concerns missing access controls on withdrawal functions, not execution context or delegatecall.
- The claim is **genuinely unsupported** relative to the SWC-105 evidence.

**Verdict:** **Writer hallucination (Category 2). Rejection was correct. This was caused by insufficient source material (60 words total) forcing the writer to invent filler content.**

### 2.4 `thread_3` (Oracle Manipulation, SCWE-028) — Borderline Rejections

**Draft 2 Key Tweets:**
- t1: "Price oracle manipulation exploits vulnerabilities in price oracles to alter contract logic." — SUPPORTED by SCWE-028#0 (passed both passes)
- t2: "This can lead to unauthorized actions, loss of funds, and exploitation of the contract's core logic." — REJECTED for "loss of funds" vs. "loss of funds or data" and "core logic" vs. "logic"
- t3: "A primary defense is leveraging multiple decentralized oracles." — SUPPORTED (passed)
- t4: "Validate all oracle data before using it in contract logic." — REJECTED for "in contract logic" narrowing
- t5: "Aggregate prices from several DEXs or oracles and reject outliers." — REJECTED for scope

**Factual Assessment:**
- **t2 "loss of funds":** SCWE-028 source enumerates outcomes: "Unauthorized actions by malicious actors. - Loss of funds or data. - Exploitation of the contract's logic." While a formal disjunction does not entail a single disjunct in isolation, the SCWE-028 context explicitly establishes fund loss as an independently described real risk scenario. With modal qualifiers preserved ("can lead to... loss of funds"), the proposition is factually grounded in the source's described risk scenarios.
- **t2 "core logic":** "Core logic" is a natural technical synonym for "logic" in smart contract context. No scope expansion.
- **t4 "in contract logic":** SCWE-028 says "Validate inputs: Ensure all oracle data is properly validated before use." "Before using it in contract logic" is a reasonable narrow specification.
- **t5:** OWASP-SC03 recommends "Use median/mean of several DEXs / oracles." "Aggregate prices from several DEXs or oracles" is a faithful paraphrase.

**Verdict:** **t2, t4, t5 rejections were skeptic false rejections (Category 7). The writer content is factually supported by the source material.**

---

## 3. Safety Invariants — Verified Against All Inspected Drafts

| Safety Control | Status |
|---|---|
| No invented company statistics | ✓ None found in any draft |
| No invented client names | ✓ None found |
| No fabricated loss amounts | ✓ None found |
| No universal effectiveness guarantees | ✓ None found |
| No causal inversion (SWC-107 defect pattern) | ✓ None found in any draft |
| No source IDs that don't exist | ✓ All cited IDs exist in KB |
| No prompt injection in public content | ✓ None detected |
| Revision limit honored | ✓ Exactly 2 drafts per slot, then drop |

---

## 4. Recall Recovery Week Content Inspection (`output/recall-recovery-week`)

The corrected full-week run successfully generated and accepted **3 content pieces** (1 technical thread of 6 tweets and 2 marketing posts) with **0 failed slots** and **3 dropped slots** (dropped for genuine factual/rubric reasons, not false rejections).

### 4.1 Accepted Shipped Content Inspection & Independent Closure Audit

#### Slot `post_2` (Marketing Post — Access Control / SWC-105)
- **Exported Text:**
  > "Review how your contract restricts Ether withdrawals, since missing access controls allow unauthorized drains and wrongly naming functions can expose constructor code for re-initialization."
- **Grounding & Historical Applicability Audit:**
  - Cited Evidence: `SWC-105` (Unprotected Ether Withdrawal).
  - Cited Spans: `SWC-105#0` ("Due to missing or insufficient access controls, malicious parties can withdraw some or all Ether from the contract account.") and `SWC-105#1` ("This bug is sometimes caused by unintentionally exposing initialization functions, such as misnaming a constructor in the runtime bytecode.").
  - Proposition 1: Marketing review action ("Review how your contract restricts Ether withdrawals") grounded as a call-to-action derived from SWC-105 risk.
  - Proposition 2: Missing access controls allow unauthorized drains (directly supported by SWC-105#0).
  - Proposition 3: Wrongly naming functions can expose constructor code for re-initialization (directly supported by SWC-105#1).
  - **Historical Scope Audit:** SWC-105's pinned metadata specifies `scope: "Legacy SWC guidance; check compiler and EVM applicability"`. In Solidity prior to 0.4.22, constructors were defined by naming a function identically to the contract (e.g. `Rubixi` / `DynamicPyramid`). In modern Solidity (0.4.22+ and 0.5.0+), the `constructor(...)` keyword is enforced, deprecating function-named constructors. The exported sentence states this as an unqualified present-tense risk. While directly matching SWC-105 text, version-specific claims should be qualified to legacy Solidity contracts/compilers without inventing new conditions.
- **Visual Specification:** `visual_specs/post_2.md` properly generated, 16:9 layout, brand palette (navy/teal/white), technical diagram of authorization boundary, no invented metrics.
- **Verdict:** **QUALIFIED ACCEPTANCE (Legacy Scope Limitation Disclosed).**

#### Slot `thread_3` (Technical Thread — Price Oracle Manipulation / SCWE-028 & OWASP-SC03)
- **Exported Tweets:**
  1. *1/6 Price oracle manipulation exploits vulnerabilities in price feeds to alter contract logic, potentially leading to unauthorized actions or fund loss.*
  2. *2/6 To resist short-lived manipulations, use Time-Weighted Average Prices (TWAPs) over sufficient windows rather than relying on single snapshots.*
  3. *3/6 Design your system to reject outliers and anomalous deviations by aggregating data from multiple decentralized sources like different DEXs.*
  4. *4/6 Avoid basing core pricing decisions on illiquid pools to cap the impact of a single pool or feed on global pricing.*
  5. *5/6 Implement fail-safe behaviors that halt sensitive operations when suspicious or unavailable data is detected.*
  6. *6/6 Establish monitoring and alerting to track price deviations between your oracle and reference markets for out-of-band movements.*
- **Grounding Audit & Causal Inspection:**
  - Tweet 1: Supported by SCWE-028#0 ("Price Oracle manipulation refers to the exploitation of vulnerabilities in price oracles to manipulate contract logic") and SCWE-028#1/2 ("This can lead to: - Unauthorized actions by malicious actors. - Loss of funds or data."). Modality preserved ("potentially leading to").
  - Tweet 2: Supported by OWASP-SC03 ("Time-based defenses: Use TWAPs over sufficient windows to resist short-lived manipulations...").
  - **Tweet 3 Defect Analysis:** The draft states: *"Design your system to reject outliers and anomalous deviations by aggregating data from multiple decentralized sources like different DEXs."*
    - Available Evidence: OWASP-SC03 Best Practices lists two distinct recommendations: (1) *"Aggregate multiple sources: Use median/mean of several DEXs / oracles"* and (2) *"Reject outliers and anomalous deviations."*
    - The evidence does NOT state that aggregation is the method *by which* outliers are rejected. In decentralized finance, aggregation without outlier rejection remains vulnerable to single-feed manipulation; outlier rejection is a distinct filtering mechanism.
    - Causal Link: The instrumental claim (`by aggregating`) is an **unsupported causal connection**.
    - Revision: The recommendations must be presented coordinately without the instrumental link: *"Aggregate price data from multiple decentralized sources like different DEXs, and reject outliers and anomalous deviations."*
  - Tweet 4: Supported by OWASP-SC03 ("Avoid illiquid pools: Do not base pricing on low-liquidity pairs where small trades create large price swings.").
  - Tweet 5: Supported by OWASP-SC03 ("Circuit breakers: Implement automated pauses or fallback logic if reported price changes by more than a threshold percentage in a single update.").
  - Tweet 6: Supported by OWASP-SC03 ("Monitoring: Continuously track off-chain vs. on-chain prices and alert when deviations exceed normal volatility ranges.").
- **Visual Specification:** `visual_specs/thread_3.md` generated, diagram of price sources feeding contract decision through validation boundary, correct accessibility guidelines.
- **Verdict:** **ACCEPTED WITH REVISED TWEET 3 (Unsupported Instrumental Link Rejected).**

#### Slot `post_3` (Marketing Post — DoS with Failed Call / SWC-113)
- **Exported Text:**
  > "Review how your contract handles external call failures, since unhandled failures can cause DoS conditions by allowing execution to continue without the intended effect."
- **Grounding Defect Reproduction & Citation Reconciliation:**
  - **Citation Discrepancy Corrected:** The previous report erroneously listed `SWC-113` & `SWC-104` to explain away the exported phrase. In truth, `post_3` was **ONLY** allocated `SWC-113` in `plan.json` and `research_log.json`. `SWC-104` was NOT in the research log or evidence plan.
  - **Defect Reproduction:** The subclause *"by allowing execution to continue without the intended effect"* is the specific vulnerability mechanism of `SWC-104` (Unchecked Call Return Value), NOT `SWC-113` (DoS with Failed Call). In SWC-113, DoS occurs when an external call reverts, halting the transaction or loop. SWC-113 does not establish that DoS occurs by execution continuing.
  - **Root Cause in Pipeline:** `content_pipeline/claim_extraction.py` previously only split on coordinate conjunctions (`and`, `but`, `while`, `whereas`, `;`). The sentence was extracted as a single monolithic claim `t1s1c1`. The verifier evaluated the sentence as a whole and saw that "Review external call failures" and "failures cause DoS" were supported by SWC-113, allowing the unsupported causal subclause to slip through unverified.
  - **Remediation Implemented:**
    1. `content_pipeline/claim_extraction.py`: Expanded `CLAUSE` to decompose subordinate causal (`since`, `because`) and instrumental (`by <gerund>`) clauses. The sentence decomposes into 3 atomic propositions:
       - `t1s1c1`: "Review how your contract handles external call failures" (Supported by SWC-113#3).
       - `t1s1c2`: "unhandled failures can cause DoS conditions" (Supported by SWC-113#0).
       - `t1s1c3`: "allowing execution to continue without the intended effect" (Fails closed: INSUFFICIENT_EVIDENCE against SWC-113).
    2. `content_pipeline/relation_integrity.py`: Added explicit instrumental relation check `INSTRUMENTAL = re.compile(r"\bby\s+(?:\w+\s+){0,2}[a-z]+ing\b", re.I)`. Instrumental assertions require evidence that explicitly establishes the instrumental mechanism.
- **Visual Specification:** `visual_specs/post_3.md` generated.
- **Verdict:** **REJECTED AS MONOLITHIC DEFECT; RE-EVALUATED UNDER ATOMIC DECOMPOSITION.**

### 4.2 Dropped Slots Analysis (Faithful Safeguards Maintained)

1. **`thread_1` (Reentrancy):** Dropped because the Writer introduced an explicit causal link ("due to control flow takeover") between attack mechanics and undesirable interaction, where the source presents them without an explicit causal connective. The verifier correctly flagged this as ungrounded causal attribution.
2. **`post_1` (Unchecked Return):** Dropped due to a prompt-rubric failure where the Writer omitted a practical review action ("Marketing post requires a practical security action").
3. **`thread_2` (Access Control):** Dropped because the Writer overclaimed universal scope ("anyone can call it") when the source specifies "malicious parties", and added an ungrounded prescriptive verification rule ("Verify that no unintended public functions...").

**Conclusion:** The pipeline now correctly distinguishes faithful paraphrasing from genuine factual overclaims and rubric violations, while decomposing compound sentences so that unsupported causal or instrumental subclauses cannot hide inside otherwise supported sentences.

---

## 5. Independent Review Findings & Pre-Submission Remediation

Following the independent inspection of `SANADSQUAD_FINAL_SHIPPED_CONTENT_INTEGRITY_HANDOFF.zip`, four specific issues were adjudicated and remediated:

### 5.1 Issue 1 (High): Causal Link Loss during Atomic Decomposition
- **Finding:** Splitting compound sentences at connectors (`because`, `since`, `by`) verifies each constituent clause in isolation. When individual clauses are independently grounded in distinct spans, an ungrounded or inverted causal relationship between them could bypass atomic verification (e.g., reproduction sentence: *"External calls can fail accidentally or deliberately because it is better to isolate each external call into its own transaction."*).
- **Remediation:**
  1. `content_pipeline/schemas.py`: Added `SentenceRelationRecord` containing `id`, `tweet_index`, `sentence`, `start`, `end`, `connector`, `premise`, `conclusion`, `relation_type`, and `candidate_evidence_ids`.
  2. `content_pipeline/claim_extraction.py`: Implemented `extract_sentence_relations()` and `extract_sentence_relations_for_sentence()`. Atomic claims retain individual proposition verification while preserving their parent `SentenceRelationRecord`.
  3. `content_pipeline/relation_integrity.py`: Implemented `verify_sentence_relation()` and enhanced `assess_positive()`:
     - **Normative Inversion Veto:** A remediation recommendation cannot be asserted as the cause of a vulnerability or failure condition.
     - **Causal Bridging Check:** Selected source spans must establish that the premise causes the conclusion; independently supported disconnected spans do not prove causal linkage.
     - **Action-Rationale Pattern:** Explicitly allows Action → `since` → Technical Concern justifications (e.g. SWC-104 review advice) when the action is supported and the technical concern is verified.
  4. `content_pipeline/export.py`: The export gate independently extracts and verifies all sentence relation records; ungrounded causal or instrumental links trigger an immediate export veto (`ValueError`).
  5. Deterministic Unit & Export Regressions: Added `test_reproduction_unsupported_causal_connection_fails_export` confirming the exact reviewer reproduction is rejected and blocked from export.

### 5.2 Issue 2 (Medium-High): Full Six-Slot Execution on Corrected Code
- **Finding:** The prior multi-slot run (`output/recall-recovery-week`) was historical and still contained earlier drafts.
- **Remediation:**
  1. Preserved historical runs (`output/recall-recovery-week/`, `output/relation-grounding-week/`) as diagnostic history, explicitly labeled as not publication-cleared.
  2. Launched fresh full six-slot execution on real `qwen3.5:4b` Ollama inference targeting `output/final-integrity-week`.
  3. Updated `audit/scripts/build_recall_recovery_visuals.py` to prioritize `output/final-integrity-week` for diagram, execution trace, and viewer generation.

### 5.3 Issue 3 (Medium): Deterministic Legacy Solidity Scope Enforcement
- **Finding:** SWC-105 constructor naming vulnerabilities applied only to legacy Solidity (< 0.4.22) where constructors shared the contract name. While prompts instructed historical qualification, deterministic version-scope enforcement was missing.
- **Remediation:**
  1. `content_pipeline/relation_integrity.py`: Added `LEGACY_CONSTRUCTOR` and `HISTORICAL_QUALIFIER` regex gates.
  2. Any claim asserting constructor-naming vulnerabilities without explicit historical qualification (`legacy`, `historical`, `pre-0.4.22`, `Solidity < 0.4.22`) is deterministically vetoed.
  3. `tests/test_relation_integrity.py`: Added `test_historical_post2_unqualified_legacy_constructor_fails_export` asserting that the historical unqualified `post_2` draft fails closed and is blocked from export, while qualified legacy assertions pass.

### 5.4 Issue 4: Formal Benchmark Target Status & Empirical Scope
- **Declaration:**
  - The 64-case frozen benchmark achieved **82.35% (28/34)** supported recall, which is formally and transparently declared as **FAILED** against the 85% pre-declared target.
  - Zero false accepts (0/30) on adverse benchmark examples is a finite empirical observation on the 30 tested cases, not mathematical or universal proof of zero false accepts across arbitrary open-domain prose.
  - All gate evaluations and acceptance matrices explicitly reflect these statuses.

---

## 6. Fresh Six-Slot Execution Inspection (`output/final-integrity-week`)

A fresh, full six-slot execution was executed using real local `qwen3.5:4b` Ollama inference on the final remediated codebase, with concurrency=1 and the single-revision limit strictly enforced.

### 6.1 Execution Metrics & Overview
- **Output Directory:** `output/final-integrity-week`
- **Model:** `qwen3.5:4b` (Temperature: 0, Peak Concurrency: 1)
- **Total Runtime:** 2,140.426 seconds (~35.7 minutes)
- **Token Accounting:** 236,238 prompt tokens, 23,353 completion tokens (100% complete)
- **Slot Outcomes:** **6 Planned, 0 Shipped, 6 Dropped, 0 Failed**
- **CSV Output:** `posts.csv` contains exact header `Post Text,Image` and **0 data rows**.
- **Automated Verification:** Passed `audit/semantic/inspect_new_run.py output/final-integrity-week` with exit code 0; all JSON schemas, provenance hashes, byte offsets, and option mappings validated.

### 6.2 Slot-by-Slot Audit of All Six Slots

| Slot ID | Type | Topic & Evidence | Status | Detailed Mechanism & Grounding Verdict |
|---|---|---|---|---|
| `thread_1` | tech-thread | Reentrancy (SWC-107) | **DROPPED** | On Attempt 2, Tweet 5 asserted that *"The Checks-Effects-Interactions pattern orders operations correctly"*. The verifier correctly flagged `INSUFFICIENT_EVIDENCE` against SWC-107: the source defines the pattern by the required action, but does not state that the pattern itself "orders operations correctly" as a standalone factual capability. Dropped after 1 revision. |
| `post_1` | marketing-post | Unchecked Return (SWC-104) | **DROPPED** | Draft asserted that unchecked failures cause execution to continue with unintended effects. The verifier caught this as `INSUFFICIENT_EVIDENCE` against cited span SWC-104, since the source recommends handling the possibility of failure but does not assert continued execution as a direct causal link for the specific review action. Dropped after 1 revision. |
| `thread_2` | tech-thread | Access Control (SWC-105, OZ-OWNABLE) | **DROPPED** | On Attempt 2, the model emitted concatenated tokens without spaces in Tweet 3 (`IfconstructorcodeendsupinruntimebytecodeSolidity04`). This triggered a hard coverage error (`Tweet 3 contains uncovered substantive text`), correctly failing the deterministic format gate. Dropped after 1 revision. |
| `post_2` | marketing-post | Access Control (SWC-105, OZ-OWNABLE) | **DROPPED** | Blocked directly by the new sentence-relation gate: `Sentence relation t1s1rel1 (since): The justification premise does not state a verifiable technical risk or mechanism`. The new gate prevented an ungrounded justification from reaching export. Dropped after 1 revision. |
| `thread_3` | tech-thread | Oracle Manipulation (SCWE-028, OWASP-SC03) | **DROPPED** | In Tweet 4, the draft asserted input validation as an effective mitigation strategy without establishing efficacy against manipulation. The relation gate vetoed it: *"A recommendation alone does not establish claimed mitigation effectiveness"*. Dropped after 1 revision. |
| `post_3` | marketing-post | DoS with Failed Call (SWC-113) | **DROPPED** | The draft asserted that DoS conditions occur specifically *"if they are not managed"*. The verifier sustained `INSUFFICIENT_EVIDENCE`: SWC-113#0 states external calls can fail and cause DoS, but does not assert that unmanaged failures cause DoS. The disjunction between failure and lack of management was not bridged. Dropped after 1 revision. |

### 6.3 Historical Runs vs Final Code Execution Comparison

1. **`output/recall-recovery-week` (Historical Diagnostic Run):**
   - Result: 6 planned, 3 shipped, 3 dropped, 0 failed.
   - Finding: Preserved as diagnostic history, but **NOT publication-cleared**. Its shipped `post_3` contained the ungrounded execution-continuation clause, and `post_2` lacked deterministic legacy version qualification.
2. **`output/integrity-closure-post3` (Isolated Standalone Correction):**
   - Result: 1 planned, 1 shipped, 0 dropped, 0 failed.
   - Text: *"Review how your contract handles low-level call results, since external calls can fail accidentally or deliberately and cause a DoS condition."*
   - Finding: Clean, fully grounded standalone proof that the isolated `post_3` revision eliminates the former execution-continuation defect and passes all semantic and relation gates against SWC-113.
3. **`output/final-integrity-week` (Final Full-Week Code Execution):**
   - Result: 6 planned, 0 shipped, 6 dropped, 0 failed.
   - Finding: Validates that under the complete hardened gates (sentence-relation verification, legacy version-scope enforcement, and atomic decomposition), the system operates strictly **fail-closed**. Zero ungrounded causal assertions, zero unqualified legacy claims, and zero smuggled mechanisms escaped to `posts.csv`.

