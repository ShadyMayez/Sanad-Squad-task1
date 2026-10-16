# Frozen relation set: first real-model observation

The first 20-case run used `qwen3.5:4b` and the pinned local KB. It preserved the original SWC-107 negative case and used ten new positives and ten adverse cases across several vulnerability categories. All 20 calls returned measured usage. Results are in `heldout-results.json`; this file is the primary evidence.

| Measure | Observed |
|---|---:|
| Supported precision | 5/5 = 100% |
| Supported recall | 5/10 = 50% |
| Adverse false acceptance | 0/10 |
| Unsupported causal false acceptance | 0 in tested cases |
| Supported causal false rejection | 1 (`RG02`) |
| Recommendation paraphrase recall | 0/4 |
| Exact five-label accuracy | 8/20 = 40% |
| Initial evidence-relation classification accuracy | 9/20 = 45% |
| Mean verifier latency | 19.883 seconds per case |
| Prompt / completion tokens | 45,027 / 5,493 |
| External model API charges | USD 0; local operating costs unmeasured |

The original unsafe SWC-107 claim (`RG11`) was rejected as `INSUFFICIENT_EVIDENCE`. No adverse example was accepted. However, the model rejected four valid source-attributed recommendations (`RG04`–`RG07`), primarily in the skeptical pass, despite the prompt explicitly allowing that relationship. It also marked a valid SWC-106 causal statement (`RG02`) insufficient because the initial pass labeled a directly causal sentence `DIRECT_DESCRIPTIVE_SUPPORT`. Those are false rejections, not safety wins. Eight adverse cases received `CONTRADICTED` where the reference label was `INSUFFICIENT_EVIDENCE`, lowering exact label accuracy without causing a false acceptance. The source-relation labels were particularly weak, so they cannot be treated as ground truth.

This result does **not** support a claim that the model reliably preserves valid recommendations. The 20 cases are too small to estimate broad security accuracy, and labels were not independently adjudicated by an external specialist. The code was finalized while this Python process was running, so a separately named final-code replay is required for deployment-version metrics. That replay reuses the same fixed cases and therefore is not a new independent holdout.

## Final-code replay of the same frozen set

`heldout-final-code-results.json` completed with 20/20 measured cases and unchanged claim texts and labels. Supported precision was **4/4 = 100%**, supported recall **4/10 = 40%**, and adverse false acceptance **0/10**. The old causal claim `RG11` remained rejected. The one supported causal false rejection `RG02` remained. Recommendation-paraphrase recall improved only to **1/4 = 25%**; `RG05`–`RG07` remained false rejections. Exact five-label accuracy was **7/20 = 35%** and initial source-relation accuracy **9/20 = 45%**. Mean latency was **14.077 seconds**; prompt/completion tokens were **45,003 / 5,622**, with complete metadata. External API charges were USD 0; local operating cost remains unmeasured.

The different supported decisions on identical inputs demonstrate local-model response variance even at the configured temperature. The replay is a regression on the final implementation, not an independent new sample. The positive recall and recommendation recall fail the intended quality target, so the project cannot be declared fully accepted on semantic reliability grounds. The zero observed adverse acceptance is limited to these cases and does not imply universal safety.
