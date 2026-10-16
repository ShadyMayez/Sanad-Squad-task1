# Known limitations and next steps

- Python checks pinned snapshot hashes, exact source quotations and claim mappings. A local model makes per-claim semantic judgments, with a second skeptical pass for tentative support. This remains an audit aid, not formal proof. A human should review exported copy before publication.
- The current 4B writers may paraphrase and reorganize supported information, but the model can still add unsupported causality or lose a condition. The atomic verifier, skeptical pass, Reviewer, and Python gates reduce that risk without eliminating it. An editor should review factual scope and style before use.
- On the final 60-case verifier replay, two supported recommendations were rejected; the fresh 20-case holdout rejected two of ten supported claims. The final standalone technical thread also dropped on a disputed paraphrase. These are real false-negative and model-variance costs of the conservative gate, not evidence that every adverse claim will always be caught.
- The offline KB stores attributed source snapshots and URLs. Runtime does not fetch live pages or verify current web availability. The SWC Registry states that its content has not been actively maintained since 2020; refresh older entries against maintained security guidance before production use. OWASP snapshots carry CC BY-SA 4.0 attribution and ShareAlike obligations documented in `source_snapshots/`.
- Topic matching is lexical. Unsupported or ambiguous focuses fail their slot; a future version could add a verified retrieval index with human review of matches.
- Visual output is a written specification, not an image. A scheduler expecting media needs a separate conversion step.
- Only X-specific character and thread rules are implemented. Additional platforms need their own deterministic validator and output contract.
- Token counts depend on Ollama metadata. Local hardware and electricity costs are not estimated.

See [context-quality limitations](audit/context_quality/08_REMAINING_LIMITATIONS.md), [scientific residual risks](audit/semantic/07_LIMITATIONS_AND_RESIDUAL_RISKS.md), and [prompt limitations](audit/prompt_architecture/07_REMAINING_LIMITATIONS.md).

