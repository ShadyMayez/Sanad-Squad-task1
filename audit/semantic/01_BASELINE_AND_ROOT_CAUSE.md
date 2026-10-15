# Baseline and root cause (recorded before implementation)

Baseline commit: `3735fb2373880a6df3b7d92e80d1628cb2095e25`. Baseline command `.venv/bin/python -m pytest -q tests audit/tests` yielded **45 passed**.

## Traced path

`kb.json` source URL and locally written `excerpt` → `EvidenceLookup.select` → Writer prompt → Writer's sentence-level `Draft.claims` → Python ID/term checks → Reviewer prompt → Reviewer-produced `claim_support` → graph decision → accepted CSV.

Claims are represented, but one sentence may hold several propositions. Coverage checks rely on Writer metadata and sentence presence. Existing excerpts are locally authored summaries; they are **not exact extracts of retained source snapshots**. There is no snapshot hash or offset. The reviewer sees the excerpt and can mark a quote supported. Python checks only ID membership, limited technical terms, and quote substring. It cannot tell whether the quote entails the full claim or whether a quantifier, cause, scope, or negation was changed. Source outage is not checked during offline generation. The earlier audit proved a controlled approving reviewer could ship fabricated company numbers and mismatched technical claims, and found five unsupported or overbroad sentences in the genuine sample. Direct real Reviewer probes rejected four isolated adversarial prompts, which is encouraging but narrower than the observed failure.

The root cause is a **trust-boundary collapse**: Writer-authored claim coverage and Reviewer-authored quote selection are treated as sufficient factual grounding even though neither is independent evidence-integrity or meaning verification. A valid ID and substring are necessary checks, not entailment. This closure adds snapshot integrity, independent claim extraction, an explicit semantic verdict for each atomic claim, and a non-overridable acceptance gate.

Baseline sources inspected: `content_pipeline/skills.py`, `agents.py`, `validation.py`, `schemas.py`, `graph.py`, `kb.json`, writer/reviewer instructions, `tests/`, `audit/tests/`, original `output/sample-week/`, and `audit/04_SCIENTIFIC_AND_GROUNDING_AUDIT.md`.
