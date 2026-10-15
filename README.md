# SanadSquad local content pipeline

Generates a six-slot week of grounded X content for a smart contract security auditing firm. Uses the local `qwen3.5:4b` Ollama model, LangChain's `ChatOllama`, and LangGraph. Nothing is published or scheduled.

## Setup

```bash
python3.12 -m venv .venv
.venv/bin/python -m pip install -r requirements.txt
ollama list  # must include qwen3.5:4b
cp .env.example .env  # optional: defaults already work
```

The host used for the sample run had Ollama server 0.40.3. No cloud API key is needed. Environment settings: `OLLAMA_MODEL`, `OLLAMA_BASE_URL`, `OLLAMA_MAX_CONCURRENCY` (default 1), `OLLAMA_TIMEOUT_SECONDS` (default 180), `OLLAMA_TRANSPORT_RETRIES` (default 1), and `OUTPUT_BASE` (default `output`). The installed model must match `OLLAMA_MODEL`; no alternative is selected automatically.

## Commands

```bash
.venv/bin/python run_week.py --plan plan.json --output output/week-42
.venv/bin/python run_week.py --plan plan.json --set thread_2="oracle manipulation"
.venv/bin/python run_piece.py --type tech-thread --topic "reentrancy"
.venv/bin/python -m pytest -q
```

The two Python scripts also work with the environment's `python` after activating `.venv`. `--set` overrides a slot focus. `--output` must name a new directory. Exit 0 means at least one piece shipped and no slot failed; exit 1 means the run finished with failed slots or no shipped piece; exit 2 means invalid input or an output path error. Dropped pieces are expected quality-gate outcomes and are listed in the summary.

## Inputs and output

Edit `brand-voice.md` (the JSON block holds enforceable rules), `kb.json`, `plan.json`, `instructions/*.md`, and `content-types.json` without changing the graph. A new content type needs a registry entry and a writer instruction file. Its writer uses the shared structured draft contract and the same gates. For a format requiring a different data contract, implement a writer adapter and register it at the agent boundary.

Every run writes `resolved_plan.json`, `research_log.json`, drafts, `validation_report.json`, `review_report.json`, `accepted_content.json`, `failures.json`, `visual_specs/`, `posts.csv`, and `summary.json`. See [artifact schemas](docs/SCHEMAS.md). Only accepted pieces enter `posts.csv`. Its columns are exactly `Post Text,Image`. Each technical thread is one CSV record; numbered tweets are separated by blank lines within the quoted Post Text field. `Image` values such as `spec:visual_specs/thread_1.md` point to written specifications, not image media. Convert them to actual images before importing into a scheduler that expects media files.

Source IDs and claim-to-evidence mappings stay in the draft and accepted JSON, not in public post text. The local KB contains evidence excerpts and source URLs so a run works offline once dependencies and Ollama are installed. Optional live web research is not implemented in this version.

## Provenance

The `reference-autopost-ai/` directory is an unchanged source snapshot at commit `5fa0ba548dee97051f37688348ba08e99f69c184`, with its MIT license. See `REFERENCE_AUDIT.md` for the adaptation decisions. The SWC Registry itself warns that its content has not been actively maintained since 2020; see `LIMITATIONS.md`.

