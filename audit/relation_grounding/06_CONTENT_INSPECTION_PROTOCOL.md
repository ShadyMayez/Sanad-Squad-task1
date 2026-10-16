# Real-run inspection protocol

For each saved standalone piece and each of the six weekly slots:

1. Validate every JSON artifact with the persisted Pydantic contract, then verify exact CSV header and row count against accepted pieces.
2. Check plan-order aggregation, slot status, draft count (one or two), final Reviewer scores and decision, and absence of Visual specifications for dropped or failed slots.
3. For each accepted claim, read the public text alongside every selected exact source span and its scope; verify that the selected passage establishes the claimed actor, relationship, condition, direction, and certainty. A matching citation or relation label alone is insufficient.
4. Recheck brand and platform rules, thread length of 5–10, one-sentence marketing form, and `spec:visual_specs/...` references.
5. Record false acceptance, false rejection, and any unresolved semantic question without retroactively editing a historical run.

`inspect_runs.py` creates a compact source-to-claim review sheet after mechanically validating each run. Its `manual_semantic_clearance` field stays `PENDING_HUMAN_REVIEW`; the report must record the engineer's actual reading of every accepted claim. No saved output is automatically publication-cleared.
