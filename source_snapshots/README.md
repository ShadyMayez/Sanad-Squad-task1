# Pinned source attribution

Snapshots in `source_snapshots/` were retrieved on 2026-10-15 from the credited public pages below. Most files are normalized page text for local, offline audit; `source_quote` in `kb.json` is an exact substring with code-point offsets and a SHA-256 snapshot hash. The existing `excerpt` field is a local summary, not a verbatim citation. Reachability, hashing, and quotation integrity do not prove semantic correctness.

The SWC Registry source material is from the [SWC Registry](https://github.com/SmartContractSecurity/SWC-registry) under its [MIT license](https://github.com/SmartContractSecurity/SWC-registry/blob/master/LICENSE), reproduced in `SWC_LICENSE.txt`. Its pages warn that the content has not been thoroughly updated since 2020. The two OWASP records come from the [OWASP Smart Contract Security project](https://github.com/OWASP/owasp-scs), whose repository contains the matching `docs/SCWE/SCSVS-ORACLE/SCWE-028.md` and `docs/sctop10/SC03-PriceOracleManipulation.md` source pages. The project uses [CC BY-SA 4.0](https://github.com/OWASP/owasp-scs/blob/main/License.md), reproduced in `OWASP_LICENSE.md`. All snapshots were adapted by extracting and whitespace-normalizing the published page text for offline verification. Attribution, license notices, and source URLs accompany them; adapted OWASP text should be redistributed under the applicable ShareAlike terms.

- `SWC-107` — Reentrancy, https://github.com/SmartContractSecurity/SWC-registry/blob/master/entries/docs/SWC-107.md (active snapshot `source_snapshots/SWC-107-canonical.txt`, normalized from the preserved official Markdown `source_snapshots/SWC-107-official.md`, retrieved 2026-10-16). The prior flattened page snapshot `source_snapshots/SWC-107.txt` is retained so earlier diagnostic run hashes remain auditable; it collapsed separate remediation bullets and is no longer used by the active KB.
- `SWC-104` — Unchecked Call Return Value, https://swcregistry.io/docs/SWC-104/ (snapshot `source_snapshots/SWC-104.txt`, retrieved 2026-10-15).
- `SWC-105` — Unprotected Ether Withdrawal, https://swcregistry.io/docs/SWC-105/ (snapshot `source_snapshots/SWC-105.txt`, retrieved 2026-10-15).
- `SWC-106` — Unprotected SELFDESTRUCT, https://swcregistry.io/docs/SWC-106/ (snapshot `source_snapshots/SWC-106.txt`, retrieved 2026-10-15).
- `SWC-112` — Delegatecall to Untrusted Callee, https://swcregistry.io/docs/SWC-112/ (snapshot `source_snapshots/SWC-112.txt`, retrieved 2026-10-15).
- `SWC-113` — DoS with Failed Call, https://swcregistry.io/docs/SWC-113/ (snapshot `source_snapshots/SWC-113.txt`, retrieved 2026-10-15).
- `SWC-114` — Transaction Order Dependence, https://swcregistry.io/docs/SWC-114/ (snapshot `source_snapshots/SWC-114.txt`, retrieved 2026-10-15).
- `SWC-115` — Authorization through tx.origin, https://swcregistry.io/docs/SWC-115/ (snapshot `source_snapshots/SWC-115.txt`, retrieved 2026-10-15).
- `SWC-116` — Block Timestamp Dependence, https://swcregistry.io/docs/SWC-116/ (snapshot `source_snapshots/SWC-116.txt`, retrieved 2026-10-15).
- `SWC-120` — Weak Sources of Randomness, https://swcregistry.io/docs/SWC-120/ (snapshot `source_snapshots/SWC-120.txt`, retrieved 2026-10-15).
- `SWC-101` — Integer Overflow and Underflow, https://swcregistry.io/docs/SWC-101/ (snapshot `source_snapshots/SWC-101.txt`, retrieved 2026-10-15).
- `SWC-109` — Uninitialized Storage Pointer, https://swcregistry.io/docs/SWC-109/ (snapshot `source_snapshots/SWC-109.txt`, retrieved 2026-10-15).
- `SWC-117` — Signature Malleability, https://swcregistry.io/docs/SWC-117/ (snapshot `source_snapshots/SWC-117.txt`, retrieved 2026-10-15).
- `SWC-100` — Function Default Visibility, https://swcregistry.io/docs/SWC-100/ (snapshot `source_snapshots/SWC-100.txt`, retrieved 2026-10-15).
- `SWC-110` — Assert Violation, https://swcregistry.io/docs/SWC-110/ (snapshot `source_snapshots/SWC-110.txt`, retrieved 2026-10-15).
- `SCWE-028` — Price Oracle Manipulation, https://scs.owasp.org/SCWE/SCSVS-ORACLE/SCWE-028/ (snapshot `source_snapshots/SCWE-028.txt`, retrieved 2026-10-15).
- `OWASP-SC03` — Price Oracle Manipulation, https://scs.owasp.org/sctop10/SC03-PriceOracleManipulation/ (snapshot `source_snapshots/OWASP-SC03.txt`, retrieved 2026-10-15).
- `OZ-OWNABLE` — OpenZeppelin Ownable Access Control, https://github.com/OpenZeppelin/openzeppelin-contracts/blob/v5.0.0/contracts/access/Ownable.sol (snapshot `source_snapshots/OZ-OWNABLE.txt`, retrieved 2026-10-16).

