# Known limitations and next steps

- Claim-to-evidence IDs are checked in Python, but semantic support is judged by a local LLM reviewer. This is an audit aid, not formal proof. A human should review exported copy before publication.
- The offline KB stores curated excerpts and URLs. Runtime does not fetch live pages or verify current web availability. The SWC Registry states that its content has not been actively maintained since 2020; refresh older entries against maintained security guidance before production use.
- Topic matching is lexical. Unsupported or ambiguous focuses fail their slot; a future version could add a verified retrieval index with human review of matches.
- Visual output is a written specification, not an image. A scheduler expecting media needs a separate conversion step.
- Only X-specific character and thread rules are implemented. Additional platforms need their own deterministic validator and output contract.
- Token counts depend on Ollama metadata. Local hardware and electricity costs are not estimated.

