# 06 — Original artifact verification and fresh Ollama execution

## Runtime identity and commands

On this host, `ollama --version` reported server **0.40.3** (client 0.24.0). `ollama list` contained `qwen3.5:4b`, model ID `c46e961bbacc`. The application's default endpoint is `http://127.0.0.1:11434`. No cloud model or paid API was used.

Fresh commands were executed from `/home/shady/sandsquad` with stdout, stderr, exit code, and wall time captured under `audit/evidence/`:

```bash
.venv/bin/python run_week.py --plan plan.json --output audit/evidence/fresh-week
.venv/bin/python run_piece.py --type tech-thread --topic reentrancy --output audit/evidence/fresh-piece
.venv/bin/python run_piece.py --type invalid --topic reentrancy
```

| Run | Exit | Application elapsed | Shell wall time | Shipped / dropped / failed | Prompt / completion tokens | Peak active calls |
|---|---:|---:|---:|---|---:|---:|
| Original `output/sample-week/` | unavailable | 162.991 s | unavailable | 6 / 0 / 0 | 9,156 / 3,802 | 1 (saved counter) |
| Fresh audit week | 0 | 172.639 s | 174.65 s | 6 / 0 / 0 | 9,156 / 3,802 | 1 (saved counter) |
| Fresh audit piece | 0 | 39.303 s | 41.12 s | 1 / 0 / 0 | 1,676 / 1,019 | 1 (saved counter) |
| Invalid-type smoke | 2 | n/a | not timed | no run | n/a | n/a |

The independent parser (`audit/scripts/inspect_run.py`) checked every required artifact, parsed persisted Pydantic contracts, reconciled plan IDs and final statuses, re-ran deterministic validation on accepted drafts, checked final review approval, checked CSV rows and image-spec paths, and reconciled token totals against accepted slot records. It passed for both week folders and the standalone piece. It does **not** validate the semantic truth of content; report 04 does that separately.

The original and fresh `accepted_content.json` SHA-256 are both `3178fa483b6c33d59e066d69a69e16cd22561029cf6d7d034306407be53bf1c4`; their `posts.csv` SHA-256 are both `05f7c7decd62afb13ba2c9cf5bba8eaa02ed0d08d6f0d4cad9bfcddc11b94ed0`. Thus the saved six pieces and their per-slot token fields are byte-identical across runs. The summaries differ in elapsed time. This verifies consistency of the prior artifact claim, not independent raw Ollama accounting: raw response usage and per-call timestamps were not persisted.

## Fresh week slot trace

These are **observed persisted values**. “Revision” means another content draft after review rejection; it does not count any transport retry. Per-slot duration is unavailable because the application records only run-level elapsed time.

| Slot | Resolved topic and source | Writer | Drafts / revisions | Final reviewer | Visual spec | Final status | Recorded tokens in / out | Slot duration |
|---|---|---|---:|---|---|---|---:|---|
| `thread_1` | Reentrancy; SWC-107 | Technical | 1 / 0 | Approved | Present | Accepted; 7 tweets | 1,684 / 1,072 | unavailable |
| `post_1` | Unchecked Call Return Value; SWC-104 | Marketing | 1 / 0 | Approved | Present | Accepted; 1 tweet | 1,393 / 287 | unavailable |
| `thread_2` | Unprotected Ether Withdrawal; SWC-105 | Technical | 1 / 0 | Approved | Present | Accepted; 6 tweets | 1,594 / 894 | unavailable |
| `post_2` | Unprotected Ether Withdrawal; SWC-105 | Marketing | 1 / 0 | Approved | Present | Accepted; 1 tweet | 1,395 / 341 | unavailable |
| `thread_3` | Price Oracle Manipulation; SCWE-028 and OWASP-SC03 | Technical | 1 / 0 | Approved | Present | Accepted; 6 tweets | 1,760 / 942 | unavailable |
| `post_3` | DoS with Failed Call; SWC-113 | Marketing | 1 / 0 | Approved | Present | Accepted; 1 tweet | 1,330 / 266 | unavailable |

The three empty focuses were `post_1`, `thread_2`, and `post_3`; their resolved topics and source IDs appear in `research_log.json`. The CSV has the exact header `Post Text,Image`, six accepted records, quoted multiline thread text, and `spec:` paths to existing `.md` files. No dropped or failed slot appears in this particular real run. The separate deterministic fault-injection tests establish those paths.

## Reviewer decisions and factual quality

All six real reviewers approved on first pass and gave criterion-level scores. The audit's independent claim review found five shipped sentences unsupported or overbroad as written, plus seven needing qualification (report 04). The model also rejected all four direct adversarial Reviewer probes; that narrower success does not make the published sample fully reliable. The visual specs are written instructions, not rendered images. No content was published.

`summary.json` reports external model API charges as **$0.00** because the model was local. It explicitly excludes electricity and hardware costs. Token fields reconcile arithmetically, but the repository does not retain raw Ollama responses, model call counts, per-call timing, per-slot duration, or retry events; those remain unavailable rather than inferred from six successful slots.
