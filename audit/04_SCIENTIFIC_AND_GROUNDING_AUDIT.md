# 04 — Scientific accuracy and grounding audit

## Method and source boundary

I inspected all 16 local KB records and all 22 substantive claim records in the original sample. The fresh audit run produced byte-identical `accepted_content.json` and `posts.csv`, so the same claim findings apply to both runs. The audit independently fetched all 17 KB URLs: all returned HTTP 200 (`evidence/kb-url-check.json`). I compared sample claims with the local excerpts and the underlying [SWC-107](https://swcregistry.io/docs/SWC-107/), [SWC-104](https://swcregistry.io/docs/SWC-104/), [SWC-105](https://swcregistry.io/docs/SWC-105/), [SWC-113](https://swcregistry.io/docs/SWC-113/), [OWASP SCWE-028](https://scs.owasp.org/SCWE/SCSVS-ORACLE/SCWE-028/), and [OWASP SC03](https://scs.owasp.org/sctop10/SC03-PriceOracleManipulation/) pages. A 200 response or matching title establishes neither current applicability nor support for a particular sentence.

Verdicts: **Supported** means the cited source supports the sentence as written; **Qualified** means the idea is plausible but needs narrower wording or context; **Unsupported** means a meaningful clause, frequency, guarantee, or causal link is not established by the cited material. Unsupported is not automatically the same as empirically false.

## Claim-level review of shipped sample

| ID | Exact published sentence | Cited evidence | Verdict | Assessment |
|---|---|---|---|---|
| T1.1 | A callee can reenter a contract before its first invocation finishes. | SWC-107 | Supported | Direct mechanism in source. |
| T1.2 | This happens when state is updated after an external call, allowing repeated use of stale state. | SWC-107 | Qualified | Source example and KB root cause support the risk, but the stored excerpt does not explicitly state the stale-state condition. |
| T1.3 | The root cause is that control flow passes to the callee before the initial update completes. | SWC-107 | Qualified | Valid for the described pattern, not a universal root cause of every reentrancy form. |
| T1.4 | Remediation involves performing internal state changes before the external call. | SWC-107 | Supported | Explicit remediation. |
| T1.5 | Using checks-effects-interactions ensures state is safe before any interaction occurs. | SWC-107 | **Unsupported** | The pattern orders state changes; the source does not guarantee state is safe against every issue. “Ensures” overstates the mitigation. |
| T1.6 | A reentrancy lock blocks the unwanted callback into the protected path. | SWC-107 | Supported | Cited mitigation and curated excerpt support this scoped description. |
| T1.7 | It does not prevent control passing to the external callee itself. | SWC-107 | Supported | Consistent with the source's external-control-flow mechanism; local excerpt states the distinction. |
| P1.1 | Review the return value from low-level calls to prevent accounting inconsistencies when a call fails but execution continues. | SWC-104 | Supported | Source says execution can resume after failed call and recommends checking return; accounting is a plausible consequence recorded in the curated excerpt. |
| T2.1 | When a withdrawal function lacks authorization checks, any caller can trigger the transfer. | SWC-105 | Supported | Source describes unauthorized Ether withdrawal. |
| T2.2 | The root cause is often omitting access control logic before the Ether moves. | SWC-105 | Qualified | Missing access control is supported; “often” is an unmeasured frequency claim. |
| T2.3 | Implementing msg.sender checks against a stored owner prevents unauthorized triggers. | SWC-105 | Qualified | The cited example has such a check; outcome depends on correct implementation and intended authorization model. |
| T2.4 | Using onlyOwner modifiers ensures only designated parties can initiate withdrawals. | SWC-105 | Qualified | True only for a correctly implemented and applied modifier; the source's sample alone does not justify an unconditional guarantee. |
| T2.5 | Without these controls, the contract's balance becomes vulnerable to external calls. | SWC-105 | **Unsupported** | The actual risk is unauthorized withdrawal through an exposed path. “External calls” is too broad and misidentifies the trust boundary. |
| T2.6 | Auditors should verify that every transfer path includes explicit access restrictions. | SWC-105 | **Unsupported** | The source addresses withdrawal authorization according to contract specification. It does not prescribe owner-style restrictions on every transfer path. |
| P2.1 | Review whether your withdrawal functions check msg.sender against an authorized owner to prevent unauthorized fund transfers. | SWC-105 | Supported | An appropriate review question for the cited access-control issue, subject to the contract's intended roles. |
| T3.1 | Contracts relying on single price feeds risk executing logic based on distorted market data. | SCWE-028 | Qualified | Oracle manipulation is supported, but a single feed is a risk factor rather than proof that its price can be distorted. |
| T3.2 | Security-critical calculations often fail because they trust an unvalidated or manipulable source. | SCWE-028 | **Unsupported** | The source describes possible manipulated decisions; it gives no failure frequency supporting “often fail.” |
| T3.3 | Exploits targeting these weaknesses distort contract logic by feeding the system inaccurate prices. | SCWE-028 | Supported | Directly describes oracle manipulation. |
| T3.4 | Mitigation requires validating inputs and switching to resilient oracle sources rather than single points of failure. | SCWE-028 | Qualified | Validation and resilient sources are recommended; “requires switching” is stronger than the source and may depend on design. |
| T3.5 | Aggregating multiple price sources creates a buffer against short-lived attempts to manipulate the feed. | OWASP-SC03 | **Unsupported** | OWASP lists aggregation and time-based defenses separately. It assigns resistance to short-lived manipulation to sufficient TWAP windows, not to aggregation alone. |
| T3.6 | Using time-weighted averages over sufficient windows further resists rapid price distortion attacks. | OWASP-SC03 | Supported | Matches the source's time-based defense. |
| P3.1 | Review how a single failing external call can revert a wider transaction and prevent progress for other participants. | SWC-113 | Supported | The source's payment-loop sample and local excerpt support this conditional risk. |

**Count:** 10 supported, 7 needing qualification, 5 unsupported as written. No fabricated client names, company statistics, audit results, or promotional links appeared in the sample. The five unsupported sentences were nevertheless approved by the real model reviewer and exported. This is a material output-quality failure, even though the code records valid source IDs for every sentence.

## KB entry review

All 16 records have the required schema fields, one or more evidence references, and reachable links. The table records topic-specific concerns; “title matched” is a limited check, not a full scientific endorsement of every curated paraphrase.

| KB ID | Topic | Independent observation |
|---|---|---|
| SWC-107 | Reentrancy | Source mechanism and CEI/lock remediation support the entry; local excerpt contains an explanatory synthesis about lock scope. |
| SWC-104 | Unchecked Call Return Value | Source confirms a failed low-level call can let execution continue; accounting consequence is a reasonable but derived illustration. |
| SWC-105 | Unprotected Ether Withdrawal | Source supports unauthorized withdrawals; source sample contains owner checks. Current sample overgeneralizes these controls. |
| SWC-106 | Unprotected SELFDESTRUCT | **Version-sensitive.** The old SWC page says the contract can be destroyed. Current Solidity documentation says Cancun-era `selfdestruct` usually transfers Ether without deleting code/storage, except the same-transaction creation case. The KB does not state this distinction. |
| SWC-112 | Delegatecall to Untrusted Callee | Source title and stated mechanism align; no sample output used it. |
| SWC-113 | DoS with Failed Call | Source describes failure-induced denial of service and a loop example; sample post is supported. |
| SWC-114 | Transaction Order Dependence | Source title and KB mechanism align; no sample output used it. |
| SWC-115 | Authorization through tx.origin | Source title and KB mechanism align; no sample output used it. |
| SWC-116 | Block Timestamp Dependence | Source title and KB mechanism align; no sample output used it. |
| SWC-120 | Weak Sources of Randomness | Source title and KB mechanism align; no sample output used it. |
| SWC-101 | Integer Overflow and Underflow | **Compiler-sensitive.** Solidity 0.8+ checks arithmetic by default; unchecked blocks and older versions differ. KB broadly mentions older versions, but lacks a precise applicability range. |
| SWC-109 | Uninitialized Storage Pointer | Legacy compiler behavior; KB lacks version/applicability context. |
| SWC-117 | Signature Malleability | Source title and KB mechanism align; no sample output used it. |
| SWC-100 | Function Default Visibility | **Compiler-sensitive.** Solidity 0.5+ requires explicit visibility, so a modern generic post needs version context. |
| SWC-110 | Assert Violation | Source title and KB mechanism align; no sample output used it. |
| SCWE-028 | Price Oracle Manipulation | OWASP source supports the mechanism and recommends input validation. Its second evidence URL separately recommends source aggregation and sufficient TWAP windows. |

The SWC Registry itself states that it has not been thoroughly updated since 2020. The version distinctions above are independently corroborated by [current Solidity `selfdestruct` guidance](https://docs.soliditylang.org/en/latest/introduction-to-smart-contracts.html), [Solidity 0.8 arithmetic changes](https://docs.soliditylang.org/en/latest/080-breaking-changes.html), and [Solidity 0.5 visibility changes](https://docs.soliditylang.org/en/v0.5.9/050-breaking-changes.html). Entries not used in the sample received structural, title, and link checks, not a full source-by-source technical proof.

## Reviewer reliability and adversarial controls

The code verifies that a reviewer-provided quote is a substring of the cited local excerpt (`agents.py:49-57`). It cannot decide if the whole sentence follows from that quote. In three deterministic adversarial cases, a fake reviewer with high scores and a real excerpt substring caused the graph to ship a contradicted reentrancy claim, a fabricated SanadSquad audit count, and a claim with an unrelated citation (`audit/tests/test_independent_audit.py`). This proves a trust-boundary weakness under reviewer error. A separate real `qwen3.5:4b` probe rejected those three claims and an injected instruction in evidence text (`evidence/reviewer-probe.json`); that probe does **not** establish a universal rejection rate. The real six-slot sample demonstrates missed overstatements.

The prompt labels evidence as data and tells agents to ignore embedded instructions, but no isolation or sanitization mechanism prevents an adversarial excerpt from reaching the model prompt. The one live injection probe was rejected; broader prompt-injection resistance remains **NOT VERIFIED**.
