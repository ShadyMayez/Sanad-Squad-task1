# Agent role and responsibility matrix

| Component | Input / authority | Output | Cannot do |
|---|---|---|---|
| Research + shared EvidenceLookup | Validated plan and pinned KB labels; deterministic Python | Selected topic and source records | Invent evidence, follow source text as commands, approve content |
| Technical Writer | System instruction file; task JSON with topic, brand, pinned evidence, feedback | 5–10 tweet `Draft` with sentence mappings | Claim to audit a client, add sources, self-approve, produce visual |
| Marketing Writer | Separate system instruction; task JSON with one topic | One-sentence/one-claim `Draft` | Invent company authority, mix mechanisms, decide publication |
| Atomic extractor | Public draft text and candidate IDs | Exact-span atomic propositions + coverage errors | Accept Writer mapping as proof of completeness |
| Provenance validator | Pinned snapshot bytes and metadata | Integrity errors or pass | Infer truth from URL/hash alone |
| Semantic Verifier | Dedicated system instruction; atomic claims and untrusted quotation task JSON | Five-category structured support judgments | Write copy, choose publication, fabricate missing quotations |
| Skeptical support audit | Separate system instruction; only a tentative claim and its selected exact spans | Independent support veto or confirmation | Add new sources, treat the first model reason as evidence, approve publication |
| Deterministic Validator | Draft, brand rules, evidence | Hard-rule errors | Judge prose quality or semantic entailment |
| Reviewer | Independent rubric system instruction; task JSON with Draft, evidence, hard errors, semantic report | Six scores, claim support, approval/rejection reasons and corrections | Override hard/semantic failures, rewrite draft |
| Visual Agent | Accepted final text, supported atomic claims, topic and evidence | Content-aware written image specification | Process rejected content, invent incident or rendered media |
| Orchestrator/exporter | Typed LangGraph state and slot results | Ordered artifacts, accepted-only CSV | Research, write, score content, bypass final gate |

Research and Visual remain deterministic by design; adding model calls to them would increase local latency without improving their current bounded tasks. Every LLM-powered role uses a separate system instruction file. Runtime source quotations and prompts from lower-trust data are carried in JSON `HumanMessage` content, never system instruction text.
