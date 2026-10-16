# Root cause analysis

## Baseline independently checked

`output/semantic-release-week/summary.json` records six planned, three shipped, three dropped, zero failed, 580.873 seconds, 84,640 prompt tokens, 9,980 completion tokens, and peak one Ollama call. Its accepted CSV has three rows. These are saved observations, not a target acceptance rate. The original 20-case benchmark has two supported cases and fifteen adverse model cases; its saved confusion matrix shows 2/2 supported accepted and 0/15 adverse accepted.

## `thread_3` source and decisions

Pinned `SCWE-028` (snapshot SHA-256 `e32ddfe0f4d4aef684ca1aca408949bebf268e37a01e8fadc9d17bdb7c87060c`) says: “Price Oracle manipulation refers to the exploitation of vulnerabilities in price oracles to manipulate contract logic. This can lead to: - Unauthorized actions by malicious actors. - Loss of funds or data.” The quote continues with another listed outcome and remediation. It is located at snapshot code-point offsets 400–830.

On attempt 1, the Writer said “It may cause loss of funds or data within the contract's logic.” The selected option was the isolated loss item, `SCWE-028#2`. “Within the contract's logic” adds a location/relationship not established by that item or the neighboring list. Rejection of this draft was justified.

On attempt 2, the Writer removed that addition: “It may cause loss of funds or data.” The first verifier saw the full `source_quote` and selected `SCWE-028#2`, marking it SUPPORTED. The skeptical verifier received **only** the selected option “Loss of funds or data.” It did not receive the preceding “This can lead to:” or the oracle manipulation antecedent. It vetoed the claim because the item alone lacked a modal and causal link. That was a false negative relative to the full pinned source: “This can lead to” explicitly makes the list a set of possible consequences of price oracle manipulation. The Reviewer repeated the fragment-level objection, and the slot dropped after its one allowed revision.

The failure was at the handoff between initial verification and skeptical verification. The first pass had context; the second pass was deliberately restricted to a fragment. The selected span remained exact, but the second pass could not interpret the span's list relationship. A targeted real Ollama rerun after adding bounded context marked the attempt-2 claim SUPPORTED and recorded both passes and the exact source window. That result does not validate the stronger attempt-1 wording.

## Extractive writing

Both Writer files required every public sentence to use words copied in order from one contiguous source fragment. This prevented meaningful paraphrasing, synthesis, and readable progression. The saved release shows a five-tweet reentrancy thread that largely restates source bullets, a constructor thread with only three tweets, and marketing posts close to checklist items. The source can be sparse; removing the copy rule does not create new supported facts. This constraint likely contributed to low usefulness and the short constructor thread, but the saved run alone cannot quantify its causal effect on rejection frequency. The new policy permits meaning-preserving paraphrase while semantic and deterministic gates remain unchanged.

## Reviewer calibration

The Reviewer rubric equated exact source wording with strong support and sometimes treated short selected fragments as the whole source. It also returned unsupported quote-format objections across all final `thread_3` claims. The correction is to judge factual entailment, technical correctness, clarity, usefulness, brand, and platform separately, using current-draft evidence context. The Python atomic veto still has final authority.

## Additional coreference failure found during evaluation

A separate synthetic, pinned source said, “The oracle and bridge update the price. It can be stale.” The first context-quality probe accepted “The bridge can be stale.” The source's “It” does not unambiguously refer to the bridge; price is a plausible and grammatically nearer referent. This is a dangerous false acceptance in a deliberately ambiguous fixture, even though no public piece was shipped from it. Both semantic prompts now require explicit referent resolution before substituting a named entity for a pronoun. The original probe result is preserved in `supplemental-pre-coreference-results.json`; the revised prompt's result is separately saved. The result does not establish general immunity to pronoun errors.

## Reviewer rendering-contract failure found during real execution

The first updated standalone technical run produced six separate tweet strings with six SUPPORTED atomic claims and no deterministic errors. The Reviewer twice returned `approved=false` while every score passed. It first treated the array as one post, then demanded numbering inside each tweet; both assertions contradicted the CSV rendering contract. The graph failed the slot and exported no content. The root cause was model interpretation of Reviewer task structure, not a fact or platform-rule failure. The rubric and task payload now repeat the rendering facts explicitly; a real recheck approved the same saved draft without changing factual or hard rules.
