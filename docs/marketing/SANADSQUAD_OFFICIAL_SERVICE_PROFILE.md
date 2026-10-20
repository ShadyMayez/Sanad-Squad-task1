# SanadSquad — Official Company Service Profile & Positioning Guide

**Directive:** `SANADSQUAD_V3_OFFICIAL_BRAND_INTEGRATION_01`  
**Authoritative Source:** Official Website (`https://sanadsquad.com/`)  
**Retrieval Verification Timestamp:** `2026-10-20T15:38:43Z`  
**Purpose:** Canonical company positioning profile establishing exact service definitions, customer pain points, technical problems, deliverables, engagement processes, allowed claims, and strict evidentiary boundaries.

---

## 1. Executive Company Overview & Verified Public Contacts

### Company Positioning
> **Security for Blockchain and AI financial systems.**  
> We review design, implementation, and operational controls for Web3 protocols and AI agents that hold funds.  
> *Sanad: We create a chain of trust for your system.*

### Connective Core Thesis
> **The contract and the agent transacting with it are one system. We review and build across all of it.**  
> Blockchain protocols face constant threats of fund loss, making intensive review crucial. Autonomous AI financial systems operate on blockchains too, yet frequently lack hardened security controls. Traditional security firms audit smart contracts and stop there. SanadSquad pairs manual smart contract auditing with penetration testing, agentic security tooling, agentic payment protocol reviews, and early security consulting.

### Verified Public Business Contacts
Retrieved and verified from `https://sanadsquad.com/contact/`:
- **Company Name:** SanadSquad (also styled as Sanad Squad)
- **Business Inquiries Email:** `frank@sanadsquad.com`
- **Official Contact Form:** `https://sanadsquad.com/contact/`
- **Telegram Channel:** `@castle_chain`
- **X (Twitter) Channel:** `@SanadSquad`
- **Official Website:** `https://sanadsquad.com`
- **Public Telephone Number:** *None listed on website.* (Do not fabricate telephone numbers; `+1-555-0199` is strictly prohibited).
- **Recruitment Contact:** `career@sanadsquad.com` (Identified on `https://sanadsquad.com/careers/growth-bd-lead/`; strictly reserved for careers/hiring and barred from commercial inquiries).

---

## 2. Service 1: Blockchain Security Audits

### 2.1 Metadata
- **Exact Official Name:** Blockchain security audits
- **Official Source URL:** `https://sanadsquad.com/services/blockchain-security-audits/`
- **Canonical Research Taxonomy:** `web3-security`
- **SHA-256 Checksum:** `e50a6d79fec45ab238abed72b7e1bf1a97bd1800ef37a169adbc57f06e612721`

### 2.2 Supported Capabilities & Scope
- **Chains Supported:** All EVM chains (Ethereum, Arbitrum, Polygon, Avalanche, BNB Chain, Monad) and Non-EVM chains (Solana/SVM, Sui).
- **Review Methodology:** Manual, line-by-line review of smart contract code by Senior Auditors, supported by internal AI detectors.
- **Specific Vulnerability Classes Reviewed:**
  1. *Broken Invariants:* Stated protocol invariants and state transition assumptions tested for violations.
  2. *Accounting and Rounding:* Rounding that favors the caller, fee application on the wrong side of division, share inflation on empty vaults.
  3. *Access Control and Privilege:* Role escalation, uninitialized/callable initializers, upgrade paths granting unintended admin authority.
  4. *Oracle and Price Manipulation:* Spot price manipulation within a single transaction, stale price feeds lacking freshness bounds.
  5. *Cross-Contract and Reentrancy:* Re-executing operations before completion, read-only reentrancy, cross-chain compatibility.
  6. *Economic and Incentive Design:* Individually correct flows that are jointly exploitable (donation attacks, first-depositor advantage).
- **Optional/Premium Capabilities:** Specialized fuzzing suite development and formal verification (available where the engagement calls for it).
- **Mitigation & Post-Audit Support:** Verification of client patches to confirm original issues are resolved without introducing regressions; continuous support channel remaining open for questions before deployment.

### 2.3 Intended Customers & Pain Points
- **Target Customers:** Protocol founders, DeFi architects, foundation leads, and smart contract engineers on EVM, Solana/SVM, and Sui.
- **Customer Pain Points:** Fear of post-deployment exploit or total value locked (TVL) drainage; anxiety over subtle rounding bugs or economic manipulation; lack of certainty that audited commits match deployed bytecode.
- **Relevant Technical Problems:** Post-audit state drift, reentrancy via external callbacks, pool price manipulation during liquidations, SVM account confusion.

### 2.4 Applicable Deliverables
- Fixed-price audit report detailing findings with reproducible steps and recommended remediations.
- Mitigation review report confirming patch effectiveness.
- Optional fuzzing suite and formal verification specification report.

### 2.5 Engagement Process (6 Stages)
1. **Scoping:** Reading codebase, architecture, documentation, and previous reports before quoting fixed price, duration, and researcher staffing.
2. **Pre-audit:** Critical path first pass using AI detectors to surface obvious defects before deep manual review.
3. **Security Audit:** Line-by-line manual review testing protocol invariants, fund loss paths, fraud, and DoS.
4. **Fuzzing & Formal Verification (Premium):** Building invariant fuzzing suites and formal specifications where engaged.
5. **Mitigation Review:** Reviewing developer fixes to verify issues are solved without collateral side-effects.
6. **Continuous Support:** Dedicated communication channel remaining open after delivery for deployment questions.

### 2.6 Suitable Marketing Angles
- Why manual invariant review catches flaws that static linters miss.
- How share inflation attacks drain empty ERC-4626 vaults and how invariant assertions prevent them.
- Solana/SVM account ownership verification vs EVM caller semantics.

### 2.7 Claims Matrix
- **Allowed Company Positioning Claims:**
  * "SanadSquad conducts manual, line-by-line smart contract audits across EVM and non-EVM chains including Solana and Sui."
  * "SanadSquad checks protocol invariants, accounting mechanics, and access controls."
  * "SanadSquad offers mitigation reviews and optional invariant fuzzing and formal verification."
- **Claims Requiring Additional Verification / Approval:**
  * Citing specific audit counts or researcher experience metrics (e.g. "60+ audits", "300+ criticals") in marketing posts.
- **Claims That Must Never Be Made:**
  * Claiming that every engagement automatically includes premium formal verification.
  * Guaranteeing 100% bug-free contracts or zero-risk deployments.
  * Claiming third-party breaches (e.g. Bybit/Safe) as SanadSquad audit clients.

---

## 3. Service 2: Penetration Testing

### 3.1 Metadata
- **Exact Official Name:** Penetration testing
- **Official Source URL:** `https://sanadsquad.com/services/penetration-testing/`
- **Canonical Research Taxonomy:** `pentesting`
- **SHA-256 Checksum:** `43129d7dafabdd4cef482e6ca4aa1f550b724f4b2c8c831c6320016550065793`

### 3.2 Supported Capabilities & Scope
- **Target Systems:**
  1. *Web and mobile applications:* Frontend interfaces, user session handling, phishing surface, denial of service (DoS), broken authorization.
  2. *APIs:* Broken Object Level Authorization (BOLA), Broken Function Level Authorization (BFLA), rate limiting, data exfiltration.
  3. *Blockchain infrastructure:* Node and validator setups, RPC endpoints, SDKs, Layer 1 network components.
  4. *Web3 off-chain components:* Wallets, bridge SDKs, Key Management Services (KMS), CI/CD build pipelines.
- **Methodology:** Simulated real-world adversary attacks mapping entry points, automated/AI-assisted scanning, and manual exploitation.

### 3.3 Intended Customers & Pain Points
- **Target Customers:** Web3 dApp developers, exchange operators, validator clusters, and fintech infrastructure engineering leads.
- **Customer Pain Points:** Recognizing that smart contract audits do not protect against frontend DNS hijacking, malicious npm dependencies, or API key compromise; exposure of private validator keys via unhardened RPCs.
- **Relevant Technical Problems:** BOLA in withdrawal APIs, CI/CD pipeline dependency poisoning, malicious calldata injection in transaction signers.

### 3.4 Applicable Deliverables
- Comprehensive penetration testing report with vulnerability severity ratings, reproduction proof-of-concepts, and remediation blueprints.
- Retest report after mitigations are deployed.

### 3.5 Engagement Process (4 Stages)
1. **Scoping:** Codebase, architecture, and docs review to confirm scope boundaries, duration, and researcher allocation.
2. **Scanning and Discovery:** Automated and AI-assisted mapping of every flow, entry point, and dependency flaw.
3. **Exploitation:** Simulated real-world adversary attacks targeting DoS, broken authorization, and exfiltration.
4. **Mitigation and Ongoing Support:** Reviewing developer patches to verify fixes do not open new attack surfaces.

### 3.6 Suitable Marketing Angles
- Why an audited smart contract remains vulnerable if the frontend API or signer pipeline has authorization flaws.
- Supply chain integrity in Web3 build environments: CI/CD pipeline risks.
- Off-chain signing boundaries and KMS exposure.

### 3.7 Claims Matrix
- **Allowed Company Positioning Claims:**
  * "SanadSquad performs penetration testing on web apps, APIs, blockchain infrastructure, SDKs, and off-chain components."
  * "SanadSquad simulates real-world adversary attacks against authorization and data flows."
- **Claims Requiring Additional Verification / Approval:**
  * Specific customer infrastructure breach simulations or undisclosed client pen-test statistics.
- **Claims That Must Never Be Made:**
  * Claiming SanadSquad offers every general enterprise IT/cloud consulting service beyond published dApp/infrastructure scope.
  * Stating that penetration testing replaces smart contract auditing.

---

## 4. Service 3: Agentic Security Tooling

### 4.1 Metadata
- **Exact Official Name:** Agentic security tooling (Website H1: Agentic tooling)
- **Official Source URL:** `https://sanadsquad.com/services/ai-security-tooling/`
- **Canonical Research Taxonomy:** `agentic-security`
- **SHA-256 Checksum:** `987804573e8ae366408ee5e8402ca1b74c762b7a6b7eae92699263ba88b459e0`

### 4.2 Supported Capabilities & Scope
- **Core Offering:** Building custom AI security software tailored to a client protocol's codebase and architecture:
  1. *Protocol-Specific Detectors:* Custom AI detector agents trained on protocol architecture to catch vulnerabilities during development as soon as code is committed.
  2. *Automated Pull-Request Reviewers:* Automated PR reviewers evaluating whether proposed code changes violate established invariants or introduce regressions.
  3. *Cloud Monitoring Agents:* Cloud-based transaction monitoring agents observing live smart contract activity to detect anomalies and raise alerts before funds can be drained.
- **Maintenance:** Three months of included ongoing maintenance, cloud provider adaptations, and configuration support.

### 4.3 Intended Customers & Pain Points
- **Target Customers:** Protocol engineering teams, continuous integration maintainers, and security leads managing rapid release cycles.
- **Customer Pain Points:** Developer velocity introducing regressions between formal audits; manual code reviews failing to catch subtle invariant violations; inability to monitor live transactions around the clock.
- **Relevant Technical Problems:** Post-audit pull request drift, delayed breach notification, protocol-specific business logic bugs invisible to generic linters.

### 4.4 Applicable Deliverables
- Deployed, operational custom security detector, PR review bot, or cloud transaction monitoring agent.
- Architecture and schema documentation.
- 3 months of operational maintenance and configuration support.

### 4.5 Engagement Process (6 Stages)
1. **Scoping:** Agreeing on tool specifications, input sources, output formats, timeline, and engineering team.
2. **Architecture Design:** Schemas, workflows, and system design before coding begins.
3. **Prototype:** First working model validated against the client's codebase.
4. **Development:** Full code construction and testing across deployment environments.
5. **Deployment:** Production deployment on client infrastructure against live conditions.
6. **Maintenance (3 months):** Post-delivery configuration support and cloud adjustments.

### 4.6 Suitable Marketing Angles
- Why generic linters miss protocol-specific invariant violations and how tailored PR reviewers catch them early.
- Moving security detection from annual audit milestones into every pull request.
- Transaction monitoring agents vs reactive post-mortem discovery.

### 4.7 Claims Matrix
- **Allowed Company Positioning Claims:**
  * "SanadSquad builds custom AI security tools, including protocol-specific detectors, PR reviewers, and monitoring agents."
  * "SanadSquad provides end-to-end tooling from architecture design to production deployment with 3 months maintenance."
- **Claims Requiring Additional Verification / Approval:**
  * Presenting experimental prototypes or illustrative detector benchmarks as production client deployments.
- **Claims That Must Never Be Made:**
  * Limiting this offering merely to "AI red teaming" (it is a software development and tooling service).
  * Claiming automated tools replace human security audits.

---

## 5. Service 4: Agentic Payments

### 5.1 Metadata
- **Exact Official Name:** Agentic payments
- **Official Source URL:** `https://sanadsquad.com/services/agentic-payments/`
- **Canonical Research Taxonomy:** `agentic-payments`
- **SHA-256 Checksum:** `df543f4f72c745d4785a39cb8952bf7b7cc68e1fb9a6f88b0ab986ccc6c42b1f`

### 5.2 Supported Capabilities & Scope
- **Core Offering:** Building and securing autonomous AI agents that accept and execute micro-payments over modern agent payment rails:
  1. *Payment Rail Implementations:* Supporting both **x402** and **MPP** (Machine Payments Protocol / Tempo).
  2. *MCP Server Development & Review:* Developing and evaluating Model Context Protocol (MCP) servers exposed by agents, testing resistance to load and adversarial attacks.
  3. *Facilitator Layer Integration:* Verifying correct connection between AI agents and off-chain payment facilitators, validating on-chain state synchronization, and request mapping.
  4. *Authorization & Prompt Injection Defense:* Testing whether prompt injection can coerce an agent into signing unintended messages, paying for unrequested tools, or accessing unauthorized URLs; preventing replay attacks and fake requests.
  5. *Agent Launch Support:* Testing agents under production adversarial conditions and verifying behavior matches test boundaries.

### 5.3 Intended Customers & Pain Points
- **Target Customers:** AI agent developers, micro-service providers, autonomous payment rail architects, and agentic commerce platforms.
- **Customer Pain Points:** Malicious tool instructions tricking buyer agents into draining budgets; replay attacks duplicating payments; facilitator desynchronization causing funds to lock; unvalidated MCP servers collapsing under malicious requests.
- **Relevant Technical Problems:** Prompt injection reaching wallet signing tools; confusion between HTTP 402 transport headers and facilitator settlement; session hijacking in agentic payments.

### 5.4 Applicable Deliverables
- Hardened agent code and MCP server deployment.
- Security review report assessing injection vectors, authorization boundaries, and facilitator reliability.
- Production launch verification and ongoing advisory support.

### 5.5 Engagement Process (5 Stages)
1. **Scoping:** Defining what the payment agent must do, what it must never do, scope boundaries, and timeline.
2. **Development:** Architecture design, prototyping, and core agent construction.
3. **Security Review:** Adversarial testing against prompt injection, unauthorized tool calls, and budget draining.
4. **Launch:** Live production rollout confirming real-world behavior aligns with security testing.
5. **Follow-up:** Dedicated ongoing support for edge cases and unexpected behaviors.

### 5.6 Suitable Marketing Angles
- Why prompt injection in payment agents is a financial hazard, not just a chatbot glitch.
- The technical distinction between HTTP 402 status signaling and off-chain facilitator verification and settlement.
- Hard wallet spending caps and cryptographic tool authorization outside model context.

### 5.7 Claims Matrix
- **Allowed Company Positioning Claims:**
  * "SanadSquad builds and secures AI payment agents supporting x402 and MPP."
  * "SanadSquad reviews MCP servers, facilitator integration, payment authorization, and prompt injection defenses."
- **Claims Requiring Additional Verification / Approval:**
  * Comparative transaction throughput or volume statistics between x402 and MPP (must cite external primary sources like x402.org or mpp.dev).
- **Claims That Must Never Be Made:**
  * Claiming HTTP 402 itself settles funds on-chain (HTTP 402 is an RFC transport signal; facilitators handle verification and settlement).
  * Promising complete immunity to prompt injection without architectural controls.

---

## 6. Service 5: Security Consulting

### 6.1 Metadata
- **Exact Official Name:** Security consulting
- **Official Source URL:** `https://sanadsquad.com/services/consulting/`
- **Canonical Research Taxonomy:** Cross-cutting (`web3-security`, `pentesting`, `agentic-security`)
- **SHA-256 Checksum:** `ef1959d398953cd800d1338b604549f10d8e5f19c2422454689f8b193d8ceee7`

### 6.2 Supported Capabilities & Scope
- **Core Offering:** Advisory and architectural security guidance before, during, and after code development:
  1. *Early Design Review:* Reviewing system design choices before code is written, validating design against project scope and security requirements, and recommending architectural improvements.
  2. *Architecture Implementation:* Structuring program schemas, defining data flow models, and establishing security checks and invariants that must be in place prior to implementation.
  3. *Continuous Development Review:* Iterative review of written code against the target architecture, catching implementation errors and fixing vulnerabilities early.
  4. *Report Delivery & Follow-up:* Comprehensive final report covering design, implementation, and review phases, followed by continuous advisory access.

### 6.3 Intended Customers & Pain Points
- **Target Customers:** Early-stage protocol founders, technical architects launching new blockchains or agent networks, and engineering leads designing novel financial primitives.
- **Customer Pain Points:** Starting code development with flawed security assumptions that are expensive to refactor after audits; lack of senior security architects on the founding team; discovering fundamental architecture flaws right before mainnet launch.
- **Relevant Technical Problems:** Premature commitment to insecure state machines, unworkable upgrade architectures, flawed tokenomic incentive models, and unsafe key management designs.

### 6.4 Applicable Deliverables
- Architectural security specification and schema review.
- Pre-implementation threat model and design recommendations.
- Final comprehensive consulting report covering design, implementation, and review stages.
- Open continuous consultation channel for follow-up questions.

### 6.5 Engagement Process (4 Stages)
1. **Scoping:** Determining required architectural tasks, splitting milestones, estimating timelines, and providing fixed quote.
2. **Implementation:** Working alongside client engineers to implement protocol architecture and review design choices.
3. **Report Delivery:** Final deliverable documenting the design review, implementation review, and open considerations.
4. **Follow Up:** Consultation channel remains open for subsequent architecture queries and deployment guidance.

### 6.6 Suitable Marketing Angles
- Why fixing architectural design flaws before writing code costs a fraction of refactoring after a failed audit.
- Designing protocols to be secure by default.
- Continuous development reviews vs stressful end-of-cycle audit discoveries.

### 6.7 Claims Matrix
- **Allowed Company Positioning Claims:**
  * "SanadSquad provides security consulting from early architecture design review before code is written to ongoing implementation review."
  * "SanadSquad works alongside client engineering teams to build secure-by-default protocols."
- **Claims Requiring Additional Verification / Approval:**
  * Specific consulting client advisories or unverified partnership claims.
- **Claims That Must Never Be Made:**
  * Subsuming consulting into standard audits (it is an independent architectural offering).
  * Guaranteeing that consulting eliminates all subsequent audit findings.

---

## 7. Audit History and Private Engagement Data Policy

### Authoritative Rule
The official website showcases high-level researcher experience numbers on its homepage founders section (e.g. 0xFrankCastle: Rust/Solana; Al-Qa'qa': EVM). However:
1. **`audits.json` Remains Empty:** Detailed historical audit client lists, private engagement reports, and proprietary vulnerability registers are strictly confidential.
2. **Zero Third-Party Fabrication:** Never manufacture audit entries in `audits.json` or populate it from third-party repositories (such as Accretion or external bug bounties).
3. **Explicit Marketing Approval Gate:** High-level metrics displayed on the website (e.g. audit counts, severity numbers, client counts) may **NOT** be automatically incorporated into marketing posts without explicit marketing authorization.
4. **Client Confidentiality Invariant:** SanadSquad maintains rigorous confidentiality across all private security reviews and consultations.
