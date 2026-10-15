# Final prompt-engineering report

## A. Previous weaknesses

The historical pipeline put instructions and dynamic source text into similar prompt context, used broad task statements without clear role boundaries, and relied on Reviewer citation-string checks that did not establish entailment. Its six shipped sample pieces later yielded five unsupported or overbroad sentences.

## B. Agent prompt design

The Technical Writer, Marketing Writer, Reviewer, Semantic Verifier, and skeptical auditor have separate editable instructions with identity, mission, position, evidence boundary, procedure, structured output, examples, and failure behavior. The latest Writer prompts prefer near-extractive public source statements and prohibit converting a recommendation into an unstated causal guarantee. The Reviewer scores six rubric dimensions and ties adverse reasons to the current draft.

## C. Message integration

LangChain `SystemMessage` carries trusted, file-loaded agent instructions. `HumanMessage` carries structured slot, brand, feedback, and pinned source data. Legacy KB summaries are withheld from Writer and Reviewer factual context. `LocalModel` preserves this split through its single configured ChatOllama factory, timeout, bounded retry, and shared inference limit.

## D. Evidence verification

Python pins source snapshot bytes and extracts all public atomic claims. The first model pass selects exact source spans; a second skeptical pass can veto support. Deterministic and Reviewer gates remain independent. A fabricated Reviewer quote cannot approve; omission of a redundant Reviewer quote may pass only when the complete atomic semantic report has verified spans and the Reviewer itself approves. The Reviewer sees measured tweet-array structure and a compact semantic brief. A high-score rejection without a failed mandatory gate triggers one bounded consistency re-evaluation, then a slot failure if it remains contradictory.

## E. Visual Agent

The Visual Agent receives accepted text, topic, claims, source IDs, and final supported verdicts. It writes a content-dependent image specification and refuses unsupported or failed input. The reentrancy diagram recognizes the accepted phrase “calls back”; the unchecked-call diagram says “return value” rather than an unstated “success flag”; recipient-initiated transaction isolation gets a distinct grounded layout. No actual image is generated.

## F. Prompt evaluation

The current deterministic suite has **68 passing tests**. A fixed 20-case real-model semantic benchmark accepted 2/2 supported and 0/15 adverse cases, with 80% exact five-label accuracy. Six real-model source-text injection probes produced 0/6 false accepts. See `05_PROMPT_EVALUATION_RESULTS.md` and the benchmark records.

## G. Real Ollama regression

The first corrected-architecture week dropped all six slots and exported no content, exposing source-overreach in Writer text. A later complete real technical piece shipped one grounded five-tweet thread after the source and Reviewer integration fixes. The final release run shipped 3, dropped 3, and failed 0 in 580.873 seconds. The three shipped texts have grounded final claims, passing Reviews, and source-aware written visuals; see `06_END_TO_END_REGRESSION.md` and `../semantic/FINAL_CONTENT_INSPECTION.md`. Do not attribute differences from the historical six-of-six sample to prompts alone: provenance, claim extraction, verification, and prompt boundaries changed together.

## H. Workflow visualization

`../visuals/workflow_viewer.html` is a local read-only viewer of the implemented graph and measured run. `../visuals/workflow.png` and `../visuals/execution_trace.png` are standalone images. The viewer never publishes or edits content.

## I. Remaining limitations

A 4B model can misjudge entailment, and its two passes share correlated errors. The benchmark is small, snapshots may be dated or omit context, and the deterministic Visual Agent has a limited design vocabulary. See `07_REMAINING_LIMITATIONS.md`.

## J. Acceptance verdict

PASS for the prompt/message architecture, bounded gates, and the observed final local run. The final suite passed 68 tests, the fixed benchmark showed 0/15 adverse false accepts and 2/2 supported recall, and the final six-slot run shipped 3 grounded pieces while correctly dropping 3. These finite checks do not establish universal factual correctness or production publishing readiness.
