# Residual scientific limitations and final acceptance verdict

## Evaluation against Section 16 final acceptance gate

| # | Acceptance condition | Component / evidence | Result | Verdict |
|---|---|---|---|---|
| 1 | Original problematic SWC-107 root-cause inference rejected without independent causal support | `content_pipeline/relation_integrity.py`, `tests/test_relation_integrity.py`, `heldout-final-code-results.json` (`RG11`) | Historic false-positive reproduction blocked as `VERIFICATION_ERROR` (or `INSUFFICIENT_EVIDENCE` without contradictory text); 0 false accepts on adverse causal claims in real model run | PASS |
| 2 | Genuinely supported causal statements remain eligible for approval | `assess_positive`, `test_direct_causal_source_and_recommendation_paraphrase_remain_eligible` | Deterministic eligibility preserved; SWC-105 causal statement approved when supported | PASS |
| 3 | Accurate recommendation paraphrases remain eligible for approval | Python gate, prompts, `fixtures/heldout.json` | Structurally eligible in gate logic; however, in real local `qwen3.5:4b` inference, recommendation-paraphrase recall was only 1/4 (25%) due to model-side over-rejection in the skeptical pass | FAIL (Model Yield) |
| 4 | Contradictory structured semantic verdicts cannot pass | `assess_positive`, `test_original_false_acceptance_is_blocked_and_preserved`, `test_structured_mismatch_and_skeptic_veto` | Contradiction flags, explicit opposition in rationale, and relationship verdict mismatches immediately trigger `VERIFICATION_ERROR` | PASS |
| 5 | Evidence provenance remains verified | `content_pipeline/provenance.py`, `export.py` | SHA-256 snapshot hashes, exact byte offsets, and option-to-quote mappings strictly validated | PASS |
| 6 | Reviewer scores cannot override relation failures | `content_pipeline/graph.py`, `export.py`, `test_export_rechecks_relation_even_if_review_or_saved_flag_claims_approval` | Exporter and graph independently re-run relation checks; Reviewer approval cannot force unverified claims into CSV | PASS |
| 7 | No failed mandatory claim enters CSV | `content_pipeline/export.py`, `output/relation-grounding-week/posts.csv` | Exact CSV header present; 0 rows exported in the real six-slot week | PASS |
| 8 | One-revision behavior remains unchanged | `content_pipeline/graph.py`, `week-inspection.json` | Every slot produced exactly two drafts (draft 1 + 1 revision) before being dropped; no runaway loops | PASS |
| 9 | All original PDF requirements remain satisfied | Full pipeline, `plan.json`, `kb.json`, `brand-voice.md` | Six planned slots (3 threads, 3 posts), brand rules, isolation, shared skills, CSV contract, and JSON trail preserved | PASS |
| 10 | Existing and new regression suites pass | `tests/` | All 98 deterministic pytest tests pass in 1.71 seconds | PASS |
| 11 | New held-out evaluation reported accurately | `audit/relation_grounding/heldout-final-code-results.json` | 20 frozen cases: 100% supported precision (4/4), 40% supported recall (4/10), 0% adverse false acceptance (0/10), 35% 5-label accuracy | PASS |
| 12 | Real six-slot run preserved and inspected | `output/relation-grounding-week/`, `08_SIX_SLOT_WEEK_INSPECTION.md` | Full run preserved with logs, summaries, reviews, and inspections for all 6 slots | PASS |
| 13 | Token and runtime overhead measured | `output/relation-grounding-week/summary.json` | 1,504.110 s elapsed, 203,991 prompt tokens, 25,418 completion tokens, peak 1 active Ollama call, $0 external API cost | PASS |
| 14 | Workflow viewer reflects actual implementation | `audit/visuals/workflow_viewer.html`, `viewer-final.png` | Updated to 16 pipeline stages including explicit Evidence Role, Relation Integrity, Skeptical Veto, and Final Export Gate | PASS |
| 15 | Residual uncertainty explicitly disclosed | `01_ROOT_CAUSE_AND_DESIGN.md`, `03_HELDOUT_OBSERVATIONS.md`, this report | Model over-rejection, small sample sizes, absence of external specialist adjudication, and zero shipped content documented | PASS |

---

## Final acceptance verdict

**VERDICT: REQUIRES REMEDIATION**

### Detailed assessment
1. **Safety and Architectural Invariants: FULL PASS**
   - The demonstrated causal inversion vulnerability (SWC-107 remediation text accepted as root-cause proof) is conclusively eliminated.
   - Contradictory model justifications, mismatching relationship verdicts, and ungrounded effectiveness guarantees are strictly blocked.
   - Reviewer scores cannot override failed relation checks.
   - The pipeline operates completely fail-closed: unverified claims never reach Visual Generation or the final CSV.
   - Parallel slot isolation, bounded single-revision limit, and Ollama concurrency limit of one functioned perfectly across all runs.

2. **Content Generation and Semantic Recall: REQUIRES REMEDIATION**
   - In the real six-slot execution (`output/relation-grounding-week/`), **0 of 6 slots shipped** (all 6 dropped after one revision).
   - In the frozen 20-case real-model benchmark (`heldout-final-code-results.json`), supported recall dropped to **40% (4/10)**, and recommendation-paraphrase recall was only **25% (1/4)**.
   - The local model (`qwen3.5:4b`) displays excessive skepticism and pedantic over-rejection during the second (skeptical) pass, rejecting valid paraphrases and source-attributed recommendations (e.g. rejecting "loss of funds" when the source states "loss of funds or data", or claiming a recommendation cannot support a "may call back" paraphrase).
   - Simply relaxing the Python gate is inadmissible as it would re-introduce false acceptance. Resolving this requires developing targeted Writer calibration prompts and a fresh, independently labeled holdout set.

---

## Residual scientific and operational limitations

1. **Local Model (`qwen3.5:4b`) Semantic Fragility**
   - Parameter capacity (4B) limits nuanced distinctions between syntactic paraphrasing and semantic entailment.
   - Even at deterministic configuration (temperature 0), small changes in prompting or context can cause noticeable decision variance (e.g., initial frozen run accepted 5/10 supported cases; final-code replay accepted 4/10).
2. **Evaluation Sample Size and Adjudication**
   - The frozen benchmark consists of 20 targeted cases (10 supported, 10 adverse). While effective as a regression probe, 20 cases are statistically insufficient to guarantee universal domain reliability.
   - Benchmark ground truth labels were authored by the internal implementing engineer based on source texts, without independent adjudication by an external third-party smart contract security auditor.
3. **Finite Knowledge Base**
   - Pinned KB contains 16 smart contract vulnerability entries; live web search and dynamic KB expansion are offline.
4. **Hardware and Operating Cost**
   - External model API charges were USD 0. Local compute, hardware depreciation, and electricity consumption were not instrumented.
