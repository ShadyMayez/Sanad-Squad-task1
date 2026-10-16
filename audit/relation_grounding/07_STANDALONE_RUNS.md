# Real standalone workflow outcomes

Both commands invoked the actual LangGraph application and `qwen3.5:4b`; neither substituted a mock or cloud model. Both saved full artifact folders, and `inspect_runs.py` validated their JSON contracts and accepted-only CSV behavior.

| Run | CLI exit | Shipped / dropped / failed | Elapsed | Prompt / completion tokens |
|---|---:|---:|---:|---:|
| `run_piece.py --type tech-thread --topic reentrancy --output output/relation-grounding-tech` | 1 | 0 / 1 / 0 | 342.793 s | 50,345 / 6,135 |
| `run_piece.py --type marketing-post --topic 'access control' --output output/relation-grounding-marketing` | 1 | 0 / 1 / 0 | 77.591 s | 9,834 / 1,284 |

The technical piece produced a six-tweet first draft and a five-tweet revision, then dropped. The revision still asserted that a reentrancy lock “prevent[s] recursive entry within the calling contract”, a mechanism not stated by its selected SWC-107 recommendation span. Another claim said the practices “help avoid the major dangers of control flow takeover” without direct evidence for that effectiveness relationship. The Reviewer also rejected it. No visual or CSV row was created.

The marketing piece produced two drafts. The first offered a review action but combined access-control and initialization facts into an unverified causal chain. The revision asserted that an attacker could withdraw Ether **by** re-initialization, a link the selected evidence and verifier did not establish to the required standard, and it omitted a practical security action. The deterministic marketing rule and Reviewer rejected it. No visual or CSV row was created.

Both drops respected the single-revision bound. Measured usage was complete, peak active Ollama calls was one, and external model API charge was USD 0 for each. Hardware and electricity cost was not measured. These outcomes show safe exclusion, but they also show that the current local model and Writer instructions do not reliably generate acceptable educational content under the strict relation gate.
