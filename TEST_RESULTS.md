# Verification results

> Historical baseline (before independent scientific audit and semantic closure). The later independent audit found five unsupported or overbroad sentences in `output/sample-week/` despite this report's original favorable inspection. Do not treat the baseline as publication clearance. Current results are in `audit/semantic/` and `audit/prompt_architecture/`.

## Environment and commands

- Python: 3.12.13 in `.venv`.
- Ollama server: 0.40.3; local client: 0.24.0. `ollama list` reported `qwen3.5:4b` with model ID `c46e961bbacc`.
- Installed core packages: `langchain==1.4.6`, `langgraph==1.2.15`, `langchain-ollama==1.1.0`, `pydantic==2.14.1`, `pytest==9.1.1`.
- Real connectivity and Pydantic structured-output smoke calls to `qwen3.5:4b` succeeded before the pipeline was built. Returned Ollama usage metadata was present.
- `17` KB evidence URLs returned HTTP 200 during source preparation. Runtime uses local curated evidence, so it does not depend on live URL fetches.
- `.venv/bin/python -m pytest -q`: **22 passed in 1.45 seconds** on the final run. The tests use deterministic model doubles for failure injection, graph routing, review gates, shared skills, CLI contracts, concurrency, output, and retry limits. `.venv/bin/python -m compileall -q content_pipeline run_week.py run_piece.py` also passed.

## Actual model runs

| Command | Result | Elapsed | Recorded prompt / completion tokens |
|---|---|---:|---:|
| `.venv/bin/python run_week.py --plan plan.json --output output/sample-week` | 6 shipped, 0 dropped, 0 failed | 162.991 s | 9,156 / 3,802 |
| `.venv/bin/python run_week.py --plan plan.json --set thread_2="oracle manipulation"` | 6 shipped, 0 dropped, 0 failed | 162.686 s | 9,372 / 3,893 |
| `.venv/bin/python run_piece.py --type tech-thread --topic "reentrancy"` | 1 shipped, 0 dropped, 0 failed; six tweets | 39.348 s | 1,676 / 1,019 |

The override run is retained locally in `output/run-20261015-192442-025542/`; its `resolved_plan.json` sets `thread_2` to `oracle manipulation`, and its research log records `SCWE-028` and `OWASP-SC03`. The standalone run is in `output/run-20261015-192738-325916/`. These diagnostic runs are ignored by Git; the committed sample is `output/sample-week/`.

## Sample inspection

The sample contains all required artifact files. Every persisted JSON artifact parsed through its Pydantic contract. Its CSV has exactly `Post Text,Image` as the header and six accepted rows. Each image value points to an existing written specification. The three technical threads contain 7, 6, and 6 tweets. All six accepted drafts passed the current deterministic validator and have claim records with known evidence IDs. All final reviews approved with rubric scores; the recorded peak was one simultaneous Ollama call. The six items were inspected against their cited KB evidence and brand rules. The sample's prompt and completion token totals are actual returned metadata; external model API charges were $0. Local electricity and hardware costs were not measured.

Earlier diagnostic runs exposed model mistakes: an unchecked-call post confused a failed subcall with a failed whole transaction, and a failed-call post contradicted its evidence about blocked progress. Source wording, writer instructions, and reviewer guidance were corrected at the time. The subsequent independent audit still found five other unsupported or overbroad statements in the historical sample. This history is why human review remains necessary even when a local reviewer approves a draft.

## Limits of the evidence

Mocked tests establish control-flow behavior and failure handling, not prose quality. The final real run establishes that this installed model completed all six slots on this host. LLM output can vary on future runs. Citation IDs and verbatim quote checks do not mathematically prove that every paraphrase is correct; semantic support still requires review.

## Semantic and prompt closure (2026-10-16)

The historical sample above predates the atomic semantic gate; the independent audit found five unsupported or overbroad shipped sentences in it. The current implementation ran `.venv/bin/python -m pytest -q` with **68 passed** and `.venv/bin/python -m compileall -q content_pipeline run_week.py run_piece.py audit/semantic audit/prompt_architecture` successfully. The fixed A–T benchmark on `qwen3.5:4b` accepted **2/2** supported examples and **0/15** adverse examples, with **80%** exact five-label accuracy; four adverse labels differed only by rejection category. It recorded **22,440 prompt** and **1,867 completion tokens** with complete usage metadata. The final parser-aligned rerun of six source-text injection probes produced **0/6 false accepts**, with 4,950 prompt and 598 completion tokens.

A real final standalone technical piece at `output/semantic-final-accepted-piece/` shipped **1/1**: five ordered tweets, five pinned supported atomic claims, an approving six-score Review, one written visual specification, and one CSV row. The independent artifact inspector passed. Runtime was **69.305 seconds**, with **12,625 prompt** and **1,330 completion tokens**, complete usage metadata, and peak one active Ollama call. Earlier diagnostic pieces and a six-slot week with all slots dropped remain saved as failure evidence; see `audit/semantic/06_REAL_OLLAMA_EXECUTION.md` for root causes.

The first closure six-slot run at `output/semantic-closure-week/` shipped **2**, dropped **4**, and failed **0** in **644.509 seconds**. It recorded **89,416 prompt** and **10,754 completion tokens** with complete metadata and peak one active call. The independent inspector passed; only the five-tweet reentrancy thread and one unchecked-call marketing post appeared in its CSV, each with pinned supported claims, approving Reviews, and written visual specs. Four second-pass failures were correctly dropped and excluded. The final-code rerun is reported in the semantic audit after completion. External model API charges were USD 0; local electricity and hardware costs were not measured.

The second real six-slot run at `output/semantic-final-verified-week/` shipped **3**, dropped **3**, and failed **0** in **587.657 seconds**. It recorded **83,764 prompt** and **9,875 completion tokens**, complete usage metadata, and peak one Ollama call. The independent inspector passed, and manual inspection found the three accepted texts grounded in SWC-107, SWC-104, and SWC-113. Visual inspection found one unsupported phrase, “success flag,” in a written image specification; the Visual Agent was corrected to say “return value” and to depict the accepted recipient-initiated transaction separation. The original run remains preserved. The final release run using the corrected Visual Agent is reported below and in `audit/semantic/06_REAL_OLLAMA_EXECUTION.md`.

The final release six-slot run at `output/semantic-release-week/` shipped **3**, dropped **3**, and failed **0** in **580.873 seconds**. It recorded **84,640 prompt** and **9,980 completion tokens**, complete usage metadata, peak one active call, and USD 0 external model API charges; local costs remain unmeasured. The independent inspector passed all JSON contracts, exact source/span mappings, CSV and spec paths. Manual inspection found the three accepted texts and visuals grounded in SWC-107, SWC-104, and SWC-113; three invalid or insufficiently supported pieces remained out of the CSV. See `audit/semantic/FINAL_CONTENT_INSPECTION.md` for per-slot findings.
