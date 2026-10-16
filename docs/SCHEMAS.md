# Persisted artifact contracts

All JSON is UTF-8. Contracts are Pydantic models in `content_pipeline/schemas.py`, with generated JSON Schema files in `schemas/`. Regenerate them with `PYTHONPATH=. .venv/bin/python scripts/export_schemas.py`. Unknown fields are ignored by Pydantic. IDs are stable strings.

| File | Shape |
|---|---|
| `resolved_plan.json` | `Plan`: `slots[]` of `{id,type,focus?}` after overrides. |
| `research_log.json` | Ordered list of `{slot_id,topic?,source_ids[],evidence[],status,reason?}`. Evidence includes pinned snapshot, hash, exact quotation, offsets, retrieval date, type, and scope. |
| `drafts/<slot>-attempt-N.json` | `Draft`: `tweets[]`, `claims[]`; each claim has exact tweet or sentence `text` and `evidence_ids[]`. Every sentence must be mapped. `N` is 1 or 2. |
| `validation_report.json` | Ordered list of `{slot_id,attempts[][]}`; each inner list contains Python rule errors. |
| `review_report.json` | Ordered list of `{slot_id,attempts[]}`; each attempt is `Review` with six 0–5 scores, `approved`, `reasons[]`, `corrections[]`, `grounding_assessment`, and optional per-claim `claim_support[]` annotations. A populated annotation must contain a real quote; an omitted annotation is allowed only when the separate complete atomic semantic report pins every public clause and the Reviewer itself approves. |
| `accepted_content.json` | Ordered accepted `SlotResult` objects with `image_spec_reference`; each contains slot, topic, evidence, draft and review history, and token counts. |
| `claims.json` | Ordered `ClaimsRecord[]`; each attempt contains extracted atomic claims, public text spans, qualifiers, and candidate evidence IDs. |
| `evidence_provenance.json` | Ordered `EvidenceProvenanceRecord[]`; per-slot source metadata and provenance errors. |
| `semantic_verification.json` | Ordered `SemanticRecord[]`; new records carry `schema_version: "2.0"`. Attempt-level verdicts include claim relations, evidence relation, relationship verdict, both independent pass records, selected source-role hints, relation gate result and error, exact supporting spans, reasons, context windows, and verifier latencies. Earlier records without `schema_version` remain parseable as legacy data and do not retroactively gain a passed relation gate. |
| `grounding_summary.json` | `GroundingSummary`: atomic claim and verdict counts, cumulative verifier latency, and accepted final claim count. |
| `failures.json` | Ordered non-accepted entries `{slot_id,status,reason}`. |
| `summary.json` | `{model,planned,shipped,dropped,failed,reasons[],elapsed_seconds,prompt_tokens_recorded?,completion_tokens_recorded?,usage_complete,peak_simultaneous_ollama_calls,external_model_api_charges_usd,local_inference_cost}`. `null` means no token measurement was available. |

Slot status is `accepted`, `dropped`, or `failed`. A drop means both content attempts were rejected. A failure means research, model, or another agent failed. CSV has exactly `Post Text,Image`, one accepted piece per row. Threads use numbered tweets separated by two newline characters inside a quoted CSV field. Image fields use the `spec:` prefix and a path relative to the run folder. A `SUPPORTED` semantic verdict is an independent model judgment tied to verified quotation bytes; the relation gate can veto that judgment but does not prove entailment.

