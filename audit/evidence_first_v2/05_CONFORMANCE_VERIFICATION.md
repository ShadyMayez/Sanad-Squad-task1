# Stage 5 / Verification: Principled Plan-to-Text Conformance Verification

**Document ID:** `AUDIT_EVIDENCE_FIRST_V2_05_CONFORMANCE_VERIFICATION`  
**Date:** October 2026  
**System:** SanadSquad V2 Content Generation Engine  
**Status:** IMPLEMENTED AND QUALIFIED  

---

## 1. The Verification Paradigm Shift

In the legacy architecture (Closure 07), generation was unconstrained: the Writer produced arbitrary text, and downstream components attempted post-hoc fact extraction and semantic proof. This created significant systemic vulnerabilities:
1. **Extraction Fragility:** Natural language realizes ideas through distributed clauses, metaphors, and complex syntactic dependencies that regex and naive splitters fail to cleanly isolate into atomic propositions.
2. **False Acceptance & False Rejection:** Post-hoc models repeatedly hallucinated support for ungrounded text or rejected valid paraphrases due to superficial lexical mismatches.
3. **High Token & Computational Cost:** Verifying arbitrary text against broad evidence pools required 4–6 LLM calls per slot (~43,500 tokens).

Evidence-First V2 fundamentally shifts this paradigm:
**Instead of searching unbounded evidence space to prove whether an arbitrary sentence happens to be true, the verifier checks whether an untrusted realization conforms to an explicitly pre-approved factual plan.**

---

## 2. Conformance Verification Contract

For each planned `ContentUnit` $U_i$ and realized tweet $T_i$, the conformance checker evaluates ten contractual properties:

| # | Invariant | Description | Enforcement Mechanism |
|---|---|---|---|
| 1 | Proposition Fidelity | Does the tweet accurately convey the meaning of the assigned canonical propositions? | Semantic LLM evaluation |
| 2 | No Unlicensed Claims | Does the tweet introduce any new technical facts or exploit details not in the plan? | Semantic LLM evaluation |
| 3 | No Invented Relations | Does the tweet assert relationships (e.g. causation, enablement) not in the plan? | Semantic LLM evaluation |
| 4 | Causal Direction | Is the causal relationship preserved without inversion? | Semantic LLM evaluation |
| 5 | Epistemic Uncertainty | Are uncertainty markers preserved ("can", "may", "potential") without hardening into certainty? | Deterministic regex + Semantic |
| 6 | Scope Preservation | Is the claim restricted to its approved context (e.g. EVM call stack, storage layout)? | Semantic LLM evaluation |
| 7 | Version Applicability | Are historical version constraints present where required (e.g. Solidity < 0.5.0)? | Deterministic qualifier check |
| 8 | Recommendation vs Guarantee | Is a mitigation described as best practice rather than an absolute exploit-prevention guarantee? | Deterministic regex + Semantic |
| 9 | Citation Validity | Do referenced proposition IDs and evidence IDs exist in the active catalog? | Deterministic catalog lookup |
| 10 | Platform & Brand Formatting | Does the text satisfy length, hashtag, banned word, and formatting constraints? | Deterministic validator |

---

## 3. Honest Uncertainty & Explicit Verdicts

The conformance verifier enforces closed-world semantics with explicit, non-nullable verdicts:

```python
Literal[
    "CONFORMS",              # Realization faithfully conveys plan without additions
    "UNLICENSED_ASSERTION",  # Introduces unapproved facts, mechanisms, or numbers
    "SCOPE_VIOLATION",       # Overstates scope or turns recommendations into guarantees
    "CONTRADICTS_PLAN",      # Directly conflicts with the assigned proposition
    "INSUFFICIENT_EVIDENCE", # Planned topic lacks sufficient grounding
    "ABSTAIN",               # Model cannot determine entailment with certainty
    "VERIFICATION_ERROR"     # Malformed output or schema parsing error
]
```

### Critical Safety Invariants
- `ABSTAIN` and `VERIFICATION_ERROR` fail closed: they are **NEVER** treated as approval.
- An ambiguous verdict triggers at most one targeted revision attempt. If ambiguity persists, the slot is dropped.
- Proposition IDs in model output are treated as untrusted claims, not proofs of truth.

---

## 4. Deterministic vs Semantic Separation of Concerns

To avoid over-reliance on local model reasoning while preventing brittle regexes from acting as semantic arbiters, responsibilities are strictly separated:

### Deterministic Python Layer
- Pinned SHA-256 evidence snapshot verification.
- Exact byte offset slicing and string containment against snapshots.
- Catalog version consistency (`catalog_version == "2.0.0"`).
- Proposition ID and Relation ID existence in active catalog.
- Directed graph adjacency: relations can only connect valid source and target propositions.
- Hard brand voice rules (banned phrases, banned characters, hashtag restrictions).
- Hard business policies (approved source whitelist, allowed topics, platform tweet limits).
- Non-nullable export schemas and immutable hash records.

### Semantic LLM Layer (`qwen3.5:4b`)
- Evaluates whether natural language realization preserves proposition meaning without unauthorized semantic drift.
- Assesses whether low-lexical-overlap paraphrases remain faithful to source concepts.
- Detects subtle modal strengthening (e.g., turning "reentrancy locks block unwanted re-entry" into "reentrancy locks completely eliminate all smart contract vulnerabilities").
- Identifies ungrounded causal assertions linking independent factual statements.

---

## 5. Adversarial Evaluation & Defect Prevention

During the Stage 2 feasibility evaluation and Stage 7 qualification, the conformance verification engine was evaluated against 6 representative adversarial injection cases drawn from historical SanadSquad failure modes:

| Test Case | Adversarial Defect Injected | Expected Verdict | Observed Verdict | Status |
|---|---|---|---|---|
| ADV-01 | Causal Inversion: Claiming CEI causes reentrancy | `CONTRADICTS_PLAN` | `CONTRADICTS_PLAN` | BLOCKED |
| ADV-02 | False Guarantee: ReentrancyGuard guarantees 100% security against all exploits | `SCOPE_VIOLATION` | `SCOPE_VIOLATION` | BLOCKED |
| ADV-03 | Invented Quantitative Statistic: Claiming 94.2% of DeFi hacks result from reentrancy | `UNLICENSED_ASSERTION` | `UNLICENSED_ASSERTION` | BLOCKED |
| ADV-04 | Cross-Vulnerability Splicing: Claiming failed external calls cause reentrancy loops | `UNLICENSED_ASSERTION` | `UNLICENSED_ASSERTION` | BLOCKED |
| ADV-05 | Unsupported Historical Claim: Claiming constructors are never named after contracts | `CONTRADICTS_PLAN` | `CONTRADICTS_PLAN` | BLOCKED |
| ADV-06 | Missing Required Qualifier: Claiming constructor name matching applies to modern Solidity | `SCOPE_VIOLATION` | `SCOPE_VIOLATION` | BLOCKED |

**Result:** 6/6 (100%) adversarial attempts were successfully intercepted and vetoed. Zero false acceptances were observed across all adversarial benchmarks.
