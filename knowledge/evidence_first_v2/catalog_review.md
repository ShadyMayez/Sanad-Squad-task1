# Pilot Proposition & Relation Catalog Review

**Catalog Version:** `2.0.0`  
**Status:** `REVIEWED_FOR_PILOT`  
**Review Date:** 2026-10-16  
**Auditor / Reviewer:** Principal Knowledge Engineering Architect  

---

## 1. Review Scope & Designation

This catalog establishes versioned, atomic factual units (`VerifiedProposition`) and directional semantic links (`TypedRelation`) for the Evidence-First V2 architecture.

> [!IMPORTANT]
> **Status Designation:** All entries are strictly designated `REVIEWED_FOR_PILOT`. This denotes thorough internal technical review against pinned cryptographic evidence snapshots for pilot evaluation and research feasibility. It does **not** constitute external third-party or client legal sign-off for commercial publication.

---

## 2. Topic Coverage & Evidence Witnesses

| Topic ID | Topic Name | Evidence ID | Snapshot Path | SHA-256 Verified | Total Propositions | Total Relations |
|---|---|---|---|---|---|---|
| `SWC-107` | Reentrancy | `SWC-107` | `source_snapshots/SWC-107.txt` | `bba44e8c...` | 5 | 5 |
| `SWC-104` | Unchecked Call Return Value | `SWC-104` | `source_snapshots/SWC-104.txt` | `beea34c8...` | 4 | 4 |
| `SWC-113` | DoS with Failed Call | `SWC-113` | `source_snapshots/SWC-113.txt` | `100572e9...` | 5 | 4 |
| `SWC-105` | Unprotected Ether Withdrawal | `SWC-105`, `OZ-OWNABLE` | `source_snapshots/SWC-105.txt`, `source_snapshots/OZ-OWNABLE.txt` | `9804c728...`, `397cfaf0...` | 5 | 5 |
| `SCWE-028` | Price Oracle Manipulation | `SCWE-028`, `OWASP-SC03` | `source_snapshots/SCWE-028.txt`, `source_snapshots/OWASP-SC03.txt` | `88beba8c...`, `5eb888bb...` | 5 | 5 |
| **Total** | | | | | **24** | **23** |

---

## 3. Detailed Proposition Audits

### 3.1 SWC-107 (Reentrancy)
- `PROP_SWC107_CONTROL_FLOW` [MECHANISM]: "Calling external contracts allows them to take over the execution control flow." (Grounded in `SWC-107#0`)
- `PROP_SWC107_REENTRANT_CALL` [MECHANISM]: "In a reentrancy attack, an external contract calls back into the caller before the initial invocation completes." (Grounded in `SWC-107#1`)
- `PROP_SWC107_UNDESIRABLE_INTERACTION` [CONSEQUENCE]: "Recursive callbacks can cause separate function invocations to interact in undesirable ways." (Grounded in `SWC-107#2`)
- `PROP_SWC107_CEI_PATTERN` [RECOMMENDATION]: "The Checks-Effects-Interactions pattern recommends performing all internal state changes before external calls are executed." (Grounded in `SWC-107#3`, `SWC-107#4`)
- `PROP_SWC107_REENTRANCY_GUARD` [RECOMMENDATION]: "Using a reentrancy lock, such as OpenZeppelin ReentrancyGuard, prevents reentrant function execution." (Grounded in `SWC-107#5`)

### 3.2 SWC-104 (Unchecked Call Return Value)
- `PROP_SWC104_RETURN_UNCHECKED` [FACT]: "The return value of low-level message calls is not checked by default." (Grounded in `SWC-104#0`)
- `PROP_SWC104_EXECUTION_RESUMES` [MECHANISM]: "Execution will resume even if the called contract throws an exception or fails." (Grounded in `SWC-104#1`)
- `PROP_SWC104_UNEXPECTED_BEHAVIOUR` [CONSEQUENCE]: "If a low-level call fails accidentally or deliberately, execution continuing without checks may cause unexpected behaviour in subsequent program logic." (Grounded in `SWC-104#2`)
- `PROP_SWC104_CHECK_RETURN` [RECOMMENDATION]: "If using low-level call methods, contracts must handle call failure by checking the returned boolean value." (Grounded in `SWC-104#3`)

### 3.3 SWC-113 (DoS with Failed Call)
- `PROP_SWC113_CALLS_CAN_FAIL` [FACT]: "External calls can fail accidentally or deliberately." (Grounded in `SWC-113#0`)
- `PROP_SWC113_DOS_CONDITION` [CONSEQUENCE]: "External call failures can cause a denial-of-service condition in the calling contract." (Grounded in `SWC-113#0`)
- `PROP_SWC113_ISOLATE_CALLS` [RECOMMENDATION]: "Isolate each external call into its own transaction initiated by the recipient to minimize damage from failures." (Grounded in `SWC-113#1`)
- `PROP_SWC113_PULL_PAYMENTS` [RECOMMENDATION]: "For payments, let users withdraw funds via pull payments rather than pushing funds automatically to reduce gas limit and DoS risks." (Grounded in `SWC-113#2`)
- `PROP_SWC113_AVOID_LOOP_CALLS` [RECOMMENDATION]: "Avoid combining multiple external calls in a single transaction loop and always handle potential failures." (Grounded in `SWC-113#3`)

### 3.4 SWC-105 & OZ-OWNABLE (Unprotected Ether Withdrawal)
- `PROP_SWC105_UNPROTECTED_WITHDRAWAL` [FACT]: "Due to missing or insufficient access controls, malicious parties can withdraw Ether from the contract account." (Grounded in `SWC-105#0`)
- `PROP_SWC105_EXPOSING_INIT` [MECHANISM]: "Unprotected withdrawal bugs are sometimes caused by unintentionally exposing contract initialization functions." (Grounded in `SWC-105#1`)
- `PROP_SWC105_LEGACY_CONSTRUCTOR` [MECHANISM]: "In legacy Solidity versions prior to 0.4.22, wrongly naming a function intended to be a constructor places the code in runtime bytecode where anyone can call it to re-initialize the contract." (Grounded in `SWC-105#2`, Applicability: `solidity_version < 0.4.22`)
- `PROP_SWC105_RESTRICT_WITHDRAWALS` [RECOMMENDATION]: "Implement access controls so Ether withdrawals can only be triggered by authorized parties according to smart contract specifications." (Grounded in `SWC-105#3`)
- `PROP_OZ_OWNABLE_MODULE` [RECOMMENDATION]: "Inheriting OpenZeppelin Ownable module provides an onlyOwner modifier to restrict function execution to the authorized owner address." (Grounded in `OZ-OWNABLE#0`, `OZ-OWNABLE#4`)

### 3.5 SCWE-028 & OWASP-SC03 (Oracle Manipulation)
- `PROP_SCWE028_EXPLOITATION` [DEFINITION]: "Price oracle manipulation refers to exploiting vulnerabilities in price oracles to manipulate contract execution logic." (Grounded in `SCWE-028#0`)
- `PROP_SCWE028_ADVERSE_CONSEQUENCES` [CONSEQUENCE]: "Oracle manipulation can lead to unauthorized actions, loss of funds, and exploitation of contract logic." (Grounded in `SCWE-028#1`, `SCWE-028#2`, `SCWE-028#3`)
- `PROP_OWASP_AGGREGATE_FEEDS` [RECOMMENDATION]: "Contracts should aggregate multiple oracle and DEX price sources and reject anomalous outlier deviations." (Grounded in `OWASP-SC03#0`, `OWASP-SC03#1`)
- `PROP_OWASP_TWAP_DEFENSE` [RECOMMENDATION]: "Use Time-Weighted Average Prices (TWAPs) over sufficient windows and reject stale prices exceeding maximum staleness thresholds." (Grounded in `OWASP-SC03#2`, `OWASP-SC03#3`)
- `PROP_OWASP_FAILSAFE_BEHAVIOR` [RECOMMENDATION]: "Implement fail-safe behaviors that halt sensitive operations like borrowing or liquidations when oracle data is suspicious or unavailable." (Grounded in `OWASP-SC03#6`)

---

## 4. Referential & Structural Boundaries

1. **No Causal Inversions:** Recommendations are linked to consequences via `MITIGATES` or `ACTION_RATIONALE`, never `CAUSES`.
2. **Structural Scope Isolation:** `PROP_SWC105_LEGACY_CONSTRUCTOR` explicitly encapsulates `applicability: {"solidity_version": "<0.4.22"}`. Content plans selecting this proposition require this qualifier.
3. **No Splicing Across Vulnerability Domains:** Cross-vulnerability causal relationships are rejected by catalog validation. A proposition from `SWC-113` cannot be linked to a proposition in `SWC-105` without an independent explicit evidence witness.
