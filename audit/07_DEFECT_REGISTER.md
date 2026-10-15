# 07 — Prioritized defect register

Severity follows the audit directive. “Mandatory” means the finding impairs a PDF requirement; “hardening” means it is a user-directed engineering improvement or defense in depth beyond a demonstrated normal-graph violation. Reproduce from the workspace root. No application source was changed during this audit.

## A-01 — CRITICAL — Incorrect technical claims approved and exported (mandatory)

- **Requirement:** No invented facts; every claim actually supported; reviewer catches weak pieces; publishable output.
- **Location/root cause:** `content_pipeline/agents.py:49-61` checks whether a reviewer quote is an excerpt substring but does not establish semantic entailment. `content_pipeline/validation.py:17-26` checks IDs and selected terms, not meaning. The model reviewer can confuse a valid quote with support for the entire sentence.
- **Reproduce:** `.venv/bin/python -m pytest -q audit/tests/test_independent_audit.py -k semantically_false_or_fabricated_claim_can_ship_when_reviewer_approves`; inspect `output/sample-week/accepted_content.json` and `audit/04_SCIENTIFIC_AND_GROUNDING_AUDIT.md`.
- **Expected vs actual:** False or overbroad claims should be rejected. A controlled high-scoring reviewer makes three false/fabricated fixtures ship; the real reviewer approved five unsupported or overbroad sentences in both the original and fresh six-slot runs.
- **Consequence:** A user can export technically misleading smart-contract guidance while every source ID and quote appears valid. The previous matrix's broad PASS for “no invented facts” is not justified.
- **Minimal correction:** Do not auto-label accepted cyber-security copy publish-ready. Add an explicit human claim check before final CSV export, or constrain generation to independently vetted atomic facts and require a verifier to assess each complete sentence against its source. Add regression fixtures for overbroad CEI guarantees, fabricated company counts, unrelated citations, incorrect transaction scope, and conflated oracle mitigations. Keep quote-substring checking as a secondary check only.

## A-02 — MEDIUM — Legacy source applicability is not fully encoded (mandatory grounding risk)

- **Requirement:** Accurate, source-grounded technical content for auto-selected KB topics.
- **Location/root cause:** `kb.json:6,13-16`; 15 of 16 topics use an SWC registry that says it has not been thoroughly updated since 2020. SWC-106's old `selfdestruct` guidance predates Cancun behavior. SWC-101 and SWC-100 contain broad older-version qualifiers but no precise version applicability. Research has no applicability filter (`skills.py:14-29`).
- **Reproduce:** Compare `kb.json` to [SWC notice](https://swcregistry.io/docs/SWC-106/), [current Solidity selfdestruct behavior](https://docs.soliditylang.org/en/latest/introduction-to-smart-contracts.html), [0.8 arithmetic](https://docs.soliditylang.org/en/latest/080-breaking-changes.html), and [0.5 visibility](https://docs.soliditylang.org/en/v0.5.9/050-breaking-changes.html). `audit/tests/test_independent_audit.py::test_misleading_kb_description_can_drive_topic_selection` proves schema-valid misleading descriptions can guide retrieval.
- **Expected vs actual:** Version-sensitive material should state its compiler/EVM conditions. Some entries provide only broad qualifiers or none; future auto-selected posts could omit required context. No such post was observed in the six-slot sample.
- **Consequence:** Potentially obsolete claims for future topics; this is a risk, not a proven false statement in the current sample.
- **Minimal correction:** Add explicit applicability metadata and maintained-source cross-checks for legacy entries, starting with SWC-106, SWC-101, SWC-109, and SWC-100. Exclude a topic from automatic selection until its version conditions are reviewed. Add tests that version-sensitive posts include the relevant condition.

## A-03 — MEDIUM — Exporter trusts an accepted status without approval or a nonempty spec (hardening)

- **Requirement:** Only approved pieces ship; visual specification for each accepted piece.
- **Location/root cause:** `content_pipeline/export.py:31-48` filters only on `status` and writes `r.visual_spec or ""`.
- **Reproduce:** `.venv/bin/python -m pytest -q audit/tests/test_independent_audit.py -k export_accepts_missing_visual_spec_and_unreviewed_accepted_result`.
- **Expected vs actual:** A forged or corrupted accepted result should fail export. The exporter writes a CSV row with no review and an empty spec. The normal graph currently prevents this input.
- **Consequence:** Internal API misuse or state corruption can bypass the final quality gate.
- **Minimal correction:** At export, require a final approved review, zero final hard errors, a final draft, and nonblank visual spec; fail atomically if any accepted result violates them. Add a regression test that forged acceptance raises without creating a CSV.

## A-04 — MEDIUM — “Global” Ollama limiter is only per model instance (user-directed reliability)

- **Requirement:** Shared inference limit of one default across concurrent slot work.
- **Location/root cause:** `content_pipeline/llm.py:14-22` constructs a new `asyncio.Semaphore` for each `LocalModel`.
- **Reproduce:** `.venv/bin/python -m pytest -q audit/tests/test_independent_audit.py -k two_local_model_instances_do_not_share_global_semaphore`.
- **Expected vs actual:** Two simultaneous runs each configured for one should still respect a global one-call cap. The audit mock observed two active calls. A single six-slot run observed a saved peak of one.
- **Consequence:** Multiple runs can overload a resource-constrained Ollama server.
- **Minimal correction:** Use an application-process shared limiter keyed by endpoint/model, or a cross-process queue/file lock if the promise extends across CLI processes. Test concurrent `execute` calls and document the scope precisely.

## A-05 — MEDIUM — Persisted run lacks independently replayable timing and raw usage evidence (mandatory observability is partial)

- **Requirement:** Explain what shipped/dropped, token use, cost, and an easy-to-read run trail.
- **Location/root cause:** `content_pipeline/graph.py:35-41` accumulates token counts; `content_pipeline/export.py:49-68` saves totals, but not raw `usage_metadata`, per-call start/end times, retry events, or per-slot durations.
- **Reproduce:** `.venv/bin/python audit/scripts/inspect_run.py output/sample-week`; inspect all artifacts. The totals reconcile with slot fields, but raw Ollama responses are absent.
- **Expected vs actual:** An independent auditor should be able to distinguish measured calls, retries, and duration per slot. Only aggregate counters and run elapsed time survive.
- **Consequence:** The audit can verify arithmetic, not independently replay the claimed peak, call count, or token extraction. Visual trace must mark slot duration unavailable.
- **Minimal correction:** Persist a bounded per-call event ledger with slot ID, agent, attempt, start/end timestamps, retry index, model ID, and raw usage fields. Avoid storing prompt secrets. Test sum and timing consistency.

## A-06 — MEDIUM — Partial export and unexpected error paths lose audit context (hardening)

- **Requirement:** Per-run trail and isolated failures.
- **Location/root cause:** `content_pipeline/export.py:16-48` creates and writes the destination incrementally without a temporary directory/commit marker. `graph.py:69-81,139-145` catches unexpected validator/visual exceptions only in the outer worker, dropping partial topic/draft context.
- **Reproduce:** The audit corruption fixture demonstrates a partial JSON artifact is detectable but not repaired; source path shows the non-atomic write sequence. Normal injected reviewer failures retain drafts; unexpected outer exceptions can lose them.
- **Expected vs actual:** A failed run should be clearly incomplete, and slot failure records should retain known progress. Current partial folders can look like complete runs until parsed.
- **Consequence:** Ambiguous forensic trail after disk, serialization, or unexpected node failures.
- **Minimal correction:** Write into a temporary run directory, validate artifacts, then rename atomically and add a completion marker. Wrap validator/visual node errors locally and preserve partial state. Add disk-failure and node-exception regression tests.

## A-07 — LOW — Writer role distinction is configuration-level only (PDF interpretation)

- **Requirement:** At least two specialized writer agents, each with independent instructions.
- **Location/root cause:** `content_pipeline/agents.py:24-34` has one generic `WriterAgent`; `content-types.json` and two instruction files specialize it.
- **Reproduce:** Read class definitions and observe different instruction files in prompts.
- **Expected vs actual:** The functional two-role behavior exists; separate Python agent classes do not.
- **Consequence:** Minor ambiguity when claiming two agents; no demonstrated wrong output from this design alone.
- **Minimal correction:** Either document the two configured writer instances precisely or register dedicated writer adapters if the evaluator requires distinct implementations. Keep central graph unchanged.
