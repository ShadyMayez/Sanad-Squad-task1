# Performance & Token Analysis

## 1. Runtime & Resource Metrics Comparison

Below is the comparative analysis across the sequential development passes leading to final qualification:

| Run Configuration | Planned | Shipped | Dropped | Failed | Elapsed Time (s) | Prompt Tokens | Completion Tokens | Peak Concurrency |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **`recall-recovery-week`** | 6 | 3 | 3 | 0 | 2,172.324 | 230,605 | 24,556 | 1 |
| **`final-integrity-week`** (pre-fix R1-R3) | 6 | 0 | 6 | 0 | 2,140.426 | 236,238 | 23,353 | 1 |
| **`final-relation-week`** (current qualification) | 6 | 3 | 3 | 0 | 2,340.803 | 261,046 | 25,000 | 1 |
| **`qualification-tech-test`** | 1 | 1 | 0 | 0 | 416.393 | 57,086 | 5,140 | 1 |
| **`qualification-marketing-test`** | 1 | 1 | 0 | 0 | 142.221 | 19,723 | 1,461 | 1 |

---

## 2. Resource Utilization Analysis

1. **Inference Concurrency & Stability:**
   `peak_simultaneous_ollama_calls` remained strictly at `1` across all runs, adhering to the process concurrency invariant. Zero timeout errors or deadlocks occurred.
2. **Token Efficiency:**
   The weekly run required 261,046 prompt tokens and 25,000 completion tokens across 6 slots, including all atomic extractions, verifier evaluations, skeptical audits, reviewer scorecards, and single revisions.
3. **External Charges:**
   All inference was conducted on local Ollama hardware (`qwen3.5:4b`). External model API charges: **$0.00 USD**.
