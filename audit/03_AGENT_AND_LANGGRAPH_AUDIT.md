# 03 — LangGraph, agent, and Ollama audit

## Orchestration and state

`content_pipeline/graph.py` constructs two real LangGraph `StateGraph` objects. `Send` creates an outer worker branch for every plan slot, and `operator.add` is the declared reducer for returned results (`graph.py:30-32,136-150`). The inner graph has six nodes: `research`, `write`, `evaluate`, `visual`, `drop`, and `fail`. Its conditional edges are explicit (`graph.py:119-129`). A controlled two-slot barrier showed both workers entered writing before either completed; a delayed first worker still exported before the faster second worker because the exporter sorts by plan order. Distinct `PieceState` inputs contain each slot and index. No shared draft or review list is mutated across branches. The shared `EvidenceLookup.calls` list only records call labels and is not used to make content decisions.

The graph sets `recursion_limit=14` and can write at most twice. A first rejected review routes to `write` with the review's corrections and reasons; the audit test captured that feedback in the second prompt. A second rejection routes to `drop`. Research, writer, and reviewer errors route to `fail`; an unexpected exception from the inner graph is caught in the outer worker. Controlled tests showed one unsupported topic or writer timeout did not abort a healthy slot. Multiple simultaneous reviewer failures yielded separate failed results. This establishes failure isolation for the injected cases, not a proof against every possible library-level cancellation or process crash.

| Invariant | Source and adversarial observation | Verdict |
|---|---|
| Every successfully written draft enters Python validation and reviewer | `graph.py:69-81`; test of invalid hashtag and approving reviewer | Verified for normal/evaluable drafts. A reviewer service failure leaves a draft without a completed review and marks the slot failed. |
| Only approved, hard-valid drafts reach Visual | `graph.py:83-86`; rejected fixture has no visual | Verified through normal graph. |
| One content revision maximum | `attempt` increments at `graph.py:64`; second rejection drops | Verified by two-draft fixture and bounded conditional edge. |
| Transport retry is separate | `llm.py:25-31` retries within one `structured` call; graph attempt increments only on returned draft | Verified by source and existing retry test. |
| Rejected pieces cannot reach CSV | `export.py:31-48` filters `status` | Verified for graph-generated rejected results. Exporter trusts a forged accepted status. |
| Result order deterministic | `export.py:19-20` sorts to plan IDs | Verified with delayed-slot test. |
| No cross-slot draft contamination | Each `Send` passes a fresh state dict | Verified in controlled distinct-topic run; no content-bearing shared mutable state was found. |

## Agent boundaries

Research performs only KB selection (`agents.py:16-21`, `skills.py`). The writer takes a selected vulnerability and external instruction file and calls the model for a `Draft` (`agents.py:24-34`). The reviewer separately reads the rubric and calls the model for a scored `Review`, then code enforces minimum scores and quote existence (`agents.py:37-64`). The Visual Agent deterministically creates a written specification only after successful routing (`agents.py:67-70`). Orchestration itself does not write posts or score them. The generic writer class is reused for both technical and marketing formats; independent instruction files and registry rules provide specialization, but the PDF's phrase “at least two writer agents” has only a configuration-level realization.

The Research and Reviewer both use the same `EvidenceLookup` instance. The executable skill is `content_pipeline/skills.py`; `skills/evidence-lookup.md` describes it. The independent test observed both call labels. A test registry entry for another post type passes through the unchanged graph. Formats requiring a different `Draft` structure or platform length calculation need more than a config file.

## Reviewer trust boundary

The Reviewer is not a blind pass-through: real model probes rejected a contradicted claim, a fabricated company audit count, an unrelated citation, and a malicious instruction embedded in source text. The code also overrides an `approved=True` response when deterministic errors, low scores, unknown IDs, or a missing quote occur. However, the quote check is substring matching, not semantic entailment. A high-scoring fake reviewer can still approve a false sentence with a valid citation and quote; the graph then reaches Visual and CSV. The real sample includes five sentences classified as unsupported or overbroad in report 04, despite all six reviews being approved. This is an answer-shaping and tool-interpretation weakness in the 12-layer audit lens, not a hidden second model pass.

## Local Ollama reliability

`LocalModel` builds one `ChatOllama` instance with the configured model and URL, structured JSON-schema output, `reasoning=False`, a 180-second default `asyncio.wait_for` timeout, and one default retry for timeout/transport errors. Invalid parsed output raises `ValueError` and fails that slot. `asyncio.CancelledError` is not caught by the retry clause, so cancellation propagates. The real host reported Ollama server 0.40.3 and model ID `c46e961bbacc` for `qwen3.5:4b`; fresh CLI runs used that model without a cloud API.

A mocked two-request test measured peak active calls of one for one `LocalModel` with limit one, and two with limit two. A separate test created **two** `LocalModel` instances each configured for one and measured two simultaneous requests. Thus the limiter is per instance, not process-global. The real one-week summary reports peak one, consistent with its single model instance, but no per-request start/end events or raw Ollama responses are persisted. It is impossible to independently reconstruct the peak or count transport retries from the saved run alone. If a client-side timeout leaves server-side generation active, a retry could briefly overlap at the Ollama server; that server behavior was not instrumented and is **NOT VERIFIED**.

## Failure modes not covered by the ordinary happy path

- `evaluate` calls `validate_draft` before its `try` block. An unexpected validator exception is caught only by the outer worker, producing a failed result that omits the partial topic, draft, and token trail (`graph.py:69-81,139-145`). The same loss occurs for an unexpected Visual exception.
- `export_run` writes files non-atomically. A disk or serialization failure after directory creation can leave a partial run folder. The existing artifact parser detects corruption, but the CLI does not roll back or mark the directory incomplete.
- The exporter accepts `SlotResult(status="accepted", reviews=[], visual_spec=None)` and writes a CSV row plus an empty `.md` spec. Normal graph routing prevents this today; the exporter itself does not enforce approval or spec integrity (`export.py:31-48`).
- `TypedDict(total=False)` states are type hints, not runtime checks. A wrong node return shape can reach the outer exception path and lose partial context.
