# SanadSquad | External Security Research and Marketing Knowledge Pack
Prepared: 2026-10-21
Purpose: High-quality, source-backed reference material for Antigravity to integrate into the SanadSquad V3 content pipeline.
Status: Editorial research briefing, not proof that SanadSquad's LiveResearchProvider fetched these pages during a pipeline run. Public technical material was checked through web research; company capabilities below follow the previously supplied official SanadSquad service profile, which the coding agent must revalidate before ingestion.
Boundary: Company websites can support the advertised service offering. Independent official technical publications support technical facts. Generated marketing copy must still pass runtime source verification and all V3 quality gates.

## 1. Source-of-truth rules for ingestion
- Research this pack as a candidate research index and editorial brief, not as kb.json, an audit record, a fresh-news feed, a customer success story, or an automatically verified current live result.
- Every source should have an immutable ID, exact original URL, publisher, title, source date (if known), access-check date, service tags, supported claims, excluded claims, and a verification state.
- Store stable descriptions in a dedicated marketing-research data source, maintaining technical-thread KB authority separation.
- At generation time, LiveResearchProvider must retrieve sources and record final URL, HTTP status, content excerpt and hash; fixture runs can use frozen excerpts but must disclose research_mode=fixture.
- The official company site supports the five advertised offerings. It is not proof that a particular client engagement succeeded or that the company audited a named third party. Leave audits.json empty.
- Do not claim that a provided link is publication-eligible if it fails allowlist, redirect, HTTP retrieval, excerpt verification or freshness rules. Never invent an alternative URL.
- Do not describe every topic as a breaking-news story. Use dated primary announcements for news reactions, technical documents for tips/resources, and approved company claims for service overviews.

## 2. Curated primary technical evidence library

### WEB3 / BLOCKCHAIN SECURITY
- **W01 — Solana, Verifying Programs**
  - URL: https://solana.com/docs/programs/verified-builds
  - Publisher: Solana documentation.
  - Supported: Verification compares deployed executable and deterministically built source; it establishes source/deployment correspondence, not security. Verification metadata should be updated after upgrades; a changed deployed binary requires verification of that version.
  - NOT supported: 'verified means audited', 'verified means vulnerability-free', 'upgrades are inherently unauthorized'.

- **W02 — Solana, Deploying Programs**
  - URL: https://solana.com/docs/programs/deploying
  - Publisher: Solana documentation.
  - Supported: Program authority controls program updates; it can be transferred, or removed to make a program immutable. ProgramData stores program executable code.
  - NOT supported: A retained authority is automatically malicious; a multisig eliminates all governance risk.

- **W03 — OpenZeppelin, ERC-4626 guide**
  - URL: https://docs.openzeppelin.com/contracts/5.x/erc4626
  - Publisher: OpenZeppelin documentation.
  - Supported: Vault share pricing, empty-vault inflation/donation attacks, slippage and mitigation tradeoffs.
  - NOT supported: All ERC-4626 vaults are exploitable; default mitigations eliminate every attack.

- **W04 — OpenZeppelin, Proxy API**
  - URL: https://docs.openzeppelin.com/contracts/5.x/api/proxy
  - Publisher: OpenZeppelin documentation.
  - Supported: Distinguishes transparent and UUPS proxy patterns, upgrade authorization behavior, privileged proxy administrators, and implementation risks.
  - NOT supported: 'OpenZeppelin audited SanadSquad', or that an upgradeable proxy is automatically insecure.

### PENTESTING / OFF-CHAIN SECURITY
- **P01 — OWASP API1:2023, Broken Object Level Authorization**
  - URL: https://api-security.owasp.org/editions/2023/en/0xa1-broken-object-level-authorization/
  - Publisher: OWASP API Security Project (2023).
  - Supported: An already authenticated user may reach another user's object when object-level authorization fails. This is distinct from failed login authentication.
  - NOT supported: Every API is affected; any specific unverified real dApp is vulnerable.

- **P02 — OWASP API Security Top 10 2023**
  - URL: https://api-security.owasp.org/editions/2023/en/0x11-t10/
  - Publisher: OWASP API Security Project (2023).
  - Supported: Differentiates API1 BOLA, API2 broken authentication, API5 broken function-level authorization, API7 SSRF, and other categories.
  - NOT supported: A specific calldata/signing-front-end exploit unless separately evidenced by its actual incident report.

- **P03 — MCP 2026-07-28 specification announcement**
  - URL: https://blog.modelcontextprotocol.io/posts/2026-07-28/
  - Publisher: MCP maintainers; 2026-07-28.
  - Supported: MCP specification revised auth hardening, request handling and routing architecture; authorization changes address server/client trust boundaries.
  - NOT supported: Every deployed MCP server automatically adopts the updated spec or becomes secure.

### AGENTIC SECURITY TOOLING
- **A01 — OWASP Agent Control Standard (ACS)**
  - URL: https://genai.owasp.org/resource/agent-control-standard-acs/
  - Publisher: OWASP GenAI Security Project; 2026-09-01.
  - Supported: Agent transparency, runtime middleware hooks, inspectable execution and declarative policy enforcement across agent frameworks.
  - NOT supported: OWASP promises it prevents all prompt injection; OWASP specifies a mandatory wallet spending cap in dollars; Simon Willison is publisher of the OWASP standard.

- **A02 — OWASP Top 10 for Agentic Applications 2026**
  - URL: https://genai.owasp.org/resource/owasp-top-10-for-agentic-applications-for-2026/
  - Publisher: OWASP GenAI Security Project; 2025-12-09 (2026 framework).
  - Supported: A reference framework for recognizing autonomous-agent security risks and building controls around tool-using workflows.
  - NOT supported: OWASP certifies a particular implementation as safe without independent evaluation.

- **A03 — GitHub Code Scanning on Pull Requests**
  - URL: https://docs.github.com/en/code-security/concepts/code-scanning/code-scanning-on-pull-requests
  - Publisher: GitHub documentation.
  - Supported: Pull-request security analysis can surface findings before merge; illustrates the workflow value of PR security checks.
  - NOT supported: GitHub endorses SanadSquad or its custom AI detectors; no false efficacy percentages.

### AGENTIC PAYMENTS
- **M01 — x402 Foundation, Facilitator**
  - URL: https://github.com/x402-foundation/x402/blob/main/docs/core-concepts/facilitator.md
  - Publisher: x402 Foundation specification.
  - Supported: x402 uses payment-required request/response signaling; a facilitator is optional but recommended for verifying and settling payments. Servers can handle those operations directly.
  - NOT supported: Every x402 payment requires a third-party facilitator; HTTP 402 status alone transfers funds.

- **M02 — MPP, EVM and x402 support**
  - URL: https://mpp.dev/blog/evm-x402-support
  - Publisher: MPP; dated 2026-06-08.
  - Supported: mppx supports MPP EVM charge and compatible x402 exact flows from one SDK interface.
  - NOT supported: Entire specifications are interchangeable or identically secure; all networks and payment methods are supported.

- **M03 — MPP, Improved sessions experience**
  - URL: https://mpp.dev/blog/sessions-improved
  - Publisher: MPP; dated 2026-06-17.
  - Supported: A session can authorize spending once and incrementally extend authorization with usage; useful for usage-based APIs.
  - NOT supported: Sessions eliminate authorization, replay, spending or settlement risk; all session costs universally decrease by the same amount.

### SECURITY CONSULTING / SECURE DESIGN
- **C01 — NIST SP 800-218, Secure Software Development Framework v1.1**
  - URL: https://csrc.nist.gov/pubs/sp/800/218/final
  - Publisher: NIST; published 2022-02.
  - Supported: Security practices belong throughout the development lifecycle, including requirements, design choices, security reviews and software provenance.
  - NOT supported: NIST endorses or certifies SanadSquad; following SSDF guarantees zero vulnerabilities.

- **C02 — OpenZeppelin Proxy API**
  - URL: https://docs.openzeppelin.com/contracts/5.x/api/proxy
  - Publisher: OpenZeppelin; also W04.
  - Supported: Upgrade-admin privileges, Transparent/UUPS architectural choices and authorization design create meaningful pre-implementation review questions.
  - NOT supported: Every architecture must be immutable or must use a specific vendor pattern.

## 3. SanadSquad service-offering authority: prior provided company profile
Source authority: Prior user-provided SANADSQUAD_OFFICIAL_SERVICE_PROFILE.md, based on SanadSquad's public website. Company pages could not be independently fetched by the current web retrieval tool; the coding agent must revalidate locally before treating them as current company evidence.
- **Blockchain security audits**: https://sanadsquad.com/services/blockchain-security-audits/ — manual EVM/Solana/Sui audit focus, invariant/accounting/access review, mitigation review; specialized fuzzing/formal verification only where scoped. Maps to research group web3-security.
- **Penetration testing**: https://sanadsquad.com/services/penetration-testing/ — web/API, blockchain infrastructure and off-chain component assessments. Maps to pentesting.
- **Agentic security tooling**: https://sanadsquad.com/services/ai-security-tooling/ — custom security detectors, pull-request reviewers and monitoring agents. Maps to agentic-security. Do not equate this service merely with AI red teaming.
- **Agentic payments**: https://sanadsquad.com/services/agentic-payments/ — x402/MPP agent implementations, MCP servers and payment authorization review. Maps to agentic-payments.
- **Security consulting**: https://sanadsquad.com/services/consulting/ — design/architecture review and development-phase security advice. Cross-cutting, but its commercial identity must remain distinct.

Company contacts recorded in the earlier official-site report: frank@sanadsquad.com and https://sanadsquad.com/contact/; no confirmed public telephone number. Do not activate commercial CTAs until the existing company-contact approval state authorizes publication. Keep the recruitment channel for recruitment only. Leave audits.json empty.

## 4. Ten evidence-backed editorial briefs ready to seed the planner
- **B01** (Blockchain audits, Solana teams): A verified build answers source identity, not whether logic has vulnerabilities. Source: W01. Formats: short-tip, differentiation.
- **B02** (Blockchain audits, Protocol governance leads): Who can replace code after an audit? Upgrade authority is a control surface. Sources: W02, W04. Formats: differentiation, service-overview.
- **B03** (Blockchain audits, DeFi vault engineers): An empty vault can expose share-price inflation attacks; what defenses are needed? Source: W03. Formats: short-tip, learning-resource.
- **B04** (Penetration testing, Web3 app engineers): An authenticated user is not automatically authorized to read another user's object. Source: P01. Formats: short-tip, learning-resource.
- **B05** (Penetration testing, API/security leads): BOLA, broken login and function-level authorization are different tests. Source: P02. Formats: differentiation, service-overview.
- **B06** (Agentic security tooling, Agent platform owners): Runtime policy hooks and action visibility matter when AI is allowed to operate tools. Source: A01. Formats: learning-resource, news-reaction (dated 2026-09-01).
- **B07** (Agentic security tooling, Protocol CI maintainers): PR-level alerts can make security findings available before merge; tailor checks to protocol invariants. Sources: A03 + official service. Formats: differentiation, service-overview.
- **B08** (Agentic payments, Agent/API payment builders): x402 facilitators simplify verification/settlement but are optional. Source: M01. Formats: short-tip, learning-resource.
- **B09** (Agentic payments, Payment integrators): MPP's June 2026 x402 support makes authorization and verification design a better comparison than protocol tribalism. Source: M02. Format: news-reaction.
- **B10** (Security consulting, Protocol founders): Which design decisions must be reviewed before implementation? Privileged upgrades and requirements are early decisions. Sources: C01, C02. Formats: differentiation, service-overview.

## 5. Prewritten copy candidates: reference examples only
Examples below are drafted editorially, NOT produced by Antigravity's local Ollama model. Each must still be checked by the V3 writer/reviewer and runtime evidence pipeline, and should not be counted as an AI-generated acceptance test.
- **E01 — Solana verified-build distinction (short-tip, W01)**: A verified Solana build answers: does deployed bytecode match this source? It cannot answer: is the program's logic safe? Treat source verification, security review and upgrade controls as separate checks.
- **E02 — Upgrade governance (differentiation, W02/W04)**: Upgradeable contracts need two reviews: what can the code do, and who can replace it? Upgrade authorization is part of the threat model, not just a deployment detail.
- **E03 — Vault inflation risk (short-tip, W03)**: An empty ERC-4626 vault can be sensitive to donation-based share-price manipulation. Review initial exchange-rate behavior, slippage protection and the vault's chosen inflation mitigations before launch.
- **E04 — BOLA (short-tip, P01)**: A valid login does not authorize every object. BOLA lets an authenticated user access another user's records when object-level permission checks are missing. Test the resource boundary, not just sign-in.
- **E05 — API security offering (service-overview, P01/P02 + company page)**: An audited contract can still depend on an exposed admin API. SanadSquad's penetration testing covers off-chain dApp endpoints and infrastructure, including authorization paths that connect users to privileged operations.
- **E06 — Agentic tooling (service-overview, A03 + company page)**: Security review at release is late for fast-moving protocols. SanadSquad builds tailored security detectors, PR reviewers and monitoring agents to help teams spot risky changes and investigate deployed behavior.
- **E07 — OWASP ACS (learning-resource, A01)**: OWASP's Agent Control Standard addresses runtime visibility and policy hooks for tool-using agents. Read the original standard: https://genai.owasp.org/resource/agent-control-standard-acs/
- **E08 — x402 facilitator nuance (short-tip, M01)**: An x402 facilitator is optional, not a magic settlement guarantee. A resource server can verify and settle directly or delegate those steps. Review where payment authorization, verification and settlement really happen.
- **E09 — MPP x402 news (news-reaction, M02)**: MPP added support for compatible x402 exact flows in mppx in June 2026. The integration question now includes spending controls and verification paths, not just protocol labels. Source: https://mpp.dev/blog/evm-x402-support
- **E10 — Security consulting (short-tip, C01/C02)**: Before deploying an upgradeable protocol, ask who can change the implementation, which approvals are required and how changes are reviewed. Security architecture starts before the audit.

## 6. Editorial rules and common false claims
- Distinguish (i) authoritative sources for factual mechanics, (ii) SanadSquad's advertised offerings, and (iii) editorial interpretation.
- Do not say 'Solana verified builds prove smart contracts safe' (W01 contradicts it).
- Do not say 'a program with upgrade authority is malicious' (W02 describes authorized administration).
- Do not say 'BOLA is failed authentication' (P01/P02 separate authorization from login).
- Do not say 'OWASP ACS stops all prompt injection' or 'OWASP ACS mandates spending limits' (A01 makes neither guarantee).
- Do not link to Simon Willison and call it an OWASP document. Cite the real OWASP ACS URL for ACS claims.
- Do not say 'x402 requires a facilitator' (M01 calls it optional).
- Do not call MPP and x402 totally interchangeable (M02 describes specific compatible flows in a specific SDK).
- Do not say 'formal verification guarantees correctness' or 'audits prove bug freedom'.
- Do not say 'SanadSquad has audited [third-party project]' unless separately approved records prove it. Keep audits.json=[].
- news-reaction requires a dated, specific event AND a supporting live-verified source URL. Static manuals are not automatically current news.
- The official company site is a source for public contact and service offerings, but never an independent source about protocol security.
