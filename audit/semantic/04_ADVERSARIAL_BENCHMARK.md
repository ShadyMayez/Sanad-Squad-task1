# Adversarial benchmark protocol (fixed before live scoring)

The labeled fixture `fixtures/benchmark.json` covers categories A–T from the closure directive. It contains both positive and negative examples. Labels reflect direct reading of the pinned source quotations and, for version-sensitive case S, current Solidity guidance. Cases N, P and T use explicitly synthetic fault-injection material; they are not presented as official source quotations. J, P and T test deterministic integrity/failure behavior rather than model semantics.

**Predeclared criterion:** zero unsupported or contradicted claims shipped in deterministic end-to-end fixtures; zero model false accepts on this small labeled benchmark; at least 70% recall on supported examples. Report every departure, including false rejection and exact-label disagreements. This small benchmark cannot establish universal semantic reliability. The model's verdict is a judgment, not proof.

The executable runner records each expected and observed verdict, per-case latency and usage, confusion matrix, supported precision/recall, dangerous false-accept rate, false-reject rate, and category results. No output label will be edited to improve scores after running.

## Observed local-model runs

All runs used the unchanged 20-case A–T fixture and `qwen3.5:4b`. Early versions exposed structured-output failures; the compact one-pass version exposed an actual false entailment. The final two-pass design adds an independent skeptical check of only the selected exact spans. Intermediate outputs are preserved under distinct filenames, not overwritten as evidence.

| Version | Supported recall | False accepts / 15 adverse | Five-label accuracy | Recorded prompt / completion tokens |
|---|---:|---:|---:|---:|
| Initial batched verifier | 1/2 | 0 | 55% | 10,144 / 3,640 |
| Message separation with large output schema | 0/2 | 0 | 70% | 13,810 / 1,957 |
| Compact decision schema, one pass | 2/2 | 1 (case L) | 80% | 20,109 / 1,570 |
| Compact schema plus skeptical selected-span audit | 2/2 | 0 | 80% | 21,755 / 1,905 |
| Joint-span skeptical audit, complete pinned quote | 2/2 | 0 | 85% | 22,663 / 1,846 |
| Canonical SWC-107 source and abbreviation/bullet parser (final) | 2/2 | 0 | 80% | 22,440 / 1,867 |

The final file is `benchmark-post-parser-results.json`; `benchmark-results.json` is the latest generated copy. The final run recorded complete Ollama usage for its 17 actual model cases. Mean wall time per case was 6.189 seconds, including three deterministic fault cases that required no model call. The case labels and fixture JSON remained unchanged; the final run used the canonical SWC-107 Markdown-derived snapshot and corrected abbreviation/bullet segmentation. The preceding complete-quote run is preserved as `benchmark-current-source-results.json`; the earlier clipped-quote run is `benchmark-joint-prequote-results.json`. External model API charges were USD 0; local electricity and hardware cost were not measured.

Four final verdicts disagreed with the expected **rejection category** while still rejecting the claim: D, G, N, and R were called CONTRADICTED instead of INSUFFICIENT_EVIDENCE. Case L was a dangerous false support in the one-pass version; the skeptical audit now rejects it using only the selected remediation spans. The result meets the predeclared zero false-accept and at least 70% supported-recall thresholds on this fixture. Only two positive examples and 15 adverse examples were tested, so the 100% and 0% rates are sample observations, not reliability guarantees. In particular, the model sometimes overuses CONTRADICTED for unsupported claims.
