# Changeset and review commands

Base commit: `3735fb2373880a6df3b7d92e80d1628cb2095e25` on `main`. Implementation branch: `codex/semantic-grounding`. The branch's final commit contains the complete source, editable prompts, pinned snapshots, tests, real outputs, reports, and visualizations. The handoff ZIP also includes a Git bundle so the exact commit history and diff can be inspected after extraction.

- `content_pipeline/provenance.py`, `text_spans.py`, `claim_extraction.py`, and `semantic_verification.py`: selected-source integrity, exact span/offset parsing, atomic public-claim coverage, and two-pass local-model entailment judgments.
- `content_pipeline/agents.py`, `graph.py`, `export.py`, and `validation.py`: trusted instruction separation, source-bound writing, rubric consistency, one revision, failure isolation, grounded visual specs, and a repeated acceptance gate at export.
- `kb.json` and `source_snapshots/`: 17 pinned evidence records over 16 vulnerability entries, with official source attribution and retained diagnostic history.
- `instructions/`, `tests/`, `audit/semantic/`, and `audit/prompt_architecture/`: editable prompts, deterministic and live evaluations, failure evidence, real release output, and limitations.

After cloning the bundle or opening this repository, inspect the exact patch with `git diff 3735fb2373880a6df3b7d92e80d1628cb2095e25..codex/semantic-grounding`. The final acceptance evidence is `output/semantic-release-week/`, `FINAL_CONTENT_INSPECTION.md`, and `../../ACCEPTANCE_MATRIX.md`.
