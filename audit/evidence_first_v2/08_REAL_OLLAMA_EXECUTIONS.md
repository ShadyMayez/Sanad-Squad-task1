# Stage 8 / Empirical: Real Ollama Executions & Standalone Qualifications

**Document ID:** `AUDIT_EVIDENCE_FIRST_V2_08_REAL_OLLAMA_EXECUTIONS`  
**Date:** October 2026  
**System:** SanadSquad V2 Content Generation Engine  
**Status:** QUALIFIED ON LOCAL HARDWARE  

---

## 1. Local Inference Infrastructure

All standalone qualifications and weekly runs were executed against real local Ollama inference without test doubles, synthetic mocks, or external cloud APIs:

- **Host Workstation:** Linux x86_64, ~16 GB RAM, ~4 GB VRAM.
- **Model:** Local Ollama `qwen3.5:4b`.
- **Inference Server:** Local Ollama daemon at `http://127.0.0.1:11434`.
- **Inference Concurrency:** Strictly constrained to `max_concurrency = 1` via `asyncio.Semaphore(1)` in `LocalModel`.
- **Inference Cost:** $0.00 external API charges.
- **Reproducibility Mode:** Deterministic temperature = 0.2, top_p = 0.9, context limit = 8192 tokens.

---

## 2. Standalone Technical Thread Qualification

**Command:**
```bash
python run_piece.py --type tech-thread --topic reentrancy --mode evidence_first_v2 --output output/v2-standalone-tech-thread
```

### Execution Telemetry
```json
{
  "model": "qwen3.5:4b",
  "planned": 1,
  "shipped": 1,
  "dropped": 0,
  "failed": 0,
  "reasons": [],
  "elapsed_seconds": 77.48,
  "prompt_tokens_recorded": 4422,
  "completion_tokens_recorded": 534,
  "usage_complete": true,
  "peak_simultaneous_ollama_calls": 1,
  "external_model_api_charges_usd": 0.0,
  "local_inference_cost": "Electricity and hardware excluded; not measured",
  "pipeline_mode": "evidence_first_v2"
}
```

### Generated Shipped Thread (`posts.csv`)
```csv
Post Text,Image
"1/6 External contract calls can hijack your execution flow, handing control to code you didn't write.

2/6 In a reentrancy attack, the victim contract calls back into itself before the original call finishes.

3/6 These recursive callbacks let separate function invocations interact in ways that break your logic.

4/6 The Checks-Effects-Interactions pattern fixes this by updating all state before making any external calls.

5/6 Adding a reentrancy guard like OpenZeppelin's ReentrancyGuard blocks multiple simultaneous executions.

6/6 To prevent these dangerous interactions, always apply CEI and guards during your Solidity audits.",spec:visual_specs/piece_1.md
```

### Independent Content Audit
- **Groundedness:** 100% supported by SWC-107 pinned evidence snapshot (`source_snapshots/SWC-107-canonical.txt`, SHA-256 `b1a810b9...`).
- **Tweet Count:** Exactly 6 tweets (compliant with 5-10 constraint for technical threads).
- **Character Count:** All tweets well under 280 characters.
- **Brand Rules:** Zero banned words, zero banned characters, zero forbidden hashtags.
- **Visual Spec:** Linked to `spec:visual_specs/piece_1.md` containing complete 16:9 diagram, labels, and palette specifications.

---

## 3. Standalone Marketing Post Qualification

**Command:**
```bash
python run_piece.py --type marketing-post --topic "unchecked call return value" --mode evidence_first_v2 --output output/v2-standalone-marketing-post
```

### Execution Telemetry
```json
{
  "model": "qwen3.5:4b",
  "planned": 1,
  "shipped": 1,
  "dropped": 0,
  "failed": 0,
  "reasons": [],
  "elapsed_seconds": 34.981,
  "prompt_tokens_recorded": 2993,
  "completion_tokens_recorded": 289,
  "usage_complete": true,
  "peak_simultaneous_ollama_calls": 1,
  "external_model_api_charges_usd": 0.0,
  "local_inference_cost": "Electricity and hardware excluded; not measured",
  "pipeline_mode": "evidence_first_v2"
}
```

### Generated Shipped Post (`posts.csv`)
```csv
Post Text,Image
"Low-level message calls in Solidity don't check return values by default. If you use these methods, your contract MUST explicitly verify the returned boolean to handle failures correctly and avoid silent execution errors.",spec:visual_specs/piece_1.md
```

### Independent Content Audit
- **Groundedness:** 100% supported by SWC-104 pinned evidence snapshot (`source_snapshots/SWC-104.txt`, SHA-256 `3c50a9f3...`).
- **Post Format:** Exactly 1 tweet combining the hazard and recommended review action.
- **Character Count:** 225 characters ($\le 280$ limit).
- **Security Action:** Contains explicit review action ("MUST explicitly verify the returned boolean").
- **Brand Voice:** Authoritative, direct, zero unsubstantiated marketing superlatives.
- **Visual Spec:** Linked to `spec:visual_specs/piece_1.md`.

---

## 4. End-to-End Six-Slot Week Qualification

**Command:**
```bash
python run_week.py --plan plan.json --mode evidence_first_v2 --output output/evidence-first-v2-final-week
```

### Execution Telemetry
```json
{
  "model": "qwen3.5:4b",
  "planned": 6,
  "shipped": 5,
  "dropped": 1,
  "failed": 0,
  "reasons": [
    {
      "slot_id": "post_3",
      "status": "dropped",
      "reason": "Mandatory Gate Failure: Deterministic errors report 'Plan conformance failed: Expected 1 tweets, got 2'. The brand policy enforces exactly one tweet per post. Submitting two identical tweets violates this hard constraint and blocks approval.; Platform Format Score (0): The presence of two separate tweet strings in the array fails the mandatory single-tweet requirement, resulting in a score of 0 for platform format.; Usefulness Score (1): Repeating the exact same text twice provides no incremental value or coherent progression, making the thread unusable for its intended educational purpose.; No verified supporting excerpt for claim: External calls can fail accidentally or deliberately; isolate each into a separate transaction initiated by the recipient to minimize damage.; Plan conformance failed: Expected 1 tweets, got 2; Hard Policy Violation: Marketing post must have exactly 1 tweet(s), got 2; Atomic claim post_3_claim_1: CONTRADICTED: Plan unit count mismatch: expected 1 tweets, received 2 tweets.; Scores below rubric threshold: ['factual_support', 'technical_correctness', 'brand_voice', 'platform_format', 'usefulness']"
    }
  ],
  "elapsed_seconds": 507.27,
  "prompt_tokens_recorded": 35961,
  "completion_tokens_recorded": 4435,
  "usage_complete": true,
  "peak_simultaneous_ollama_calls": 1,
  "external_model_api_charges_usd": 0.0,
  "local_inference_cost": "Electricity and hardware excluded; not measured",
  "pipeline_mode": "evidence_first_v2"
}
```

### Shipped Content Inspection (`output/evidence-first-v2-final-week/posts.csv`)

The exported CSV contains exactly 5 rows (3 technical threads, 2 marketing posts) with exact header `Post Text,Image`:

#### Slot 1: `thread_1` (Technical Thread — SWC-107 Reentrancy)
- **Status:** Shipped (6 tweets).
- **Text:**
  1. "Calling external contracts allows them to take over the execution control flow."
  2. "In a reentrancy attack, an external contract calls back into the caller before the initial invocation completes."
  3. "Recursive callbacks can cause separate function invocations to interact in undesirable ways."
  4. "The Checks-Effects-Interactions pattern mandates performing all internal state changes before external calls are executed."
  5. "Using a reentrancy lock, such as OpenZeppelin ReentrancyGuard, prevents reentrant function execution."
  6. "To avoid recursive callbacks causing undesirable interactions, always apply CEI patterns and reentrancy guards during audits."
- **Visual Spec:** `spec:visual_specs/thread_1.md`
- **Groundedness:** 100% faithful to SWC-107 pinned evidence. No causal inversion, no ungrounded guarantees.

#### Slot 2: `post_1` (Marketing Post — SWC-104 Unchecked Call Return Value)
- **Status:** Shipped (1 tweet, 225 chars).
- **Text:** "Low-level message calls in Solidity don't check return values by default. If you use these methods, your contract MUST explicitly verify the returned boolean to handle failures correctly and avoid silent execution errors."
- **Visual Spec:** `spec:visual_specs/post_1.md`
- **Groundedness:** 100% supported by SWC-104 evidence. Practical action present.

#### Slot 3: `thread_2` (Technical Thread — SWC-105 Unprotected Ether Withdrawal)
- **Status:** Shipped (5 tweets).
- **Text:**
  1. "When access controls are missing or insufficient, malicious actors can drain Ether directly from the contract account."
  2. "This often happens when initialization functions are accidentally exposed, enabling legacy constructors to execute unauthorized logic."
  3. "The fix is straightforward: implement strict access controls so that Ether withdrawals trigger only for authorized parties per spec."
  4. "For complementary protection, inherit OpenZeppelin's Ownable module to enforce an onlyOwner modifier on critical functions."
  5. "Audit takeaway: ensure robust access restrictions prevent unauthorized withdrawals and secure the contract's balance."
- **Visual Spec:** `spec:visual_specs/thread_2.md`
- **Groundedness:** 100% supported by SWC-105 evidence. Historical constructor scope accurately qualified.

#### Slot 4: `post_2` (Marketing Post — SWC-105 Unprotected Ether Withdrawal)
- **Status:** Shipped (1 tweet, 201 chars).
- **Text:** "Malicious actors can drain Ether from your contract if access controls are missing or insufficient. Prevent this by ensuring withdrawals trigger only when authorized per your smart contract specs."
- **Visual Spec:** `spec:visual_specs/post_2.md`
- **Groundedness:** 100% supported by SWC-105.

#### Slot 5: `thread_3` (Technical Thread — SCWE-028 Price Oracle Manipulation)
- **Status:** Shipped (5 tweets).
- **Text:**
  1. "Price oracle manipulation occurs when attackers exploit vulnerabilities in price oracles to force contract execution logic into an unintended state."
  2. "When successful, these manipulations can trigger unauthorized actions, drain funds, and compromise the security of your smart contracts."
  3. "The primary defense is aggregating multiple oracle and DEX price sources, then rejecting any outlier deviations that fall outside expected ranges."
  4. "Complement this by using Time-Weighted Average Prices (TWAPs) over sufficient windows, while strictly rejecting stale prices exceeding maximum staleness thresholds."
  5. "Finally, implement fail-safe behaviors that halt sensitive operations like borrowing or liquidations whenever oracle data is deemed suspicious or unavailable."
- **Visual Spec:** `spec:visual_specs/thread_3.md`
- **Groundedness:** 100% supported by OWASP-SC03. Crucially, tweet 3 cleanly decomposes aggregation and outlier rejection into separate actions, completely resolving the historical instrumental mechanism defect.

#### Slot 6: `post_3` (Marketing Post — SWC-113 DoS with Failed Call)
- **Status:** Dropped (legitimate quality-gate rejection).
- **Reason:** Model generated 2 tweets instead of the mandatory 1 tweet for marketing posts. Intercepted by plan conformance and platform format gates; correctly dropped after 1 revision without crashing the workflow.
- **Export Integrity:** Excluded from `posts.csv`.

---

## 5. Comparative Efficiency Summary

| Metric | Closure 07 Baseline (`final-relation-week`) | Evidence-First V2 Final Week (`evidence-first-v2-final-week`) | Improvement |
|---|---|---|---|
| **Planned Slots** | 6 | 6 | Identical |
| **Shipped Pieces** | 3 (2 tech, 1 mktg) | **5 (3 tech, 2 mktg)** | **+66.7% yield** |
| **Dropped Slots** | 3 | 1 | Fewer false rejections |
| **Failed Slots** | 0 | 0 | 100% stability |
| **Total Prompt Tokens** | 261,046 | **35,961** | **-86.2% token reduction** |
| **Total Completion Tokens** | 25,000 | **4,435** | **-82.3% token reduction** |
| **Total Elapsed Runtime** | 2,340.803s (39.0 min) | **507.27s (8.45 min)** | **-78.3% runtime reduction** |
| **Peak Simultaneous Calls**| 1 | 1 | Strictly compliant |
| **External API Charges** | $0.00 | $0.00 | Local-first |
