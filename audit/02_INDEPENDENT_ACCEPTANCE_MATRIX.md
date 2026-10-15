# 02 — Independent PDF acceptance matrix

Source of requirements: both pages of the supplied SanadSquad PDF, read directly with `pdftotext`. Existing `ACCEPTANCE_MATRIX.md` was treated as an assertion, not proof. “Optional web search” is not required because the PDF permits local KB research **or** web search. Image specifications are permitted instead of rendered images. A process-wide model limiter and a separate audit ZIP are user-directed audit concerns, not PDF requirements.

| PDF requirement | Source path | Independent test / runtime evidence | Verdict | Reason |
|---|---|---|---|---|
| Brand voice includes tone, banned terms/punctuation, approved stats, allowed links | `brand-voice.md`, `config.py:44-51`, `validation.py:33-44` | Audit test edits a banned term; sample has no prohibited phrase | VERIFIED PASS | Enforceable JSON block exists; statistics list is empty. |
| KB has at least 15 entries and required fields | `kb.json`, `schemas.py:13-31` | Pydantic loads 16 entries; malformed-entry test; 17 URLs returned HTTP 200 | VERIFIED PASS | Structural requirement met. URL reachability does not prove current correctness. |
| Weekly plan has six slots, 3 threads and 3 posts, optional focus | `plan.json`, `config.py:32-41` | Original and fresh resolved plans; invalid plan test | VERIFIED PASS | Exact 3+3 plan accepted; invalid count/type rejected. |
| Empty focus picks a topic and records source | `skills.py:14-17`, `export.py:22-24` | Three empty-focus slots resolved in both real runs | VERIFIED PASS | Topic and source IDs/URLs persisted. |
| Explicit focus and override applied before research | `cli.py:40-59` | Existing real override run, CLI tests | VERIFIED PASS | `thread_2` override resolves to oracle manipulation. |
| Orchestrator starts independent work in parallel and collects results | `graph.py:132-151`, `export.py:19-20` | Audit concurrency and slow-slot tests | VERIFIED PASS | Genuine `Send` fan-out; sorted final output. |
| One slot failure does not interrupt others | `graph.py:49-53,62-81,139-145` | Audit unsupported topic and writer-timeout tests | VERIFIED PASS | Healthy slot accepted despite another slot failure. |
| Research uses KB or web and source of every topic is recorded | `agents.py:16-21`, `skills.py`, `research_log.json` | Original/fresh six-slot inspections | VERIFIED PASS | Offline KB route satisfies the PDF's alternative. |
| Source failure marks slot failed | `skills.py:20-28`, `graph.py:49-53` | Unsupported focus fails; dead external URLs are not fetched | PARTIAL | Missing KB match fails; URL outage is invisible at runtime. |
| At least two specialized writer agents with independent instructions | `agents.py:24-34`, two instruction files, registry | Real 3+3 output; file edit test | PARTIAL | Two configured writer roles, one generic Python `WriterAgent` class. |
| Technical writer produces 5–10 tweets | `content-types.json`, `validation.py:10-11` | Original/fresh counts 7, 6, 6 | VERIFIED PASS | Graph would drop a thread outside range. |
| Reviewer scores each candidate using written rubric, explains rejection | `agents.py:43-64`, rubric file | Real reports; injected rejection/low score tests | VERIFIED PASS | Six criteria, reasons and correction fields persisted. Semantic quality is assessed separately. |
| One content revision then permanent drop | `graph.py:59-65,83-86,110-117` | Audit second-rejection test | VERIFIED PASS | Two drafts maximum; no forced approval. |
| Images/specifications only after acceptance | `graph.py:83-108` | Audit rejection and fresh run inspections | VERIFIED PASS | Normal graph never routes rejection to Visual. Exporter trust gap is listed separately. |
| At least one skill shared by two agents | `skills.py:7-34`, `graph.py:44-47` | Audit shared-call observation | VERIFIED PASS | Research and Reviewer call the same `EvidenceLookup` instance. |
| Every claim has a source; no invented facts | `Draft.claims`, `validation.py:17-26`, `agents.py:49-57` | 22 claims in each real run; adversarial false-claim tests | PARTIAL | IDs and quotes are traceable, but code can approve a false/fabricated claim if model review errs; fresh sample contains overbroad claims. |
| Hard rules in code; judgment in model | `validation.py`, `agents.py:58-61` | Existing hard-rule tests plus audit brand edit | VERIFIED PASS | Hashtags, characters, links, lengths and some technical terms are deterministic. |
| File-based brand, rubric and writer instructions | `brand-voice.md`, `instructions/`, `agents.py:11-13` | Audit instruction-file test | VERIFIED PASS | Runtime reads editable files. |
| Another post type by adding files/config, no orchestrator rewrite | `content-types.json`, `graph.py:57-58` | Existing registry test | VERIFIED PASS | Works for another type sharing the current Draft contract. |
| Three example CLI commands | `run_week.py`, `run_piece.py`, `cli.py` | Prior three real runs, fresh week and piece, invalid-type smoke | VERIFIED PASS | Exit codes and outputs observed. |
| Accepted-only CSV, `Post Text,Image` | `export.py:40-48` | Original/fresh CSV parse; rejected fixture excluded; multiline/quote audit test | VERIFIED PASS | Exact two-column header and one row per accepted piece. |
| Per-run trail with defined JSON schemas | `export.py:21-39`, `schemas/*.schema.json` | Independent read-only parser on original and fresh run | VERIFIED PASS | Required files exist and parse; stage timestamps and raw model responses are absent. |
| Summary of shipped/dropped reasons, tokens and cost | `export.py:49-68` | Original/fresh arithmetic, CLI stdout and summary | PARTIAL | Counts and totals reconcile; raw provider metadata and per-call usage are not persisted, so reported measurements cannot be independently replayed. |
| Runnable Git repository with sample output and docs | Root Git tree, `README.md`, `ARCHITECTURE.md`, `LIMITATIONS.md`, `output/sample-week/` | Clean baseline commit, 22 existing tests, fresh real run | VERIFIED PASS | Upstream snapshot and MIT license present. |
| Architecture explains agent flow, code/model split, 15 slots and second platform | `ARCHITECTURE.md` | Document inspection against PDF | VERIFIED PASS | Required topics and diagram are present. |
| Output quality suitable to post as written | `output/sample-week/accepted_content.json` | Claim-by-claim audit in report 04; fresh output byte-identical | FAIL | Several accepted technical sentences overstate or misattribute evidence. |

**Overall PDF verdict:** **REQUIRES REMEDIATION**. The workflow, file contracts, command paths, and rejection routing largely work. Grounding reliability and publishable technical accuracy remain material weaknesses. See reports 04 and 07 for reproducible claim-level findings and minimal corrections.
