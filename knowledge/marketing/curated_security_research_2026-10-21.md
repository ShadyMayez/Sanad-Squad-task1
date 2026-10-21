# SanadSquad | Curated Marketing Security Research Knowledge Base
Prepared: 2026-10-21
Scope: Official Marketing Knowledge Layer for SanadSquad's Five Commercial Services
Authority: Curated editorial research library and seed index (Fixture / Offline). NOT live runtime verification proof.

## 1. Authority Boundaries & Ingestion Rules
- **Strict KB Separation**: This marketing knowledge layer is completely distinct from the technical-thread proposition catalog (`knowledge/evidence_first_v2/`) and the audit database (`audits.json`).
- **Audits Invariant**: `audits.json` remains strictly empty (`[]`). No client audits or third-party endorsements are claimed.
- **Verification Flag**: All entries are marked `verification_status: "external_research_checked_runtime_fetch_required"`. They are not marked live-retrieved. In fixture runs, `research_mode=fixture` is disclosed.
- **Company Identity**: Official services are defined by SanadSquad's published website profile (revalidated locally). Factual technical claims are backed by independent official publications.
- **Publication Gate**: Copy generated from this knowledge must pass deterministic format constraints, character budgets ($\le 280$ chars), semantic conformance, and independent Reviewer evaluation.

---

## 2. Technical Evidence Library (14 Sources)

### TRACK 1: Blockchain Security Audits (`blockchain-security-audits` -> `web3-security`)
#### W01 — Solana: Verifying Programs
- **Source ID**: `W01`
- **Publisher**: Solana Documentation
- **URL**: `https://solana.com/docs/programs/verified-builds`
- **Publication Date**: Unknown / Reference manual (Checked: 2026-10-21)
- **Research Category**: `web3-security`
- **Supported Claims**:
  - Verification deterministically compares deployed on-chain bytecode against source code built in a reproducible container.
  - Establishes source-to-deployment correspondence; does NOT ensure security or absence of logic bugs.
  - Verification metadata must be updated after upgrades; a changed deployed binary requires verification of that new version.
- **Unsupported / Prohibited Claims**:
  - "Verified build means the program is audited or vulnerability-free."
  - "Upgrades are inherently unauthorized."
- **Customer Problem**: Solana teams confusing matching bytecode with logic correctness.
- **Suitable Formats**: `short-tip`, `differentiation`
- **Publication Eligibility**: Requires runtime fetch or fixture disclosure.

#### W02 — Solana: Deploying Programs
- **Source ID**: `W02`
- **Publisher**: Solana Documentation
- **URL**: `https://solana.com/docs/programs/deploying`
- **Publication Date**: Unknown / Reference manual (Checked: 2026-10-21)
- **Research Category**: `web3-security`
- **Supported Claims**:
  - Program upgrade authority controls program modifications and is stored in `ProgramData`.
  - Authority can be transferred to a multi-sig or governance contract, or revoked to make the program immutable.
- **Unsupported / Prohibited Claims**:
  - "Retaining upgrade authority is automatically malicious or compromised."
  - "A multi-sig eliminates all governance and centralization risk."
- **Customer Problem**: Protocol governance leads managing post-deployment admin privileges.
- **Suitable Formats**: `differentiation`, `service-overview`
- **Publication Eligibility**: Requires runtime fetch or fixture disclosure.

#### W03 — OpenZeppelin: ERC-4626 Guide
- **Source ID**: `W03`
- **Publisher**: OpenZeppelin Documentation
- **URL**: `https://docs.openzeppelin.com/contracts/5.x/erc4626`
- **Publication Date**: Unknown / Reference manual (Checked: 2026-10-21)
- **Research Category**: `web3-security`
- **Supported Claims**:
  - Vault share pricing mechanics, empty-vault inflation (donation) attacks, and slippage tradeoffs.
  - Virtual shares/assets and offset decimal mitigations help protect initial depositors.
- **Unsupported / Prohibited Claims**:
  - "All ERC-4626 vaults are exploitable."
  - "Default mitigations eliminate every economic or rounding attack."
- **Customer Problem**: DeFi vault developers facing share price manipulation and initial deposit griefing.
- **Suitable Formats**: `short-tip`, `learning-resource`
- **Publication Eligibility**: Requires runtime fetch or fixture disclosure.

#### W04 — OpenZeppelin: Proxy API
- **Source ID**: `W04`
- **Publisher**: OpenZeppelin Documentation
- **URL**: `https://docs.openzeppelin.com/contracts/5.x/api/proxy`
- **Publication Date**: Unknown / Reference manual (Checked: 2026-10-21)
- **Research Category**: `web3-security`
- **Supported Claims**:
  - Distinguishes Transparent and UUPS proxy patterns, upgrade authorization behavior, and privileged proxy administrator roles.
  - Implementation contracts and initialization mechanics require strict authorization design.
- **Unsupported / Prohibited Claims**:
  - "Upgradeable contracts are automatically insecure."
  - "OpenZeppelin audited SanadSquad."
- **Customer Problem**: Protocol architects managing proxy upgrade privileges and storage collision risks.
- **Suitable Formats**: `differentiation`, `service-overview`, `short-tip`
- **Publication Eligibility**: Requires runtime fetch or fixture disclosure.

---

### TRACK 2: Penetration Testing (`penetration-testing` -> `pentesting`)
#### P01 — OWASP API1:2023 Broken Object Level Authorization
- **Source ID**: `P01`
- **Publisher**: OWASP API Security Project
- **URL**: `https://api-security.owasp.org/editions/2023/en/0xa1-broken-object-level-authorization/`
- **Publication Date**: 2023 (Checked: 2026-10-21)
- **Research Category**: `pentesting`
- **Supported Claims**:
  - Broken Object Level Authorization occurs when an API fails to validate whether an authenticated user is permitted to access a specific resource object.
  - BOLA is distinct from authentication failure (login).
- **Unsupported / Prohibited Claims**:
  - "Every API is affected by BOLA."
  - "BOLA is failed login authentication."
  - Naming unverified real dApps as vulnerable.
- **Customer Problem**: Web3 application engineers assuming user authentication protects tenant resource boundaries.
- **Suitable Formats**: `short-tip`, `learning-resource`
- **Publication Eligibility**: Requires runtime fetch or fixture disclosure.

#### P02 — OWASP API Security Top 10 2023
- **Source ID**: `P02`
- **Publisher**: OWASP API Security Project
- **URL**: `https://api-security.owasp.org/editions/2023/en/0x11-t10/`
- **Publication Date**: 2023 (Checked: 2026-10-21)
- **Research Category**: `pentesting`
- **Supported Claims**:
  - Differentiates API1 (BOLA), API2 (Broken Authentication), API5 (Broken Function Level Authorization), API7 (Server-Side Request Forgery), and other categories.
  - Distinguishes object-level access from function-level administrative permissions.
- **Unsupported / Prohibited Claims**:
  - Specific calldata/signing-front-end exploit claims without separate primary incident evidence.
- **Customer Problem**: Security leads testing only login endpoints while missing object- and function-level authorization gaps.
- **Suitable Formats**: `differentiation`, `service-overview`
- **Publication Eligibility**: Requires runtime fetch or fixture disclosure.

#### P03 — MCP Specification Announcement: Authorization Hardening
- **Source ID**: `P03`
- **Publisher**: Model Context Protocol (MCP) Maintainers
- **URL**: `https://blog.modelcontextprotocol.io/posts/2026-07-28/`
- **Publication Date**: 2026-07-28 (Checked: 2026-10-21)
- **Research Category**: `pentesting`
- **Supported Claims**:
  - MCP specification revision introduces auth hardening, request routing, and server/client trust boundaries.
  - Addresses security isolation between client environments and tool-executing servers.
- **Unsupported / Prohibited Claims**:
  - "Every deployed MCP server automatically adopts the updated spec or becomes secure."
- **Customer Problem**: Infrastructure teams integrating AI protocol servers without defining clear RPC trust boundaries.
- **Suitable Formats**: `news-reaction`, `short-tip`
- **Publication Eligibility**: Requires runtime fetch or fixture disclosure.

---

### TRACK 3: Agentic Security Tooling (`agentic-security-tooling` -> `agentic-security`)
#### A01 — OWASP Agent Control Standard (ACS)
- **Source ID**: `A01`
- **Publisher**: OWASP GenAI Security Project
- **URL**: `https://genai.owasp.org/resource/agent-control-standard-acs/`
- **Publication Date**: 2026-09-01 (Checked: 2026-10-21)
- **Research Category**: `agentic-security`
- **Supported Claims**:
  - Establishes runtime middleware hooks, execution boundaries, and declarative safety policies outside model context.
  - Restricts unauthorized tool execution and reduces blast radius.
- **Unsupported / Prohibited Claims**:
  - "OWASP ACS universally prevents all prompt injection."
  - "OWASP ACS mandates a dollar spending cap."
  - "Simon Willison is the publisher of the OWASP standard."
- **Customer Problem**: Autonomous agent platforms invoking external APIs and wallets without hard runtime boundaries.
- **Suitable Formats**: `learning-resource`, `news-reaction`
- **Publication Eligibility**: Requires runtime fetch or fixture disclosure.

#### A02 — OWASP Top 10 for Agentic Applications 2026
- **Source ID**: `A02`
- **Publisher**: OWASP GenAI Security Project
- **URL**: `https://genai.owasp.org/resource/owasp-top-10-for-agentic-applications-for-2026/`
- **Publication Date**: 2025-12-09 (Checked: 2026-10-21)
- **Research Category**: `agentic-security`
- **Supported Claims**:
  - Reference taxonomy for recognizing autonomous agent risks (tool misuse, authorization hijacking, unconstrained delegation).
  - Recommends decoupling transaction signing authority from unstructured LLM output.
- **Unsupported / Prohibited Claims**:
  - "OWASP certifies any specific vendor implementation as safe without audit."
- **Customer Problem**: Teams deploying tool-augmented LLMs without formal threat modeling for autonomous delegation.
- **Suitable Formats**: `differentiation`, `learning-resource`
- **Publication Eligibility**: Requires runtime fetch or fixture disclosure.

#### A03 — GitHub Code Scanning on Pull Requests
- **Source ID**: `A03`
- **Publisher**: GitHub Documentation
- **URL**: `https://docs.github.com/en/code-security/concepts/code-scanning/code-scanning-on-pull-requests`
- **Publication Date**: Unknown / Reference manual (Checked: 2026-10-21)
- **Research Category**: `agentic-security`
- **Supported Claims**:
  - Integrating automated security analysis directly into pull-request workflows catches vulnerabilities prior to code merge.
  - Demonstrates the operational value of shift-left security checks in continuous integration.
- **Unsupported / Prohibited Claims**:
  - "GitHub endorses SanadSquad or its custom detectors."
  - Unsubstantiated detection rate claims (e.g., "100% bug detection").
- **Customer Problem**: Protocol development teams suffering regressions between periodic point-in-time audits.
- **Suitable Formats**: `differentiation`, `service-overview`
- **Publication Eligibility**: Requires runtime fetch or fixture disclosure.

---

### TRACK 4: Agentic Payments (`agentic-payments` -> `agentic-payments`)
#### M01 — x402 Foundation: Facilitator Specification
- **Source ID**: `M01`
- **Publisher**: x402 Foundation
- **URL**: `https://github.com/x402-foundation/x402/blob/main/docs/core-concepts/facilitator.md`
- **Publication Date**: Unknown / Reference specification (Checked: 2026-10-21)
- **Research Category**: `agentic-payments`
- **Supported Claims**:
  - x402 defines payment requirement signaling via HTTP 402 status codes and headers.
  - Facilitators are optional service providers that verify and settle payments on behalf of resource servers.
  - Resource servers can verify and settle payments directly peer-to-peer.
- **Unsupported / Prohibited Claims**:
  - "Every x402 payment requires a third-party facilitator."
  - "HTTP 402 status code alone transfers funds."
- **Customer Problem**: Agent builders confusing HTTP payment signaling with required third-party settlement intermediaries.
- **Suitable Formats**: `short-tip`, `learning-resource`
- **Publication Eligibility**: Requires runtime fetch or fixture disclosure.

#### M02 — MPP: EVM and x402 Support
- **Source ID**: `M02`
- **Publisher**: Machine Payments Protocol (MPP) / Stripe
- **URL**: `https://mpp.dev/blog/evm-x402-support`
- **Publication Date**: 2026-06-08 (Checked: 2026-10-21)
- **Research Category**: `agentic-payments`
- **Supported Claims**:
  - In June 2026, mppx SDK added unified interface support for MPP EVM charge and compatible x402 exact payment flows.
  - Illustrates convergence toward multi-protocol agent payment client interfaces.
- **Unsupported / Prohibited Claims**:
  - "MPP and x402 specifications are identical or completely interchangeable."
  - "All blockchain networks and payment methods are supported."
- **Customer Problem**: Developers unsure how to design unified client interfaces supporting both x402 and MPP flows.
- **Suitable Formats**: `news-reaction` (dated 2026-06-08)
- **Publication Eligibility**: Requires runtime fetch or fixture disclosure.

#### M03 — MPP: Improved Sessions Experience
- **Source ID**: `M03`
- **Publisher**: Machine Payments Protocol (MPP) / Stripe
- **URL**: `https://mpp.dev/blog/sessions-improved`
- **Publication Date**: 2026-06-17 (Checked: 2026-10-21)
- **Research Category**: `agentic-payments`
- **Supported Claims**:
  - Session authorization allows an agent to authorize spending once, with incremental authorization extension based on consumption.
  - Well-suited for high-frequency or usage-based API calls.
- **Unsupported / Prohibited Claims**:
  - "Sessions eliminate all authorization, replay, or spending risks."
  - Universal quantitative cost reduction claims.
- **Customer Problem**: Autonomous agent applications incurring high overhead from per-request discrete authorizations.
- **Suitable Formats**: `short-tip`, `learning-resource`
- **Publication Eligibility**: Requires runtime fetch or fixture disclosure.

---

### TRACK 5: Security Consulting (`security-consulting` -> `web3-security` & cross-cutting)
#### C01 — NIST SP 800-218: Secure Software Development Framework v1.1
- **Source ID**: `C01`
- **Publisher**: National Institute of Standards and Technology (NIST)
- **URL**: `https://csrc.nist.gov/pubs/sp/800/218/final`
- **Publication Date**: 2022-02 (Checked: 2026-10-21)
- **Research Category**: `web3-security` (Cross-cutting)
- **Supported Claims**:
  - Security practices belong throughout the entire software development lifecycle (requirements, threat modeling, architecture review, and provenance).
  - Pre-implementation design review mitigates structural flaws that audits alone cannot easily fix post-coding.
- **Unsupported / Prohibited Claims**:
  - "NIST endorses or certifies SanadSquad."
  - "Adopting SSDF guarantees zero vulnerabilities."
- **Customer Problem**: Protocol founders postponing security reviews until code freeze, discovering architectural flaws too late.
- **Suitable Formats**: `differentiation`, `service-overview`
- **Publication Eligibility**: Requires runtime fetch or fixture disclosure.

#### C02 — OpenZeppelin: Proxy Architecture and Governance Design
- **Source ID**: `C02` (Cross-referenced to `W04`)
- **Publisher**: OpenZeppelin Documentation
- **URL**: `https://docs.openzeppelin.com/contracts/5.x/api/proxy`
- **Publication Date**: Unknown / Reference manual (Checked: 2026-10-21)
- **Research Category**: `web3-security` (Cross-cutting)
- **Supported Claims**:
  - Transparent vs UUPS architectural choices, admin upgrade keys, and timelock governance design create essential pre-implementation architectural questions.
- **Unsupported / Prohibited Claims**:
  - "Every architecture must be immutable or follow a single vendor pattern."
- **Customer Problem**: Founding teams needing architecture reviews before committing to upgrade patterns.
- **Suitable Formats**: `differentiation`, `service-overview`, `short-tip`
- **Publication Eligibility**: Requires runtime fetch or fixture disclosure.

---

## 3. Ten Evidence-Backed Editorial Briefs (B01–B10)

| Brief ID | Service Line | Target Audience | Technical Problem / Hook | Source IDs | Formats |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **B01** | Blockchain audits | Solana protocol teams | Verified build establishes source correspondence, not freedom from logic flaws. | `W01` | `short-tip`, `differentiation` |
| **B02** | Blockchain audits | Protocol governance leads | Retained upgrade authority represents keyholder centralization requiring continuous review. | `W02`, `W04` | `differentiation`, `service-overview` |
| **B03** | Blockchain audits | DeFi vault engineers | Empty ERC-4626 vaults face share inflation attacks; mitigation and rounding review required. | `W03` | `short-tip`, `learning-resource` |
| **B04** | Penetration testing | Web3 app engineers | An authenticated user is not automatically authorized to access another user's resource objects. | `P01` | `short-tip`, `learning-resource` |
| **B05** | Penetration testing | API & security leads | Distinguishing object-level permissions (BOLA) from authentication and function-level access. | `P02` | `differentiation`, `service-overview` |
| **B06** | Agentic security tooling | AI agent platform owners | Runtime policy hooks and action observability restrict unauthorized tool execution outside context. | `A01` | `learning-resource`, `news-reaction` |
| **B07** | Agentic security tooling | Protocol CI maintainers | Automated PR security analysis surfaces invariant regressions before code merge. | `A03` + company | `differentiation`, `service-overview` |
| **B08** | Agentic payments | Agent payment builders | x402 uses HTTP 402 signaling; third-party facilitators are optional, not mandatory. | `M01` | `short-tip`, `learning-resource` |
| **B09** | Agentic payments | Payment integrators | MPP's June 2026 support for x402 flows in mppx unifies spending limits and settlement interfaces. | `M02` | `news-reaction` |
| **B10** | Security consulting | Protocol founders | Pre-implementation architecture reviews, governance design, and threat modeling before deployment. | `C01`, `C02` | `differentiation`, `service-overview` |

---

## 4. Reference Copy Candidates (Editorial Benchmarks Only)
These 10 posts (`E01`–`E10`) are editorial reference baselines for human evaluation. They must NEVER be substituted for or counted as model qualification outputs.
- `E01`: A verified Solana build answers: does deployed bytecode match this source? It cannot answer: is the program's logic safe? Treat source verification, security review and upgrade controls as separate checks. (201 chars, W01)
- `E02`: Upgradeable contracts need two reviews: what can the code do, and who can replace it? Upgrade authorization is part of the threat model, not just a deployment detail. (173 chars, W02/W04)
- `E03`: An empty ERC-4626 vault can be sensitive to donation-based share-price manipulation. Review initial exchange-rate behavior, slippage protection and the vault's chosen inflation mitigations before launch. (200 chars, W03)
- `E04`: A valid login does not authorize every object. BOLA lets an authenticated user access another user's records when object-level permission checks are missing. Test the resource boundary, not just sign-in. (202 chars, P01)
- `E05`: An audited contract can still depend on an exposed admin API. SanadSquad's penetration testing covers off-chain dApp endpoints and infrastructure, including authorization paths that connect users to privileged operations. (214 chars, P01/P02)
- `E06`: Security review at release is late for fast-moving protocols. SanadSquad builds tailored security detectors, PR reviewers and monitoring agents to help teams spot risky changes and investigate deployed behavior. (209 chars, A03)
- `E07`: OWASP's Agent Control Standard addresses runtime visibility and policy hooks for tool-using agents. Read the original standard: https://genai.owasp.org/resource/agent-control-standard-acs/ (188 chars, A01)
- `E08`: An x402 facilitator is optional, not a magic settlement guarantee. A resource server can verify and settle directly or delegate those steps. Review where payment authorization, verification and settlement really happen. (216 chars, M01)
- `E09`: MPP added support for compatible x402 exact flows in mppx in June 2026. The integration question now includes spending controls and verification paths, not just protocol labels. Source: https://mpp.dev/blog/evm-x402-support (223 chars, M02)
- `E10`: Before deploying an upgradeable protocol, ask who can change the implementation, which approvals are required and how changes are reviewed. Security architecture starts before the audit. (187 chars, C01/C02)
