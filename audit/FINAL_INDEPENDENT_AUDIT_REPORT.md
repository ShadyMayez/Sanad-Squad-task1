# SanadSquad — final independent engineering audit

**Verdict: REQUIRES REMEDIATION.** The six-slot LangGraph workflow executes on the specified local model, produces the required artifacts, and survives the tested failure paths. Its accepted sample nevertheless contains technical claims that are not fully supported by their cited evidence. The output should not be treated as publishable without a claim-level check.

This report is an independent audit of the implementation at baseline commit `20e028a8906a1082f384aa8388b5b2a7d0181cb9`. Audit work created only files under `audit/` and the requested ZIP. Application source, configuration, existing tests, and the original `output/sample-week/` were not changed.

## 1. Scope and method

I read both pages of the supplied SanadSquad PDF as the acceptance contract. I inspected the full pipeline, input schemas, editable instructions, graph routing, local model wrapper, validation, export, prior results, and upstream reference snapshot. I ran 23 new audit-only deterministic tests alongside the 22 existing tests, a fresh real six-slot week, a fresh real technical piece, four real Reviewer probes, and read-only artifact validation. The claim audit checked each of the 22 structured claims in both byte-identical six-slot outputs against its cited KB excerpt and primary references.

The principal evidence lives in [`evidence/`](evidence/), the independent tests in [`tests/test_independent_audit.py`](tests/test_independent_audit.py), and the reconstruction and detailed findings in reports 01–07. A passing mock test proves a specific control path; it is not treated as proof that a live model will always make a sound semantic judgment.

## 2. Architecture reconstructed from code

The outer LangGraph loads six validated slots, fans them out with `Send`, and reduces independent `SlotResult` values. The inner per-slot graph routes Research → configured Writer → Python validation and model Reviewer → Visual on approval, or one feedback revision and second review before a permanent drop. Worker exceptions become failed slot results, and final export restores plan order. Two configured writer roles use separate instruction files and one generic writer class. Research and Reviewer invoke the same evidence lookup object.

See [`01_ARCHITECTURE_RECONSTRUCTION.md`](01_ARCHITECTURE_RECONSTRUCTION.md) and the [interactive workflow viewer](visuals/workflow_viewer.html). The architecture view shows rejected, failed, and approved paths; the execution view shows the fresh real run and explicitly labels unrecorded per-slot durations.

## 3. PDF acceptance decision

The independently checked matrix is [`02_INDEPENDENT_ACCEPTANCE_MATRIX.md`](02_INDEPENDENT_ACCEPTANCE_MATRIX.md). Core contracts pass: six slots with a 3+3 split, 16 KB entries, editable brand and writer files, topic selection for empty focus, one shared skill, genuine slot fan-out, the single-revision bound, accepted-only visual routing, the three CLI forms, exact CSV header, and complete run folders. The normal week reported 6 shipped, 0 dropped, 0 failed.

The requirement that every factual claim be supported and that output be suitable to post **fails**. Source IDs and excerpt strings are traceable, but they do not by themselves prove the whole claim. Source-outage handling and usage replayability are partial. Writer specialization is functionally present through configuration, though implemented by one generic class. These distinctions are not hidden in a single blanket PASS.

## 4. Agent, graph, and control assessment

The graph uses real conditional routing and a bounded path. Tests injected hard-rule failure, first- and second-pass rejection, malformed structured output, timeouts, reviewer failure, unsupported focus, slow completion, and simultaneous slot scheduling. A rejected or failed normal-graph slot never reached Visual or CSV. With one `LocalModel`, the semaphore measured one active inference call; two separate model instances each configured for one measured a combined peak of two. The per-instance scope is a reliability defect if multiple weekly runs share the same Ollama server.

Detailed state, handoff, retry, isolation, and limiter findings are in [`03_AGENT_AND_LANGGRAPH_AUDIT.md`](03_AGENT_AND_LANGGRAPH_AUDIT.md). An exporter called directly with a forged accepted result wrote a row without a final review or visual specification; that is an API boundary defect, while the current graph prevents that input in normal execution.

## 5. Scientific and factual grounding

All 17 KB URLs returned HTTP 200 during the audit, which proves reachability only. The sources support the general vulnerability topics. The independent claim ledger in [`04_SCIENTIFIC_AND_GROUNDING_AUDIT.md`](04_SCIENTIFIC_AND_GROUNDING_AUDIT.md) classifies 22 shipped claims: **10 supported, 7 requiring qualification, 5 unsupported or overbroad as written**. Examples include a statement that checks-effects-interactions *ensures* safe state, advice to put access restrictions on every transfer path, an unquantified frequency claim, and attributing resistance to short-lived oracle manipulation to aggregation rather than to a suitable time window. These are precise wording and attribution problems; the audit does not assert that every sentence is wholly false.

The KB also contains version-sensitive legacy SWC topics. Some entries carry broad older-version qualifiers, but applicability is absent or insufficiently precise for automatic modern content, particularly `selfdestruct` behavior. The six sample slots did not use those entries, so that is a prospective risk rather than an observed error in the current week.

## 6. Adversarial results

The combined suite reported **45 passed in 1.99 seconds**: 22 baseline tests and 23 independent audit tests. Some new tests deliberately document defects by asserting the current undesirable result. A controlled approving reviewer caused semantically false or fabricated claims with valid source IDs and quotes to ship; a hard-invalid hashtag still dropped, proving the deterministic gate works. Four separate **real** `qwen3.5:4b` Reviewer probes rejected a contradicted reentrancy claim, invented company authority, an unrelated citation, and a retrieved-text instruction injection. This narrow success cannot cancel the unsupported wording observed in the actual six-slot output.

See [`05_ADVERSARIAL_TEST_RESULTS.md`](05_ADVERSARIAL_TEST_RESULTS.md) and the saved test and probe evidence. The audit did not weaken validation, mark a rejected draft approved, or use a cloud model.

## 7. Real execution and artifact integrity

Ollama server **0.40.3** served the installed `qwen3.5:4b` model. The fresh week exited 0 in **172.639 seconds application time** and shipped **6 / 6** with **0 dropped and 0 failed**. Recorded usage was **9,156 prompt** and **3,802 completion** tokens. The fresh technical piece exited 0 in **39.303 seconds**, shipped one six-tweet thread, and recorded **1,676 prompt** and **1,019 completion** tokens. The real week generated 7-, 6-, and 6-tweet threads. The accepted content and CSV files are byte-identical to the original saved sample; the original sample was not overwritten.

The saved summary reports **$0.00 external model API charges** for local inference. Electricity and hardware costs are unavailable. Raw Ollama response usage, per-call timestamps, retry events, and per-slot durations were not saved, so the audit can reconcile reported totals but cannot independently replay the raw model usage or timing. The saved one-call peak is consistent with the single-run configuration, while the separate-instance test establishes the scope limitation. See [`06_REAL_EXECUTION_REPORT.md`](06_REAL_EXECUTION_REPORT.md) and [`evidence/fresh-week/`](evidence/fresh-week/).

## 8. Defect priorities and remediation

The reproducible register is [`07_DEFECT_REGISTER.md`](07_DEFECT_REGISTER.md). There is **one critical finding**: A-01, semantic evidence mismatch and overbroad technical claims approved and exported. There are **no separate high-severity findings**. Medium findings cover legacy topic applicability (A-02), exporter trust of a forged accepted status (A-03), per-instance rather than server-wide inference limiting (A-04), incomplete raw observability (A-05), and partial-write/partial-context handling (A-06). A low finding records the one-class/two-role writer design (A-07).

The shortest safe remediation path is to block automatic publishing of accepted output until each complete claim is checked against its evidence, add regression cases based on the five observed sentences, then enforce approval and nonblank specs at export. Add precise version metadata for legacy KB entries and an explicitly scoped shared inference limiter. Persist bounded model-call and slot timing events so future usage and duration claims can be independently checked. Re-run the deterministic suite and a fresh live six-slot week after those changes.

## 9. Visual deliverables and evidence limits

Open [`visuals/workflow_viewer.html`](visuals/workflow_viewer.html) for the main self-contained, interactive architecture and execution viewer. Static exports are [`workflow.svg`](visuals/workflow.svg), [`workflow.png`](visuals/workflow.png), [`workflow.mmd`](visuals/workflow.mmd), [`execution_trace.svg`](visuals/execution_trace.svg), and [`execution_trace.png`](visuals/execution_trace.png). The execution graphic uses persisted counts, topics, sources, decision statuses, token totals, and run duration. It does not invent node durations or trace timestamps absent from the artifacts. The visual design is explanatory, not an additional runtime measurement.

## 10. Final verdict

**REQUIRES REMEDIATION.** The assignment is substantially implemented and demonstrably runs locally with the specified graph, commands, input contracts, source records, retry bound, artifacts, and model. The critical grounding weakness prevents an unconditional acceptance or a claim that the six exported pieces are ready to publish. The result is a working engineering system with a concrete, reproducible quality defect and a defined correction path.
