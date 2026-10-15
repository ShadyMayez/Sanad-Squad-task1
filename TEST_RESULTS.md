# Verification results

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

Earlier diagnostic runs exposed model mistakes: an unchecked-call post confused a failed subcall with a failed whole transaction, and a failed-call post contradicted its evidence about blocked progress. Source wording, writer instructions, and reviewer guidance were corrected. The final sample no longer contains those statements. This history is why human review remains necessary even when a local reviewer approves a draft.

## Limits of the evidence

Mocked tests establish control-flow behavior and failure handling, not prose quality. The final real run establishes that this installed model completed all six slots on this host. LLM output can vary on future runs. Citation IDs and verbatim quote checks do not mathematically prove that every paraphrase is correct; semantic support still requires review.
