# Relation Calibration Design & Compatibility Policy

**Directive ID:** `SANADSQUAD_SEMANTIC_RECALL_RECOVERY_05`  
**Phase:** 3 — Relation Classification Accuracy & Compatibility Policy  
**Module:** `content_pipeline/relation_integrity.py` & `content_pipeline/semantic_verification.py`  
**Status:** Approved & Enforced

---

## 1. Executive Summary

In previous passes (Closure 03 & 04), an over-restrictive relation-grounding policy collapsed supported claim recall to **40%**, with recommendation-paraphrase recall plunging to **25%**. While this successfully blocked the historical safety defect (an unsupported root-cause claim derived from a remediation recommendation in SWC-107), it created severe false rejections. Legitimate paraphrases such as *"Review how your contract handles low-level call results"* were treated as ungrounded causal claims or rejected because the model tagged descriptive context rather than strict normative syntax.

This design establishes a formal **Relation Compatibility Policy** that restores positive claim recognition while preserving the deterministic safeguards against causal inversion, ungrounded effectiveness guarantees, and topical hallucinations.

---

## 2. Seven Distinguished Proposition-Evidence Relation Classes

We establish seven distinct semantic relationship categories with explicit criteria, gate behaviors, and evidence standards:

| Relation Class | Definition & Semantic Boundary | Example Proposition | Example Evidence Span | Gate Action |
|---|---|---|---|---|
| **1. Direct Entailment** | The proposition states a technical fact, mechanism, or consequence directly stated or logically necessitated by the source passage. | *"External calls pass control to untrusted contracts before execution finishes."* | *"calls back to the calling contract before the first invocation of the function is finished"* (`SWC-107`) | **ACCEPT** (Subject to span match & skeptical audit) |
| **2. Faithful Paraphrase** | The proposition restates a source concept using standard domain terminology, equivalent syntax, or a valid subset/modal narrowing, without expanding scope. | *"State variables may be altered unexpectedly when an external call recurses."* | *"the caller may be able to execute other code, including calling back into the original contract, before the original call completes"* (`SWC-107`) | **ACCEPT** (Preserves modal qualifiers: `may`, `might`, `can`) |
| **3. Source-Attributed Recommendation & Review Action** | The proposition communicates recommended practice or invites developer code review based on an authoritative source recommendation or identified hazard. | *"The source recommends updating all contract state before triggering external calls."* / *"Review how your contract orders state updates relative to external calls."* | *"Apply the checks-effects-interactions pattern to ensure all state changes occur before calling external contracts"* (`SWC-107`) | **ACCEPT** (Distinguishes review action from causal assertion; requires normative or hazard-identifying evidence) |
| **4. Safe Preservation of Conditional Scope** | The proposition includes explicitly stated preconditions (`if`, `when`, `unless`) or restricts general consequences to narrower verifiable cases. | *"If a delegatecall target is untrusted, storage layout collisions can corrupt state."* | *"delegatecall executes code in the context of the calling contract, so an untrusted target can modify any storage slot"* (`SWC-112`) | **ACCEPT** (Narrower scope is logically entailed by broader hazard) |
| **5. Unsupported Causal Inference (Causal Inversion)** | The proposition asserts that a specific factor is the *root cause*, *underlying reason*, or *defining risk*, when the cited evidence only describes a recommended remediation or an isolated symptom. | *"The core risk is that state changes happen after the call, not before."* | *"Reentrancy vulnerabilities can be avoided by making all state changes before transferring tokens"* (`SWC-107#3`) | **STRICT VETO** (Historical defect fix; blocks normative span serving as root cause) |
| **6. Unsupported Effectiveness Claims** | The proposition asserts that a tool, technique, or pattern *guarantees* safety, *eliminates* all risk, or *prevents all* vulnerabilities, when the evidence describes a recommendation or partial mitigation. | *"Using ReentrancyGuard completely eliminates all reentrancy attacks."* | *"OpenZeppelin's ReentrancyGuard can help protect functions against reentrant calls"* | **STRICT VETO** (Demands explicit source evidence of absolute certainty) |
| **7. Source-Topic Similarity without Support** | The proposition discusses the same general vulnerability or topic (e.g., reentrancy, access control) but introduces facts, numbers, or mechanisms not present in the pinned evidence. | *"SanadSquad audited over 400 contracts and found 35% had reentrancy bugs."* | *"Reentrancy is an issue where external calls transfer execution flow"* (`SWC-107`) | **STRICT VETO** (Topical overlap is not entailment; unverifiable assertions rejected) |

---

## 3. Relation-Compatibility Matrix

The deterministic gate (`assess_positive` in `content_pipeline/relation_integrity.py`) evaluates the alignment between the **Claim Type**, the **Evidence Type**, the **Model Selected Evidence Relation**, and the **Syntactic Span Features**:

| Claim Type (`claim_relations`) | Allowed Evidence Relations (`evidence_relation`) | Required Syntactic Span Conditions | Disallowed Combinations / Veto Triggers |
|---|---|---|---|
| `ROOT_CAUSE` | `DIRECT_CAUSAL_SUPPORT`, `DIRECT_DESCRIPTIVE_SUPPORT` | Span must match `DIRECT_CAUSAL` regex and **MUST NOT** be pure `NORMATIVE_START`. | VETO if span is purely normative (e.g. *"Apply checks-effects-interactions"* or starts with *"Remediation"*). |
| `MITIGATION_RECOMMENDATION` | `DIRECT_RECOMMENDATION`, `DIRECT_DESCRIPTIVE_SUPPORT`, `CONTEXTUAL_SUPPORT` | Span must match `NORMATIVE_START` or `NORMATIVE_EVIDENCE`, OR describe the hazard being mitigated. | VETO if evidence relation is `INSUFFICIENT_RELATION` or contradicts recommendation. |
| `SOURCE_ATTRIBUTION` | `DIRECT_RECOMMENDATION`, `CONTEXTUAL_SUPPORT` | Span must contain normative advice (`should`, `must`, `recommend`, `remediation`). | VETO if span only describes descriptive history without guidance. |
| `MITIGATION_EFFECTIVENESS` | `DIRECT_DESCRIPTIVE_SUPPORT`, `CONTEXTUAL_SUPPORT` | Span must contain `EFFECTIVENESS` syntax matching claimed scope. | VETO if evidence is purely a recommendation (`DIRECT_RECOMMENDATION`), or lacks certainty backing. |
| `CONSEQUENCE` | `DIRECT_CAUSAL_SUPPORT`, `DIRECT_DESCRIPTIVE_SUPPORT`, `CONTEXTUAL_SUPPORT` | Span describes potential loss, disruption, or unintended state transition. | VETO if claim converts possibility (`may`) into certainty (`will always`) without evidence. |
| `EXECUTION_MECHANISM` | `DIRECT_DESCRIPTIVE_SUPPORT`, `CONTEXTUAL_SUPPORT` | Span describes execution flow, control transfer, or EVM behavior. | VETO if mechanism describes unrelated vulnerability category (e.g., delegatecall vs reentrancy). |

---

## 4. Key Calibrations Applied

### 4.1 Marketing Posts & Review Actions Decoupling
In Closure 04, any sentence containing the word `"Review"` (e.g., *"Review your contract's access controls before deployment"*) was auto-tagged as `SOURCE_ATTRIBUTION` and required explicit source quotes like *"the source recommends"*.
**Calibration:**
- Pure marketing calls to action derived from established technical hazards (e.g., *"Review how state variables are updated prior to external calls"*) are classified as `MITIGATION_RECOMMENDATION` or review actions.
- They are compatible with both `DIRECT_RECOMMENDATION` spans and `DIRECT_DESCRIPTIVE_SUPPORT` spans describing the hazard.
- `SOURCE_ATTRIBUTION` regex is now strictly reserved for explicit attribution phrases (e.g., *"According to the documentation"*, *"The source advises"*).

### 4.2 Causal Descriptions vs. Normative Guidance for Root Causes
In Closure 04, `assess_positive` required `DIRECT_CAUSAL_SUPPORT` exclusively. If the model tagged `DIRECT_DESCRIPTIVE_SUPPORT` on a passage explaining *how* a bug happens (e.g., SWC-106: *"Unprotected SELFDESTRUCT instruction allows anyone to destroy the contract"*), the gate rejected it even though the text had explicit causal syntax (`allows anyone to destroy`).
**Calibration:**
- Both `DIRECT_CAUSAL_SUPPORT` and `DIRECT_DESCRIPTIVE_SUPPORT` are permitted for `ROOT_CAUSE` claims provided the selected span contains descriptive causal syntax (`DIRECT_CAUSAL`) and is not a normative remediation block.
- This maintains 100% protection against the historical defect (`SWC-107#3`) while recognizing legitimate root-cause descriptions.

### 4.3 Preservation of the Historical Closure 04 Defect Fix
The historical defect claim:
```text
Claim: "The core risk is that state changes happen after the call, not before."
Source: SWC-107#3 (Remediation section)
Text: "Reentrancy vulnerabilities can be avoided by making all state changes before transferring tokens..."
```
Under this policy:
1. `ROOT_CAUSE` is detected in the claim via `"core risk"`.
2. The selected span is from the remediation section and matches `NORMATIVE_START` (`"Reentrancy vulnerabilities can be avoided by..."`).
3. Rule 5 (Unsupported Causal Inference) triggers: `assess_positive` observes that the span provides recommendation, not descriptive causal support.
4. **Result:** The claim is strictly **VETOED**. Safety is 100% preserved.

---

## 5. Architectural Invariant

> **Rule:** *Relation classification is auditable metadata and a conservative veto gate; it can NEVER manufacture support for an ungrounded proposition.*
> 
> A claim must pass both:
> 1. Exact textual grounding in pinned, hash-verified source snapshots.
> 2. Independent skeptical audit verifying semantic equivalence and scope preservation.
> 3. Deterministic relation compatibility veto.
