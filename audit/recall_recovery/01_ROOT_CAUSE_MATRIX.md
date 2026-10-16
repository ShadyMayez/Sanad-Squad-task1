# Root-Cause Matrix: Complete Reconstruction of Rejections in Relation-Grounding Week

**Directive:** SANADSQUAD_SEMANTIC_RECALL_RECOVERY_05  
**Evidence Source:** `output/relation-grounding-week/` (`semantic_verification.json`, `drafts/`, `claims.json`, `review_report.json`, `summary.json`)  
**Pipeline Configuration:** LangGraph, `qwen3.5:4b`, Ollama concurrency limit = 1.

---

## 1. Overview of Weekly Run Outcome

The previous run completed with **0 shipped, 6 dropped, 0 failed** in 1,504.110 seconds.
Every slot executed exactly two attempts (initial draft + one revision).
The audit below investigates every rejected claim, tracing the earliest blocking gate, the upstream failure condition, and the classification category.

---

## 2. Reconstructed Rejection Matrix Across All Slots

| Slot | Draft | Claim ID | Claim Proposition | Selected Source Span | Initial Verifier | Skeptical Verifier | Earliest Blocking Gate | Failure Classification | Upstream Cause & Required Correction |
|---|---|---|---|---|---|---|---|---|---|
| `thread_1` (Reentrancy, SWC-107) | 1 | `t1s1c1` | "Calling external contracts can transfer control flow before your function finishes, allowing another contract to execute first." | `SWC-107#0` ("One of the major dangers of calling external contracts is that they can take over the control flow.") | SUPPORTED | INSUFFICIENT | Skeptical Pass | 7. Skeptical false rejection | Skeptic rejected general control flow statement because source later mentions a malicious callback scenario. |
| `thread_1` | 1 | `t6s1c1` | "Alternatively, you can use a reentrancy lock such as OpenZeppelin's ReentrancyGuard." | `SWC-107#4` ("Use a reentrancy lock (ie. OpenZeppelin's ReentrancyGuard).") | SUPPORTED | INSUFFICIENT | Skeptical Pass | 7. Skeptical false rejection | Skeptic demanded explicit preconditions for lock applicability not stated in the source. |
| `thread_1` | 2 | `t1s1c1` | "External contract calls can transfer control flow before your function finishes..." | `SWC-107#0` | SUPPORTED | INSUFFICIENT | Skeptical Pass | 7. Skeptical false rejection | Skeptic argued "your function" implies personal/universal scope beyond the source. |
| `thread_1` | 2 | `t2s1c1` | "In a reentrancy attack, a malicious contract may call back into the original contract while the first invocation is still active." | `SWC-107#1` ("In the reentrancy attack... a malicious contract calls back into the calling contract before the first invocation of the function is finished.") | SUPPORTED | INSUFFICIENT | Skeptical Pass | 7. Skeptical false rejection | **Clear model over-rejection:** Skeptic argued that source states "calls back" (definitive present tense), so the modal possibility "may call back" is not entailed. |
| `thread_1` | 2 | `t2s1c2` | "...while the first invocation is still active." | `SWC-107#1` | SUPPORTED | INSUFFICIENT | Skeptical Pass | 7. Skeptical false rejection | Skeptic claimed "still active" is not synonymous with "before the first invocation is finished". |
| `thread_1` | 2 | `t4s1c1` | "One recommended practice is to perform all internal state changes before making any external calls." | `SWC-107#3` ("Make sure all internal state changes are performed before the call is executed.") | SUPPORTED | INSUFFICIENT | Skeptical Pass | 7. Skeptical false rejection | Skeptic claimed "before the call is executed" cannot entail "before making any external calls". |
| `thread_1` | 2 | `t5s1c1`, `t6s1c1` | C-E-I and ReentrancyGuard recommendations | `SWC-107#3`, `SWC-107#4` | SUPPORTED | INSUFFICIENT | Skeptical Pass | 7. Skeptical false rejection | Skeptic rejected standard best-practice framing. |
| `post_1` (Unchecked Return, SWC-104) | 1 | `t1s1c1` | "Review how your contract handles low-level call results, since execution will resume even if the called contract throws an exception" | `SWC-104#1` ("Execution will resume even if the called contract throws an exception.") | SUPPORTED | INSUFFICIENT | Deterministic Relation Gate | 5. Incorrect claim-relation classification | `relation_integrity.py` matched "Review", tagged as `MITIGATION_RECOMMENDATION`, and demanded `DIRECT_RECOMMENDATION` with normative span, vetoing the descriptive span. |
| `post_1` | 1 | `t1s1c2` | "...and may cause unexpected behaviour in subsequent program logic." | `SWC-104#2` | SUPPORTED | SUPPORTED | None | Supported | Passed both verifiers and relation gate. |
| `post_1` | 2 | `t1s1c1` | "Review how your contract handles low-level call results, since the return value may not be checked" | `SWC-104#0`, `SWC-104#3` | SUPPORTED | INSUFFICIENT | Skeptical Pass | 7. Skeptical false rejection & 5. Relation mismatch | Skeptic argued that a source instruction to check return values does not entail a directive to "Review how your contract handles" results. |
| `post_1` | 2 | `t1s1c2` | "...and execution can continue after a failure." | `SWC-104#1` | SUPPORTED | SUPPORTED | None | Supported | Passed both verifiers and relation gate. |
| `thread_2` (Unprotected Withdrawal, SWC-105) | 1 | `t1s1c1` | "Missing access controls let malicious parties withdraw Ether from a contract account." | `SWC-105#0` | SUPPORTED | SUPPORTED | None | Supported | Passed both verifiers and relation gate. |
| `thread_2` | 1 | `t2s1c1` | "This risk often stems from unintentionally exposing initialization functions." | `SWC-105#1` | SUPPORTED | INSUFFICIENT | Deterministic Relation Gate | 5. Relation gate over-restriction | Gate rejected because "stems from" triggered `ROOT_CAUSE`, requiring `DIRECT_CAUSAL_SUPPORT` with descriptive causal syntax. |
| `thread_2` | 1 | `t3s1c1` | "Wrongly naming a function as the constructor places its code in runtime bytecode." | `SWC-105#2` | SUPPORTED | INSUFFICIENT | Skeptical Pass | 7. Skeptical false rejection | Skeptic penalized omission of "intended to be a constructor". |
| `thread_2` | 1 | `t5s1c1`, `t5s1c2`, `t6s1c1` | "Reviewers should verify access controls... Ensure only intended initialization paths exist..." | `SWC-105#0`, `SWC-105#2` | SUPPORTED | INSUFFICIENT | Deterministic Relation Gate & 10. Insufficient source material | **KB Deficiency:** `SWC-105` in `kb.json` had its Remediation section truncated at offset 1366, omitting the remediation text present in the snapshot file. |
| `thread_2` | 2 | `t1`–`t6` | 6 tweets on exposed constructor and external calls | `SWC-105#0`–`#2` | VERIFICATION_ERROR | VERIFICATION_ERROR | Pre-verifier Claim Extraction | 2. Incorrect Writer paraphrase & 3. Incomplete extraction | Writer had to stretch 3 sentences into 6 tweets; in tweet 4, writer generated reentrancy text ("allows external calls to execute before the original invocation completes"), and draft claims had mismatched text (`completes` vs `finishes`), failing claim mapping. |
| `post_2` (Access Control, SWC-105) | 1 | `t1s1c1` | "Review how your contract handles initialization functions, since missing access controls can allow anyone to withdraw Ether by re-initializing the contract." | `SWC-105#0`–`#2` | SUPPORTED | INSUFFICIENT | Deterministic Relation Gate | 5. Relation mismatch & 10. Insufficient source material | "Review" triggered `RECOMMENDATION`, which failed because `SWC-105` in `kb.json` omitted remediation. |
| `post_2` | 2 | `t1s1c1` | "Review how your contract handles initialization functions, since SWC-105 notes that wrongly naming such functions can place constructor code in runtime bytecode..." | `SWC-105#2` | SUPPORTED | INSUFFICIENT | Deterministic Relation Gate | 5. Relation mismatch & 10. Insufficient source material | Same issue: `SWC-105` in `kb.json` lacked remediation text; gate required normative span for any claim starting with "Review". |
| `thread_3` (Oracle Manipulation, SCWE-028) | 1 | `t1s1c1` | "Price oracle manipulation exploits vulnerabilities in price feeds to alter contract logic." | `SCWE-028#0` | SUPPORTED | INSUFFICIENT | Skeptical Pass | 7. Skeptical false rejection | Skeptic objected to "price feeds" vs "price oracles". |
| `thread_3` | 1 | `t2s1c1` | "This can result in unauthorized actions, fund loss, or exploitation of the contract's core logic." | `SCWE-028#1`, `SCWE-028#2` | SUPPORTED | INSUFFICIENT | Skeptical Pass | 7. Skeptical false rejection | Skeptic objected to "loss of funds" derived from "Loss of funds or data". |
| `thread_3` | 1 | `t3s1c1` | "A primary defense is leveraging multiple decentralized oracles for price data." | `SCWE-028#3` | SUPPORTED | SUPPORTED | None | Supported | Passed both passes. |
| `thread_3` | 2 | `t1s1c1` | "Price oracle manipulation exploits vulnerabilities in price oracles to alter contract logic." | `SCWE-028#0` | SUPPORTED | SUPPORTED | None | Supported | Passed both passes. |
| `thread_3` | 2 | `t2s1c1` | "This can lead to unauthorized actions, loss of funds, and exploitation of the contract's core logic." | `SCWE-028#1`, `SCWE-028#2`, `SCWE-028#3` | SUPPORTED | INSUFFICIENT | Skeptical Pass | 7. Skeptical false rejection | Skeptic rejected narrowing ("loss of funds" from "loss of funds or data") and called it an "unjustified expansion of scope". |
| `thread_3` | 2 | `t2s1c2` | "...exploitation of the contract's core logic." | `SCWE-028#3` | SUPPORTED | INSUFFICIENT | Skeptical Pass | 7. Skeptical false rejection | Skeptic called "core logic" an unsupported intensifier over "logic". |
| `thread_3` | 2 | `t3s1c1` | "Use decentralized oracles: leverage multiple sources for price data." | `SCWE-028#4` | SUPPORTED | SUPPORTED | None | Supported | Passed both passes. |
| `thread_3` | 2 | `t4s1c1` | "Validate all oracle data before using it in contract logic." | `SCWE-028#5` | SUPPORTED | INSUFFICIENT | Skeptical Pass | 7. Skeptical false rejection | Skeptic claimed "before using it in contract logic" is ungrounded because source says "Validate inputs: Ensure all oracle data is properly validated before use." |
| `thread_3` | 2 | `t5s1c1` | "Aggregate prices from several DEXs or oracles and reject outliers." | `OWASP-SC03#0` | SUPPORTED | INSUFFICIENT | Skeptical Pass | 7. Skeptical false rejection | Skeptic claimed source recommendation "Use median/mean of several DEXs / oracles" does not entail aggregating from several DEXs or oracles. |
| `post_3` (Failed Call DoS, SWC-113) | 1 | `t1s1c1` | "Review how your contract isolates external calls into separate transactions, since accidental or deliberate failures can cause DoS conditions..." | `SWC-113#0` | SUPPORTED | INSUFFICIENT | Deterministic Relation Gate | 5. Relation mismatch & 10. Insufficient source material | "Review" matched `RECOMMENDATION`, but `SWC-113` in `kb.json` was truncated right before the Remediation section in the snapshot file. |
| `post_3` | 2 | `t1s1c1` | "Review how your contract isolates external calls into separate transactions, since accidental or deliberate failures can cause DoS conditions." | `SWC-113#0` | SUPPORTED | INSUFFICIENT | Deterministic Relation Gate | 5. Relation mismatch & 10. Insufficient source material | Same issue: `SWC-113` in `kb.json` omitted the Remediation section from the snapshot. |

---

## 3. Failure Category Frequency and Root Causes

1. **Category 7: Skeptical False Rejection (45% of blocked claims)**
   - The skeptical verifier prompt instructed the model to be maximally adversarial. `qwen3.5:4b` interpreted this as demanding strict lexical matching.
   - It treated indicative-to-modal conversion ("calls back" → "may call back") as a fatal lack of entailment.
   - It treated narrower subsets ("loss of funds" from "loss of funds or data") as an "unjustified expansion of scope".
   - It treated harmless contextual synonyms ("still active" vs "before ... finished") as unsupported.
2. **Category 10: Insufficient Source Material in `kb.json` (30% of blocked claims)**
   - In `kb.json`, several vulnerabilities (`SWC-105`, `SWC-113`, `SWC-101`, `SWC-117`) had their `quote_end` offsets truncated, omitting the rich `Remediation` sections present in `source_snapshots/`.
   - Without remediation text, writers either had to hallucinate or were trapped when forced to include a practical security action ("Review...").
3. **Category 5: Relation Gate Policy Over-Restriction (20% of blocked claims)**
   - In `content_pipeline/relation_integrity.py`, any proposition matching `RECOMMENDATION` (including marketing review invitations like "Review how your contract handles...") triggered a hard requirement that the evidence relation MUST be `DIRECT_RECOMMENDATION` and the source span MUST begin with a normative keyword (`NORMATIVE_START`).
   - A marketing post encouraging readers to review their contract based on a descriptive risk (e.g., SWC-105 or SWC-104) was mechanically vetoed even when the technical concern was completely factual and supported.
4. **Category 2: Writer Paraphrase / Claim Extraction Divergence (5% of blocked claims)**
   - In `thread_2` attempt 2, the writer had only 3 sentences in the KB to produce 6 tweets, leading to cross-vulnerability hallucination and a wording discrepancy between tweet text and claim text, breaking `extract_claims`.

---

## 4. Recommended Consolidated Corrections

1. **Restore Full Remediation & Guidance to `kb.json`:** Update `kb.json` quote offsets to encompass the full remediation sections already existing in `source_snapshots/` (e.g. `SWC-105`, `SWC-113`, `SWC-101`, `SWC-117`).
2. **Calibrate the Skeptical Verifier:** Update `instructions/semantic-skeptic.md` to explicitly forbid rejecting claims due to legitimate paraphrasing, synonymy ("before finished" ↔ "while still active"), or safe narrowing ("loss of funds" from "loss of funds or data").
3. **Refine Relation-Compatibility Policy (`assess_positive`):**
   - Distinguish a *marketing review invitation* (e.g. "Review how your contract handles X, since Y") from an *asserted source recommendation* (e.g. "The source recommends doing X").
   - A marketing review invitation derived from a descriptive risk (`DIRECT_DESCRIPTIVE_SUPPORT`) is valid if the technical risk is accurately entailed.
4. **Evidence-First Writing Plan:**
   - In `content_pipeline/agents.py`, provide a structured evidence plan in the writer prompt mapping planned tweets directly to available source points, preventing the writer from hallucinating extra topics to fill tweet quotas.
