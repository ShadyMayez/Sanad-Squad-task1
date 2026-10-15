# Final semantic-grounding closure report

## Baseline and root cause

The historical `output/sample-week/` shipped six pieces, but the independent audit identified five unsupported or overbroad sentences. Citation IDs existed, yet the prior gate did not independently test whether the cited words entailed every public claim. See `01_BASELINE_AND_ROOT_CAUSE.md` and the corrected FAIL rows in `../../ACCEPTANCE_MATRIX.md`.

## Implemented closure

Each KB evidence record now pins a source title, URL, local snapshot path and SHA-256, retrieval date, exact quote, and source offsets. The canonical SWC-107 snapshot preserves official Markdown bullet boundaries and its raw source, while the former flattened snapshot remains for diagnostic-history verification. Abbreviation-aware sentence extraction prevents `ie.` and `a.k.a.` from producing false claim fragments. Python validates these bytes for each selected slot, so one missing source does not stop unrelated work. Public tweet text is independently segmented into atomic clauses with exact offsets and qualifiers. The local model judges each clause against supplied source quotations, selects exact span IDs for tentative support, and a second skeptical call can veto it. Python verifies all selected spans and claim IDs. Non-supported verdicts, provenance failures, deterministic rule violations, adverse Reviewer scores, and export preflight checks block shipping. Verifier failures are distinct from the one allowed content revision. All source content is untrusted task data.

## Measured adversarial evidence

The fixed A–T benchmark has 20 cases: two expected supported, 15 semantic adverse, and three deterministic source/schema faults. The final two-pass local-model result accepted **2/2 supported** and **0/15 adverse**, with **80% exact five-label accuracy**; four adverse labels differed between CONTRADICTED and INSUFFICIENT_EVIDENCE. A one-pass precursor falsely accepted one adverse case, which motivated the skeptical pass. Six source-text prompt-injection probes yielded **0/6 false accepts**. These finite results do not prove universal grounding reliability.

## Real content execution

The first technical diagnostic piece dropped after its allowed revision. The first full six-slot diagnostic week dropped all six; no rejected content entered its CSV or Visual Agent. Source-first Writer prompts, canonical bullet-preserving evidence, abbreviation-aware segmentation, and a bounded Reviewer consistency repair addressed observed failures without forcing approval. The final real technical piece at `output/semantic-final-accepted-piece/` shipped one five-tweet thread with five exact supported spans, an approving Review, visual specification, and CSV row. The final release week at `output/semantic-release-week/` shipped 3, dropped 3, and failed 0; accepted texts, rejected reasons, CSV, and visual specs are inspected in `FINAL_CONTENT_INSPECTION.md` and `06_REAL_OLLAMA_EXECUTION.md`.

## Final acceptance

PASS for the implemented, bounded semantic gate and the observed final run: all three shipped pieces have exact pinned supporting spans, passing Reviews and hard checks; three unsupported or invalid pieces were dropped and excluded from export. This is not a claim of universal semantic correctness. Human editorial review remains necessary before publication because both semantic passes use the same small local model, source snippets can omit context, and the fixed benchmark is narrow. See `07_LIMITATIONS_AND_RESIDUAL_RISKS.md`.
