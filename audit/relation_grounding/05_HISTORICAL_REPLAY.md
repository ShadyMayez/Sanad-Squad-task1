# Unchanged historical A–T replay

The existing `audit/semantic/fixtures/benchmark.json` and runner were replayed with `qwen3.5:4b`; their original output remains untouched. The new result is `historical-replay.json`.

| Measure | Earlier saved run | Current replay |
|---|---:|---:|
| Cases | 20 | 20 |
| Supported precision / recall | 100% / 100% | 100% / 100% |
| Adverse false acceptance | 0 | 0 |
| Exact five-label accuracy | 80% | 80% |
| Mean verifier latency per case | 6.189 s | 8.646 s |
| Prompt tokens | 22,440 | 32,663 |
| Completion tokens | 1,867 | 3,528 |

The replay adds about 2.46 seconds per case and records more tokens. These are actual observations, but earlier context and prompt work also occurred between the saved baseline and this replay, so the entire difference cannot be attributed solely to relation fields. The A–T set has only two supported examples and did not contain the specific normative-to-causal SWC-107 failure, which is why unchanged A–T scores cannot establish closure. The separate frozen relation set exposes substantial false rejection of valid recommendations.
