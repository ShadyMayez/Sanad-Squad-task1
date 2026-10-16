# SanadSquad local content pipeline

Generates a six-slot week of X content for a smart contract security auditing firm. Uses the local `qwen3.5:4b` Ollama model, LangChain's `ChatOllama`, and LangGraph. A claim-level evidence gate checks generated text before export. Nothing is published or scheduled.

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

Source IDs and claim-to-evidence mappings stay in the draft and accepted JSON, not in public post text. The local KB contains pinned source snapshots, SHA-256 digests, exact quotations and offsets, source scope, and URLs. After installation, the content run can work without web access. `claims.json`, `evidence_provenance.json`, `semantic_verification.json`, and `grounding_summary.json` record atomic claims, exact supporting spans, bounded source-context windows, both semantic passes, and final verdicts. A `SUPPORTED` decision is a fallible local-model judgment, not a mathematical proof; review the saved quotations before publishing. Optional live web research is not implemented.

The production Writer, Reviewer, and Semantic Verifier load separate editable instructions as LangChain `SystemMessage` objects. Dynamic assignments and source material enter JSON `HumanMessage` objects. The Research Agent and Visual Agent are deterministic. The default one-call Ollama limit is shared across local CLI processes with a file lock. Other configured limits apply within the process; see [architecture](ARCHITECTURE.md).

Writers may paraphrase pinned evidence while preserving technical meaning, conditions, and certainty. The verifier records exact selected spans and bounded source-context windows, then asks an independent skeptical pass to check the full claim. The Reviewer scores usefulness separately from factual support. See the [context and quality design](audit/context_quality/02_CONTEXT_AWARE_VERIFICATION_DESIGN.md) and the saved JSON schema files in `schemas/`.

Agent instructions: [Technical Writer](instructions/tech-thread.md), [Marketing Writer](instructions/marketing-post.md), [Reviewer rubric](instructions/reviewer-rubric.md), [Semantic Verifier](instructions/semantic-verifier.md), [Skeptical support audit](instructions/semantic-skeptic.md), and [Visual Agent](instructions/visual-agent.md).

The final context-quality run is [output/semantic-context-quality-final-week](output/semantic-context-quality-final-week/): **2 shipped, 4 dropped, 0 failed**. The previous release and first diagnostic runs remain at `output/semantic-release-week/` and `output/semantic-context-quality-week/`. See the [per-slot inspection](audit/context_quality/07_REAL_OLLAMA_CONTENT_INSPECTION.md) and [acceptance matrix](ACCEPTANCE_MATRIX.md). The final structural audit passed, but a human reviewer found a possible unsupported causal framing in accepted `thread_1` tweet 3. Treat the accepted thread as **not publication-cleared** until that wording receives direct support or correction. Dropped slots never enter the CSV.

Historical `output/sample-week/` predates the semantic closure and remains unchanged. New runs have their own directories. Evaluation reports are under `audit/semantic/` and `audit/prompt_architecture/`.

## Provenance

The `reference-autopost-ai/` directory is an unchanged source snapshot at commit `5fa0ba548dee97051f37688348ba08e99f69c184`, with its MIT license. See `REFERENCE_AUDIT.md` for the adaptation decisions. The SWC Registry itself warns that its content has not been actively maintained since 2020; see `LIMITATIONS.md`.

Pinned source-page adaptations under `source_snapshots/` have their own attribution and licenses: SWC Registry MIT and OWASP Smart Contract Security CC BY-SA 4.0. See [snapshot attribution](source_snapshots/README.md) before redistributing those files.

