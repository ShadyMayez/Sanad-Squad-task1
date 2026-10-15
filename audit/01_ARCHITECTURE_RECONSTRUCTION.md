# 01 — Architecture reconstructed from executable paths

## Scope and provenance

This audit inspected commit `20e028a8906a1082f384aa8388b5b2a7d0181cb9` without changing application files. The local upstream snapshot exactly matches AutoPost AI commit `5fa0ba548dee97051f37688348ba08e99f69c184`: an isolated upstream Git directory reported no differences against `reference-autopost-ai/`. Its MIT notice is present. The upstream `main.py` is a sequential LangGraph pipeline for trend research, planning, writing, image sourcing, scheduling, persistence, reporting, and email. SanadSquad copies no upstream Python module verbatim. It adapts the `StateGraph` and Pydantic handoff patterns; all agents and export logic are new or replaced. Source: `REFERENCE_AUDIT.md`, `reference-autopost-ai/main.py`, `reference-autopost-ai/models/schemas.py`.

## Entry and state path

`run_week.py` calls `week_main`; `run_piece.py` calls `piece_main`. `week_main` validates the six-slot plan and registry, applies `--set` before any research, then calls `execute`. `piece_main` creates a one-slot `Plan` and uses the same `execute` function. `execute` loads brand rules, KB, registry, creates one `LocalModel`, builds the graph, invokes it, and exports the result (`content_pipeline/cli.py:21-81`).

The outer LangGraph state is `WeekState(plan, results)`. `START` emits one `Send("worker", {slot, index})` per slot. Six worker invocations run as independent branches. The `results` key uses an `operator.add` reducer, so branches can contribute one `SlotResult` each. `export_run` explicitly sorts them by original plan order before writing artifacts (`content_pipeline/graph.py:30-32,132-151`; `content_pipeline/export.py:19-20`).

Each worker invokes the same compiled inner graph with its own `PieceState`: `research → write → evaluate`. `evaluate` runs Python validation, then the model reviewer. Approval plus zero deterministic errors goes to `visual`. Otherwise, attempt one returns to `write` with `review.corrections + review.reasons`; attempt two goes to `drop`. Research, writer, reviewer, or unexpected worker exceptions produce a failed slot, with unrelated branches continuing (`content_pipeline/graph.py:49-129`). `attempt` increments only after a successful writer response, so a transport retry inside `LocalModel` does not count as a content revision.

The generic `WriterAgent` class is instantiated using a registry entry. Technical and marketing behavior comes from different editable instruction files and count rules. There are two configured writer roles but only one Python writer class (`content_pipeline/agents.py:24-34`, `content-types.json`). The Reviewer is a separate class and reads a rubric file on each call. Research and Reviewer use the same `EvidenceLookup` object; Python validation also calls its ID check. The `skills/evidence-lookup.md` file documents the skill, while `content_pipeline/skills.py` is its executable implementation.

`LocalModel` wraps `ChatOllama.with_structured_output` with a semaphore, `asyncio.wait_for` timeout, one default transport retry, and Pydantic parsing (`content_pipeline/llm.py:9-37`). The semaphore belongs to a `LocalModel` instance, not the entire process or Ollama server. In one `execute` run all six slots share that instance. Two separate runs can each occupy one request at the same time.

The Research Agent selects a local KB entry. Empty focus chooses `kb[index % len(kb)]`; explicit focus uses a lexical 75% word-overlap threshold (`content_pipeline/skills.py:14-29`). It does not fetch the listed URLs at runtime. The Writer sees the entry's description, root cause, and evidence excerpts; its Pydantic `Draft` contains tweets and per-sentence claims. Python validation enforces format, configured banned terms and characters, link policy, source IDs, and a short list of named techniques. The Reviewer receives the same evidence and draft, scores six criteria, and returns claim-support quotes. Code checks that each quote is a substring of its cited local excerpt. No independent semantic entailment check exists (`content_pipeline/validation.py`, `content_pipeline/agents.py:43-64`).

`VisualAgent` is deterministic text construction from an editable guide and topic, reached only after approval in the normal graph. The exporter writes per-run JSON files, one CSV row per accepted piece, and `spec:visual_specs/<id>.md` references. It trusts incoming `SlotResult.status == "accepted"`; it does not recheck review approval or nonempty visual content (`content_pipeline/export.py:30-48`).

## Unexpected behavior and evidence limits

- The previous acceptance matrix says “two writer agents”; the implementation has one generic writer class with two instruction configurations. This is functionally specialized output, with a weaker code-level separation than the wording suggests.
- “Global” inference limiting applies within one model instance. The independent test creates two instances with limit one and observes two simultaneous mocked invocations.
- `ResearchRecord.status` stores the final slot disposition, not a separate timestamped research status. The JSON trail has no per-slot stage duration or raw Ollama response metadata. Only accumulated slot tokens and a run-level peak counter persist.
- `export_run` can write an accepted CSV row and an empty image specification for a forged accepted result with no review. The ordinary graph does not create that result, but the exporter is not a second trust boundary.
- The local KB includes legacy SWC topics whose compiler/EVM applicability is absent or only broadly qualified. This matters for future auto-selected topics even though the six sample topics do not include those entries.
