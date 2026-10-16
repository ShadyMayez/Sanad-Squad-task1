# Implementation and deterministic regression

## Changed contracts

- `content_pipeline/schemas.py`: additive claim relation hints, selected-span source-role hints, structured evidence relationship, contradiction/uncertainty indicators, and persisted relation gate results. `semantic_verification.json` now emits `schema_version: "2.0"`. Older JSON without that field remains parseable as legacy evidence; it does not claim to have passed the new gate.
- `content_pipeline/relation_integrity.py`: source-role syntax hints and veto-only positive-decision checks. Normative-only spans cannot prove an independently asserted root cause; explicit source-attributed recommendations need a normative selected span; recommendation-only text cannot establish a guarantee. Obvious positive-verdict contradictions fail.
- `content_pipeline/semantic_verification.py`: first and skeptical passes both record relationship fields and run the veto. A relation mismatch becomes insufficient evidence and uses the existing one-revision route. A genuinely inconsistent structured positive becomes verification error. Initial and skeptical records are retained.
- `content_pipeline/graph.py` and `content_pipeline/export.py`: Reviewer approval and Visual execution require relation-passed claims; export reconstructs and reruns the deterministic relation check against final exact spans.
- `instructions/*.md`: Writer, Verifier, skeptic, and Reviewer instructions distinguish descriptions, causes, consequences, recommendations, effectiveness, and source scope.
- `audit/scripts/build_closure_visuals.py`: viewer and diagram name claim extraction, evidence role, relation verification, skeptic, Reviewer, and final acceptance separately.

## Deterministic observation

Command: `.venv/bin/python -m pytest -q`

Observed: **98 passed in 1.39 seconds** on the current edited tree. The targeted relation module has 12 passing tests, including the saved historical false acceptance, direct causal eligibility, source-attributed recommendation eligibility, unrelated normative support, guarantee rejection, inconsistent positive, skeptical veto, prompt injection against the Python gate, and export-time recheck. `git diff --check` and Python compilation also passed. These fixtures use controlled responses and prove gate behavior, not model-level semantic accuracy.

The legacy `thread_1` source artifact remains unchanged. The deterministic replay of its exact claim, exact selected span, and original contradictory reason now returns `VERIFICATION_ERROR`. If the same model asserts support but omits the contradictory phrase, the normative-only source still yields `INSUFFICIENT_EVIDENCE`. Neither state qualifies for review approval, Visual generation, or CSV export. Accurate source-attributed recommendation and directly sourced causal statements remain structurally eligible when both model passes support them.
