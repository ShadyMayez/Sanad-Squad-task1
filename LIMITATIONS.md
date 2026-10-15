# Known limitations and next steps

- Python checks pinned snapshot hashes, exact source quotations and claim mappings. A local model makes per-claim semantic judgments, with a second skeptical pass for tentative support. This remains an audit aid, not formal proof. A human should review exported copy before publication.
- The current 4B writer is instructed to stay close to public source wording after live tests showed unsupported causal embellishment. This improves traceability but can make posts less original or less engaging. An editor should review both factual scope and style before use.
- The offline KB stores attributed source snapshots and URLs. Runtime does not fetch live pages or verify current web availability. The SWC Registry states that its content has not been actively maintained since 2020; refresh older entries against maintained security guidance before production use. OWASP snapshots carry CC BY-SA 4.0 attribution and ShareAlike obligations documented in `source_snapshots/`.
- Topic matching is lexical. Unsupported or ambiguous focuses fail their slot; a future version could add a verified retrieval index with human review of matches.
- Visual output is a written specification, not an image. A scheduler expecting media needs a separate conversion step.
- Only X-specific character and thread rules are implemented. Additional platforms need their own deterministic validator and output contract.
- Token counts depend on Ollama metadata. Local hardware and electricity costs are not estimated.

See [scientific residual risks](audit/semantic/07_LIMITATIONS_AND_RESIDUAL_RISKS.md) and [prompt limitations](audit/prompt_architecture/07_REMAINING_LIMITATIONS.md).

