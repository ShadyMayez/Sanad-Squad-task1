# Standalone Executions & Local Model Probes

## 1. Local Model Probes (Ollama `qwen3.5:4b`)

To ensure the local model reliably distinguishes genuine support from unsupported causal connections under the corrected verification contracts, isolated probes were run against `SemanticVerifier`:

### 1. Positive Causal Probe
- **Claim:** *"External calls can fail, which can cause a DoS condition in the contract."*
- **Candidate Evidence:** SWC-113#0
- **Model Output:**
  - `verdict`: `SUPPORTED`
  - `relation_integrity_passed`: `True`
  - `latency`: 43.80s
  - `reason`: *"The claim 'External calls can fail, which can cause a DoS condition in the contract' is directly supported by span SWC-113#0, which states: 'External calls can fail accidentally or deliberately, which can cause a DoS condition in the contract.'..."*
- **Verdict:** PASSED. Genuine source causality is accurately recognized.

### 2. Negative Spliced Causal Probe (Defect R3)
- **Claim:** *"The contract can lose funds because external calls can fail."*
- **Candidate Evidence:** SWC-105#0 + SWC-113#0
- **Model Output:**
  - `verdict`: `INSUFFICIENT_EVIDENCE`
  - `relation_integrity_passed`: `False`
  - `latency`: 24.80s
  - `reason`: *"Source-to-claim relation gate: Selected source spans independently support isolated clauses but do not establish the asserted causal relationship between premise and conclusion"*
- **Verdict:** PASSED (Failed Closed). Unrelated causal splicing is rejected.

---

## 2. Full Qualification Workflows

### 1. Technical Thread Qualification (`output/qualification-tech-test`)
- **Command:** `.venv/bin/python run_piece.py --type tech-thread --topic "reentrancy" --output output/qualification-tech-test`
- **Model:** `qwen3.5:4b`
- **Result:**
  - `planned`: 1
  - `shipped`: 1
  - `dropped`: 0
  - `failed`: 0
  - `elapsed_seconds`: 416.393
  - `prompt_tokens`: 57,086
  - `completion_tokens`: 5,140
  - `peak_simultaneous_ollama_calls`: 1
- **Shipped Copy:**
  1. *1/5 Calling external contracts can transfer execution to another contract before your current function finishes.*
  2. *2/5 A malicious contract might call back into you while your first invocation is still running.*
  3. *3/5 This allows multiple invocations of the same function to interact in ways that break your logic.*
  4. *4/5 To prevent this, make sure all internal state changes are performed before the call is executed.*
  5. *5/5 Follow the Checks-Effects-Interactions pattern: change state, then interact.*

### 2. Marketing Post Qualification (`output/qualification-marketing-test`)
- **Command:** `.venv/bin/python run_piece.py --type marketing-post --topic "Unprotected Ether Withdrawal" --output output/qualification-marketing-test`
- **Model:** `qwen3.5:4b`
- **Result:**
  - `planned`: 1
  - `shipped`: 1
  - `dropped`: 0
  - `failed`: 0
  - `elapsed_seconds`: 142.221
  - `prompt_tokens`: 19,723
  - `completion_tokens`: 1,461
  - `peak_simultaneous_ollama_calls`: 1
- **Shipped Copy:**
  - *"Review how your contract restricts Ether withdrawals, since missing access controls allow malicious parties to drain funds and wrongly named constructor functions can expose re-initialization risks in legacy Solidity."*
- **Grounding Verification:**
  - Contains valid `since` action rationale.
  - Contains accurate technical hazard premise grounded in SWC-105#0.
  - Contains explicit historical scope qualification (`in legacy Solidity`).
  - Passed all semantic verifier passes, skeptical audit, reviewer review, and export gates.
