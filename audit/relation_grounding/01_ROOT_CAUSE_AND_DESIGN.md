# Source-to-claim relation closure

## Reproduced defect

The preserved `output/semantic-context-quality-final-week/` accepted `thread_1` with the tweet “The core risk is that state changes happen after the call, not before.” Its atomic claim `t3s1c1` selected only `SWC-107#3`: “Make sure all internal state changes are performed before the call is executed.” The selected sentence is a remediation instruction. It does not assert that late updates are the defining cause of all reentrancy. The source's separate description says a malicious callee calls back before the first invocation finishes. That context establishes a callback mechanism; it does not turn the selected recommendation into the tweet's general root-cause claim.

The first model returned `SUPPORTED` while its reason said the source was “directly contradicting the claim's assertion”. The skeptical model also returned `SUPPORTED`. The old structured schema had no claim or evidence relation fields, and the Python gate checked provenance, exact span membership, and positive semantic labels but did not compare the *kind* of relationship the claim asserted to the relationship the cited passage supplied. The Reviewer assigned factual support **5/5**, technical correctness **5/5**, and `approved=true`, saying all six claims were fully supported. The exporter correctly obeyed the then-existing gates and put the thread in CSV. The defect was an unsafe semantic judgment, not a forged URL or CSV writer issue.

The next tweet, “To prevent this, perform all internal state updates before making any external calls,” is an imperative that presents the recommended ordering for prevention. SWC-107 does recommend performing state changes before the call. In that imperative form, “To prevent this” expresses the purpose of the recommendation rather than an absolute assurance that it eliminates every reentrancy path. A categorical guarantee such as “Changing state first guarantees all reentrancy is impossible” would require stronger effectiveness evidence and is blocked by the new gate. This reading is narrow; an editor should review any more forceful prevention language.

The historical thread is retained as evidence and is **not publication-cleared**.

## Correction

`ModelSemanticDecision` now requires explicit claim relation types, evidence relation type, relationship verdict, and contradiction/uncertainty flags. Both verifier passes record these fields. Python stores lexical source-role hints for the selected exact spans. The hints are audit metadata; they do not grant support.

`assess_positive` is a veto-only check. A positive decision is invalid if structured fields contradict it or its reason explicitly states that evidence contradicts the claim. A root-cause claim requires a model classification of direct causal support and a selected span with descriptive causal syntax, excluding imperative-only remediation. A recommendation can be supported by a normative instruction. A mitigation guarantee cannot rest on recommendation-only evidence, and absolute certainty must occur in the cited span. The skeptical pass independently assesses the same relation before support is persisted. The exporter reapplies the deterministic check against final selected spans and skeptical fields, so a Reviewer approval or a forged saved pass flag cannot bypass it.

An unsupported relationship becomes `INSUFFICIENT_EVIDENCE`, allowing the existing single Writer revision. An internally contradictory positive becomes `VERIFICATION_ERROR`. Neither can reach the Visual Agent or accepted CSV. The original positive decision, selected span, source-role hints, and gate reason remain in the audit record.

## Limits of deterministic syntax

The Python patterns detect some high-risk inversions; they do not prove arbitrary entailment, resolve all cause/effect reversals, or identify every way of phrasing causality. The model and skeptical pass still carry meaning-level responsibility. Explicit source scope, conditions, and exact quotations remain necessary. The frozen benchmark measures observed local-model behavior and may expose residual false acceptance or false rejection. The benchmark labels were assigned by the implementing engineer against pinned source text; no separate external smart-contract specialist has independently adjudicated them.
