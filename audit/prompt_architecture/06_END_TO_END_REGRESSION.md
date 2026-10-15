# End-to-end regression

## Deterministic gates

Command: `.venv/bin/python -m pytest -q`. Current result: **68 passed**. This includes file-loaded SystemMessage/HumanMessage separation, untrusted source-data placement, genuinely shared EvidenceLookup usage, pinned source integrity, atomic claim coverage, one content revision, fabricated Reviewer quote rejection, complete semantic support with omitted duplicate Reviewer quote metadata, hard-rule vetoes, isolated slot failure, accepted-only export, and content-dependent written visuals. These fixtures are mocked and do not establish real model quality.

## Real-model checks

The `qwen3.5:4b` 20-case semantic benchmark accepted 2/2 supported examples and 0/15 adverse examples; four expected rejection-category labels differed, for 80% exact five-label accuracy. Six synthetic source-text prompt-injection probes yielded 0/6 false accepts. See `../semantic/04_ADVERSARIAL_BENCHMARK.md` and `05_PROMPT_EVALUATION_RESULTS.md` for evidence and limitations.

The first full genuine Ollama week, `output/semantic-final-week/`, ended with **0 shipped, 6 dropped, 0 failed** after 1042.85 seconds. All six branches ran and the rejection/export contracts held, but content generation did not succeed. We inspected every final draft and found source recommendations upgraded into causal guarantees or additional reviewer actions absent from pinned quotes. The Reviewer also sometimes omitted duplicate quote metadata on clauses already verified with exact spans. Source-first Writer prompts and a bounded, conditional Reviewer quote rule address these root causes without weakening semantic, hard-rule, or Reviewer score vetoes.

## Final technical piece

The final source-bound technical piece at `output/semantic-final-accepted-piece/` completed with **1 shipped, 0 dropped, 0 failed** in 69.305 application seconds. It produced five ordered reentrancy tweets, five exact pinned source spans, one approving six-score review, one written visual specification, and one accepted-only CSV row. The independent artifact inspector passed. Ollama reported 12,625 prompt and 1,330 completion tokens with complete usage metadata and peak one concurrent call. The earlier three rejected piece diagnostics remain in the audit trail; see `../semantic/06_REAL_OLLAMA_EXECUTION.md` for root causes and fixes.

## First six-slot closure run

The real `qwen3.5:4b` run at `output/semantic-closure-week/` finished **2 shipped, 4 dropped, 0 failed** in 644.509 application seconds. `thread_1` and `post_1` passed all final claim, provenance, hard-rule, Reviewer, and visual gates. Their CSV records reference existing `spec:visual_specs/` files. Each dropped slot retained two drafts and specific rejection reasons; none entered the CSV or Visual Agent. The run recorded 89,416 prompt and 10,754 completion tokens with complete usage metadata and peak one concurrent Ollama call. The independent inspector parsed every JSON artifact and checked accepted claim IDs, exact span IDs and quotations, thread length, reviewer approval, CSV quoting, and spec paths. The accepted texts were manually compared with pinned SWC-107 and SWC-104 statements. See `../semantic/06_REAL_OLLAMA_EXECUTION.md` for individual drop causes.

## Final-code six-slot run before visual wording correction

The second genuine run, `output/semantic-final-verified-week/`, shipped **3**, dropped **3**, and failed **0** in 587.657 application seconds. It recorded 83,764 prompt and 9,875 completion tokens, complete usage metadata, and peak one active call. `thread_1`, `post_1`, and `post_3` had supported final claims, passing rubric scores, written specs, and accepted-only CSV rows. `thread_2`, `post_2`, and `thread_3` dropped with explicit format or evidence reasons. The independent artifact inspector passed all JSON contracts, source/span matches, lengths, review decisions, and CSV/spec paths. Manual text inspection found the three shipped actions faithful to their SWC-107, SWC-104, and SWC-113 source statements.

Manual visual inspection then found one unstated type detail (“success flag”) in the `post_1` spec. The deterministic Visual Agent now says “return value” and gives `post_3` a recipient-transaction diagram matching its accepted text. These changes are covered by `test_visual_spec_uses_only_supported_return_value_and_transaction_terms`. The original run remains untouched.

## Final release six-slot run

The final real run at `output/semantic-release-week/` shipped **3**, dropped **3**, and failed **0** in 580.873 application seconds. It recorded 84,640 prompt and 9,980 completion tokens with complete Ollama metadata and peak one concurrent call. `thread_1`, `post_1`, and `post_3` were approved on the first draft and have exact pinned final claim spans and content-specific written image specs. `thread_2` failed the hard minimum thread length after one revision; `post_2` and `thread_3` failed evidence entailment after their revisions. No rejected item entered the CSV or visuals. The independent inspector passed all persisted JSON contracts, source and span references, thread length, review decisions, exact CSV header and three records, and spec paths. Manual claim and visual inspection is in `../semantic/FINAL_CONTENT_INSPECTION.md`. The observed 3/6 acceptance is the current local-model result; the historical six-of-six sample predates these gates.
