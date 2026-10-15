# 05 — Independent adversarial and integration tests

Run from `/home/shady/sandsquad`:

```bash
.venv/bin/python -m pytest -q tests audit/tests
.venv/bin/python audit/scripts/inspect_run.py output/sample-week
.venv/bin/python audit/scripts/probe_reviewer.py
```

The combined deterministic suite reported **45 passed in 1.99 seconds** (`evidence/combined-pytest.txt`): 22 existing tests plus 23 new audit-only tests. No application source file was changed. The new tests deliberately assert some undesirable current behaviors so that a green test result does not mean those behaviors are acceptable. Reproduction is `.venv/bin/python -m pytest -q audit/tests/test_independent_audit.py -k <test_name>`.

| Scenario | Independent result | Relevant code | Assessment |
|---|---|---|---|
| Invalid plan, type, missing brand, malformed vulnerability, invalid HTTP source | Rejected by loaders/Pydantic; CLI invalid type exited 2 with helpful error | `config.py:25-51`, `schemas.py:7-31`, `cli.py:73-80` | Pass. |
| Empty focus; unsupported explicit focus | Empty resolved to KB entry; unsupported focus failed only its slot | `skills.py:14-29`, `graph.py:49-53` | Pass for offline KB. |
| Reviewer approves hard-invalid hashtag | Python validation forced two rejections and drop; no visual | `validation.py:36-37`, `agents.py:59-61`, `graph.py:83-86` | Pass. |
| Reviewer approves false claim with real citation and quote | Graph accepted claim about lock preventing external control transfer | `agents.py:49-61` | **Defect A-01:** quote existence is not semantic support. |
| Reviewer approves fabricated SanadSquad audit count | Graph accepted a claim of 500 audited protocols despite no approved stats | `validation.py:8-49`, `agents.py:49-61` | **Defect A-01:** deterministic brand-stat rule absent; reviewer error can ship it. |
| Reviewer approves unrelated source ID | Graph accepted an oracle/reentrancy mismatch with a legitimate ID | `validation.py:20-26`, `agents.py:49-61` | **Defect A-01:** no semantic relation check. |
| Reviewer rejects valid-form draft twice | Exactly two drafts, two reviews, permanent drop, empty CSV | `graph.py:59-86,110-117`, `export.py:40-48` | Pass. |
| Contradictory reviewer response: approved but low scores | Code forced rejection and drop | `agents.py:58-61` | Pass. |
| Malformed structured writer/reviewer result | Slot failed; other worker continued where applicable | `llm.py:32-35`, `graph.py:62-81` | Pass for injected exceptions. |
| Reviewer failure after completed writer | Draft retained in failed result; no Visual or CSV | `graph.py:69-81,91-99` | Pass; review cannot complete during service failure. |
| Rejection feedback reaches revision | Second writer prompt contained corrections and reasons | `graph.py:59-65` | Pass. |
| Two slots start writing before either completes | Barrier test completed | `graph.py:136-150` | Pass: genuine parallel scheduling. |
| Two same-instance model requests with limit 1 or 2 | Measured peaks 1 and 2, respectively | `llm.py:14-22` | Pass per instance. |
| Two model instances each with limit 1 | Measured combined peak 2 | `llm.py:14-22` | **Defect A-04:** limiter is not truly global. |
| One research failure, one writer timeout, multiple reviewer failures | Failures remained isolated; healthy slot accepted where supplied | `graph.py:49-53,62-81,139-145` | Pass for these injections. |
| Slow first slot finishes after second | Exported accepted records remained in plan order | `export.py:19-20` | Pass. |
| Unexpected inner-worker exception | Outer graph returned failed slot and processed other worker | `graph.py:139-145` | Pass; partial context lost for the failed slot. |
| Forged accepted result with no review or visual | Exporter wrote accepted CSV row and empty visual spec | `export.py:31-48` | **Defect A-03:** exporter does not revalidate approval/spec. |
| CSV quote, comma, newline escaping | `csv.reader` round-tripped the string | `export.py:40-48` | Pass. |
| Corrupted `summary.json` | Independent artifact inspector raised JSON parse error | `audit/scripts/inspect_run.py` | Detection pass; app does not repair partial writes. |
| Brand rule edit, rubric edit, writer instruction edit | Changed content reached validator or model prompt without application edit | `config.py:44-51`, `agents.py:11-13` | Pass. |
| Misleading KB description | Lexical research selected SWC-107 for a fabricated quantum topic | `skills.py:18-29` | **Defect A-02:** schema and title/ID checks do not establish KB semantic integrity. |

The real Ollama Reviewer probe (`evidence/reviewer-probe.json`, 47.68 seconds) rejected four isolated adversarial cases: contradicted reentrancy claim, fabricated company authority, unrelated citation, and retrieved-text prompt injection. This is a positive result for those exact prompts. It does not negate the actual six-slot sample's five overbroad or unsupported approved sentences. A broader prompt-injection success rate was not measured.

The CLI smoke test `.venv/bin/python run_piece.py --type invalid --topic reentrancy` exited 2 and named the supported types (`evidence/invalid-piece-*`). Fresh real `run_piece.py` and `run_week.py` results are in report 06. No failed pytest assertions were suppressed or weakened; the tests expose the defects by asserting their observable present behavior. Future remediation should invert the defect probes into expected-rejection regression tests.
