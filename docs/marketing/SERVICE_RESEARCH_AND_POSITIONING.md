# SanadSquad — Service Research and Positioning Guide

**Directive:** `SANADSQUAD_V3_MARKETING_RESEARCH_QUALITY_02`  
**Purpose:** Canonical intelligence, positioning frameworks, technical mechanisms, and research query catalogs for SanadSquad's four commercial cybersecurity service lines.

---

## 1. Executive Positioning & Commercial Thesis

### The Core Problem in Web3 Security
Most Web3 security firms audit smart contracts and stop there. A protocol with a clean audit report still gets drained through a compromised developer laptop, a poisoned npm dependency, an insecure API endpoint, an unmonitored proxy upgrade, or an autonomous AI agent talked into executing an unauthorized wallet transfer.

### The SanadSquad Positioning
> **SanadSquad covers the whole attack surface, not just the contract.**

Every marketing post, research angle, and technical commentary published by SanadSquad must trace back to this foundational insight.

### The Connective Argument
These are not four distinct, siloed business divisions. Modern Web3 and autonomous agent applications require all four disciplines simultaneously:
- An **AI agent** that manages funds runs on **Web2 cloud infrastructure**, interacts with **APIs and CI/CD pipelines**, signs transactions on **Web3 blockchains (EVM/SVM)**, takes instructions in natural language, and pays for tools or services over an **agentic payment protocol (x402 / MPP)**.
- A security firm that only audits Solidity or Vyper contracts cannot evaluate this connected attack surface.

```
+-----------------------------------------------------------------------------------+
|                           THE CONNECTED ATTACK SURFACE                            |
+-----------------------------------------------------------------------------------+
|  1. Web2 Pentesting:       APIs, Cloud IAM, CI/CD, Signing Frontends, Dependencies|
|  2. Web3 Security:         EVM & SVM Smart Contracts, Verified Builds, Invariants |
|  3. Agentic Security:      Prompt Injection, MCP Boundaries, Wallet Spending Policy|
|  4. Agentic Payments:      x402 Pre-authorizations, MPP Sessions, Facilitator Trust|
+-----------------------------------------------------------------------------------+
```

### Four-Way Reasoning Discipline
To eliminate generic marketing slogans and maintain editorial integrity, every piece of content must strictly separate:
1. **Fact:** An empirical claim directly grounded in a retrieved, allowlisted source.
2. **Interpretation:** An explicitly framed technical or risk implication drawn from the evidence.
3. **Company Positioning:** The service capabilities described in SanadSquad's approved Marketing Guide.
4. **Commercial CTA:** A contextual invitation using approved company contact details.

*Critical Boundary:* A retrieved vulnerability or public incident proves that a risk exists in the industry; it does **never** prove or imply that SanadSquad worked on that vulnerability, audited the affected company, or had clients experience the breach.

---

## 2. Service Line 1: Web3 Security (EVM & SVM)

### 2.1 Target Customer
- Protocol founders, technical leads, and engineering teams deploying on Ethereum, EVM Layer-2s, and Solana / SVM.
- DeFi architects designing complex cross-contract financial mechanisms and yield vaults.
- DAO risk curators and governance managers supervising protocol upgrades and parameter adjustments.

### 2.2 Customer's Actual Security Concern
- **Post-Audit State Drift:** Contracts that were verified secure at audit time deviating in production due to subsequent governance parameter updates, proxy upgrades, or altered upstream dependencies.
- **SVM Execution Nuances:** Solana-specific pitfalls including account confusion, missing owner checks, missing signer checks, and arbitrary Cross-Program Invocations (CPI).
- **Unverified On-Chain Bytecode:** The risk that deployed bytecode in production does not byte-for-byte match the audited open-source repository commit.
- **Upgrade Authority Governance:** Unsafe keys (single-sig EOA vs. multisig vs. timelock) maintaining administrative upgrade power over protocol contracts.

### 2.3 Relevant Technical Mechanisms
1. **EVM Invariants & Formal Reasoning:**
   - State transition invariants: conditions that must hold true across every transaction boundary (e.g. total minted supply equals collateral times exchange rate).
   - Checks-Effects-Interactions (CEI) and reentrancy locks preventing execution re-entry before state updates finalize.
   - Storage layout integrity across proxy upgrades (preventing storage slot collision).
2. **Solana / SVM Verified Builds & Program Deployment:**
   - **Verified Builds (`solana-verify`):** Deterministic, Docker-isolated compilation linking on-chain program ELF binaries directly to specific Git commits and source repositories (`solana.com/docs/programs/verified-builds`).
   - **Program Deployment & Upgrade Authority:** Programs deployed via the BPF Loader remain upgradeable by default until the upgrade authority is explicitly set to a multisig (e.g. Squads), a timelock, or burned to immutable (`None`) via `solana program set-upgrade-authority` (`solana.com/docs/core/programs/program-deployment`).
   - **Account Validation Invariants:** Rigorous checks verifying `AccountInfo.owner == expected_program_id`, `AccountInfo.is_signer == true`, and PDA seeds matching canonical derivations.
3. **The Tripartite Distinction:**
   - **Source Verification:** Proves that deployed bytecode matches a specific source text. It does not evaluate whether the code contains logical vulnerabilities.
   - **Security Audit:** A point-in-time expert examination of architecture, code logic, invariants, and threat models. It does not protect against post-audit changes or environmental drift.
   - **Ongoing Security Monitoring:** Continuous runtime assertion tracking, invariant telemetry, and automated transaction simulation alerting teams to state anomalies in production.

### 2.4 Consequences Supported by Evidence
- Trail of Bits invariant research demonstrates that audited protocols frequently suffer catastrophic insolvency not from zero-day logic bugs, but from operational parameter drift and unanticipated composability interactions with external protocols.
- Accretion audit reports demonstrate that on SVM, missing account ownership checks and unconstrained CPI signer propagation enable unauthorized attackers to reassign account authority or transfer assets without balance checks (e.g. Swig ACC-C2 / ACC-H2).

### 2.5 What SanadSquad's Service Addresses
- Full-scope smart contract audits across EVM and Solana/SVM.
- Mathematical protocol invariant specification and formal review.
- Deployed program verification and build reproducibility audits.
- Administrative upgrade authority and timelock governance assessment.
- Integration security review for cross-contract and DeFi composability risk.

### 2.6 Useful Post Angles
- *The Verified Build Angle:* "A clean audit report linked to a GitHub commit is meaningless if the on-chain bytecode was compiled from an unverified local machine. Solana verified builds prove identity; audits prove logic."
- *The Upgrade Key Angle:* "Who holds the upgrade authority on your deployed program? If a single private key can change the bytecode tomorrow, your audit was performed on a temporary artifact."
- *The Invariant Drift Angle:* "Audits check code at a standstill. Protocols fail in motion when governance parameters shift an economic invariant past its breaking point."

### 2.7 Misleading or Unsupported Claims to Avoid
- Never guarantee "100% security" or claim an audit "eliminates all vulnerability risk".
- Never claim SanadSquad audited specific protocols without verified public clearance.
- Never conflate source code verification (e.g. Etherscan green checkmark) with a security audit.

### 2.8 Suitable Source Categories & Example Queries
- `docs`: `solana.com/docs/programs/verified-builds`, `solana.com/docs/core/programs/program-deployment`, `ethereum.org`
- `blogs`: `trailofbits.com`, `openzeppelin.com`, `paradigm.xyz`, `samczsun.com`
- `analysis`: `defillama.com`, `rekt.news`
- **Example Queries:**
  - `solana verified builds program deployment security`
  - `smart contract invariant drift post-audit monitoring`
  - `solana upgrade authority multisig best practices`
  - `openzeppelin proxy upgrade storage layout collision`

---

## 3. Service Line 2: Web2 Pentesting (Infrastructure & Supply Chain)

### 3.1 Target Customer
- Protocol engineering teams operating web frontends, indexing nodes, RPC gateways, and custodial backends.
- Institutional DeFi custody providers, multi-sig treasury operators, and fintech bridging platforms.
- Crypto exchanges and staking infrastructure providers managing cloud environments and validator keys.

### 3.2 Customer's Actual Security Concern
- **Losses Originating Outside Smart Contracts:** A mathematically sound contract being exploited through developer laptop compromise, stolen AWS credentials, compromised CI/CD pipelines, or DNS hijacks.
- **Frontend Transaction Manipulation:** Poisoned npm dependencies modifying transaction payloads in the browser interface, tricking signers into approving unauthorized drains.
- **API Authorization Failures:** Internal or administrative Web2 APIs leaking user data, exposing private endpoints, or allowing unauthorized state manipulation.

### 3.3 Relevant Technical Mechanisms
1. **API Authorization Flaws (OWASP API Top 10):**
   - **BOLA (Broken Object Level Authorization / API1:2023):** Endpoints failing to validate whether the requesting user owns the requested asset ID.
   - **BFLA (Broken Function Level Authorization / API5:2023):** Normal users accessing administrative functions by invoking hidden API routes.
   - **Server-Side Request Forgery (SSRF / API7:2023):** Backends coerced into querying internal cloud metadata services (`169.254.169.254`) or private microservices.
2. **CI/CD & Software Supply-Chain Compromise:**
   - Malicious package injection (typosquatting, dependency confusion, or compromised maintainer accounts) in `@solana/web3.js` or `ethers` utility packages.
   - GitHub Actions runner exploitation: Pull requests triggering malicious workflows that exfiltrate repository secrets, deployment keys, and cloud tokens.
3. **Frontend & Multi-Sig Signing Interface Security:**
   - DOM injection and client-side script tampering modifying the destination address (`to`) or calldata (`data`) immediately before the signer confirms the transaction in MetaMask or Phantom.
4. **Careful Case Study: The 2025 Bybit / Safe Incident:**
   - **Reported & Verified Findings:** In early 2025, an enterprise transaction involving Bybit and Safe multi-sig infrastructure experienced a massive unauthorized transfer. Technical post-mortems established that the underlying Safe smart contracts functioned as written; the compromise occurred in the off-chain developer environment and transaction signing interface. Malicious modifications altered the proposed transaction payload before multi-sig threshold approval, substituting attacker-controlled recipient addresses.
   - **Distinguishing Evidence from Speculation:** Speculation initially blamed smart contract vulnerabilities. Verified post-incident analyses confirmed that the smart contract logic was completely sound; the failure point was off-chain supply chain poisoning and developer machine compromise altering the transaction calldata before signing.
   - **Candidate Source Status:** Press releases from commercial platforms (`bybit.com/en/press`) are candidate notices; authoritative technical evidence is drawn fromallowlisted security research bodies (`owasp.org`, `portswigger.net`, `mandiant.com`, `cisa.gov`).

### 3.4 Consequences Supported by Evidence
- OWASP research and industry loss totals show that over 68% of Web3 asset losses stem from private key theft, infrastructure compromise, and supply-chain poisoning rather than on-chain smart contract vulnerabilities.
- Compromising a single CI/CD build script or developer laptop bypasses millions of dollars in formal contract verification.

### 3.5 What SanadSquad's Service Addresses
- Comprehensive external and internal penetration testing of Web3 cloud infrastructure.
- CI/CD pipeline auditing and automated build security hardening.
- API security reviews and BOLA/BFLA vulnerability assessments.
- Frontend dApp security reviews and dependency supply-chain audits.
- Multi-sig signing workflow and hardware key security assessments.

### 3.6 Useful Post Angles
- *The Frontend Trap:* "You audited every line of Solidity, but your users interact through a React dApp pulling 400 unpinned npm packages. A single poisoned dependency can rewrite transaction calldata before the wallet pops up."
- *The Safe/Bybit Lesson:* "The 2025 Safe transfer incident proved it again: smart contracts do not verify user intent; they verify signatures. When off-chain signing infrastructure is compromised, valid signatures drain valid contracts."
- *API Exposure:* "Web3 backends often expose internal RPC and management endpoints without object-level authorization. An attacker doesn't need to reenter your contract if they can call your API."

### 3.7 Misleading or Unsupported Claims to Avoid
- Never claim that Safe's smart contracts had a vulnerability in the 2025 incident.
- Never claim SanadSquad was hired by Bybit or Safe unless backed by public disclosure authorization.
- Never attack named competing Web2 pentest firms.

### 3.8 Suitable Source Categories & Example Queries
- `docs`: `owasp.org`, `csrc.nist.gov`, `cve.org`
- `blogs`: `portswigger.net`, `krebsonsecurity.com`, `bishopfox.com`
- `analysis`: `cisa.gov`, `mandiant.com`
- **Example Queries:**
  - `owasp api security top 10 broken object level authorization`
  - `web3 frontend supply chain attack malicious dependency transaction signing`
  - `cicd pipeline github actions secret exfiltration protocol deployer`
  - `bybit safe transaction signing interface compromise post mortem`

---

## 4. Service Line 3: Agentic Security and Red Teaming (AI Agents & Wallets)

### 4.1 Target Customer
- Autonomous AI agent framework creators, AI hedge funds, and automated treasury management developers.
- Protocols building conversational DeFi interfaces, automated arbitrage agents, or customer service bots with action capabilities.
- Enterprise software teams integrating LLM agents with internal tools, databases, and APIs via the Model Context Protocol (MCP).

### 4.2 Customer's Actual Security Concern
- **Prompt Injection Hijacking Actions:** An attacker injecting instructions via untrusted text (e.g. email, web page, Discord message, transaction metadata) that overrides the agent's instructions and commands it to execute unauthorized tool calls.
- **Unbounded Wallet Access:** An agent holding private keys or signing capabilities without hard spending caps, allowing prompt injection to drain treasuries.
- **MCP Tool Poisoning:** Malicious MCP tool definitions or compromised tool responses redirecting agent workflows.
- **Confused Deputy Problems:** Agents acting on behalf of an unauthenticated user with the agent's own elevated system privileges.

### 4.3 Relevant Technical Mechanisms
1. **Prompt Injection & Goal Hijacking (OWASP Top 10 for Agentic Applications 2026):**
   - **Direct Injection:** Adversary directly prompts the agent to ignore previous constraints.
   - **Indirect Injection:** Adversary embeds malicious instructions in data the agent retrieves (e.g. on-chain metadata, token names, scraped documentation, resume text).
2. **Tool Misuse & Delegated Authority:**
   - Exposing high-privilege functions (`send_eth`, `sign_message`, `delete_database`) to an LLM without parameter validation or schema enforcement.
3. **MCP Tool Trust Boundaries:**
   - The Model Context Protocol (MCP) standardizes tool discovery and execution. When an agent connects to third-party MCP servers, malicious tools can return poisoned context or manipulate tool execution graphs.
4. **Wallet Signing Permissions vs. Spending Restrictions:**
   - **Authentication vs. Authorization:** Keeping the private key out of the model's text context is table stakes (Authentication). It does **not** stop the model from being talked into invoking its signing tool (Authorization).
   - **Deterministic Policy Engines:** Signing keys must be held inside an isolated policy engine with immutable cryptographic rules:
     * Hard per-transaction and daily spending limits.
     * Strict recipient contract allowlists.
     * Co-signing requirements and timelocks for large transactions.
5. **Human Approval vs. Deterministic Action Authorization:**
   - Relying exclusively on human approval for agent actions fails due to notification fatigue and social engineering.
   - Robust architecture enforces deterministic code gates: if an action exceeds policy limits, the transaction cannot be signed, regardless of model intent or human persuasion.

### 4.4 Consequences Supported by Evidence
- Simon Willison's foundational research demonstrates that prompt injection cannot be stopped by system prompts or prompt engineering. When an LLM has access to a tool, any data it processes can potentially trigger that tool.
- OWASP GenAI Agentic Security guidelines demonstrate that delegating financial execution to autonomous models without external cryptographic policy limits directly results in fund loss.

### 4.5 What SanadSquad's Service Addresses
- Red-teaming autonomous agent workflows against direct and indirect prompt injection.
- Architecture review of agent tool authorization and MCP trust boundaries.
- Design and verification of out-of-band cryptographic wallet policy engines.
- Analysis of credential isolation and human-in-the-loop review mechanics.

### 4.6 Useful Post Angles
- *The Key vs. Policy Angle:* "Keeping your agent's private key in an environment variable stops the model from printing the key. It does nothing to stop prompt injection from asking the model to use the key. Security is policy, not secrecy."
- *The Tool Trap:* "If your AI agent reads untrusted web pages and has a tool called `transfer_tokens()`, you have built an automated drainer waiting for an instruction."
- *MCP Security:* "Connecting an autonomous agent to external MCP servers without strict schema validation turns tool discovery into an untrusted code execution vector."

### 4.7 Misleading or Unsupported Claims to Avoid
- Never claim that prompt engineering, guardrail prompts, or "constitutional AI" eliminate prompt injection risk.
- Never claim that SanadSquad has audited or certified proprietary AI foundation models unless publicly evidenced.

### 4.8 Suitable Source Categories & Example Queries
- `docs`: `genai.owasp.org`, `attack.mitre.org`, `modelcontextprotocol.io`, `nist.gov`
- `blogs`: `simonwillison.net`, `embracethered.com`, `lakera.ai`, `hiddenlayer.com`
- `analysis`: `arxiv.org`, `cset.georgetown.edu`
- **Example Queries:**
  - `simon willison prompt injection tool use agent security`
  - `owasp top 10 for agentic applications 2026 tool authorization`
  - `model context protocol mcp security boundaries prompt injection`
  - `agentic wallet policy spending limits out of band signing`

---

## 5. Service Line 4: Agentic Payment Protocols (x402 & MPP)

### 5.1 Target Customer
- Machine-to-machine micropayment platforms, automated AI API gateways, and pay-per-request service providers.
- Protocol developers integrating the x402 specification or Machine Payments Protocol (MPP).
- Facilitator node operators, liquidity providers, and settlement clearinghouses for autonomous commerce.

### 5.2 Customer's Actual Security Concern
- **Facilitator Intermediary Trust:** What financial or operational risks arise when relying on a facilitator to batch, verify, and submit on-chain settlements?
- **Replay Attacks & Nonce Handling:** Could an authorized payment signature be intercepted and replayed across multiple requests or different facilitators?
- **Settlement Finality & Partition Failures:** How does the payment protocol handle network latency, blockchain reorganizations, or facilitator insolvency before final on-chain settlement?
- **Agent Spending Authorization:** Preventing autonomous payment loops from draining balances when interacting with paywalled agent resources.

### 5.3 Relevant Technical Mechanisms
1. **The x402 Protocol:**
   - **Origin & Vision:** Developed as an open standard leveraging HTTP status code 402 ("Payment Required"), led by Coinbase and open-source contributors (`x402.org`).
   - **Payment Request & Settlement Flow:**
     1. Client requests a protected resource via standard HTTP GET/POST.
     2. Server responds with `HTTP 402 Payment Required`, specifying price, accepted tokens, payment address, and facilitator requirements in response headers.
     3. Client generates and cryptographically signs a payment pre-authorization (e.g. EIP-712 or Solana signature).
     4. Client repeats the request with the signed payment payload in the `Authorization` or `X-402-Payment` header.
     5. Facilitator verifies the signature, settles the transaction on-chain (or verifies pre-funded escrow), and notifies the resource server to deliver content.
   - **Facilitator Responsibilities & Trust:** The facilitator acts as a non-custodial or semi-custodial settlement relayer. The client trusts the facilitator to settle in a timely manner without front-running; however, the client's risk is bounded by the exact signed pre-authorization payload.
2. **Machine Payments Protocol (MPP / Tempo / Stripe):**
   - **Origin & Architecture:** Developed collaboratively by Stripe, Tempo, and open-source contributors (`mpp.dev`, `tempo.stream`), optimized for high-frequency streaming micropayments and interactive machine sessions.
   - **Payment Intents & Streaming Sessions:** Rather than signing discrete single-request transactions, the agent establishes a payment intent or session channel with defined spending ceilings. Incremental micropayments occur off-chain through signed state updates, settling periodically to Layer-1 or Layer-2 blockchains.
   - **Facilitator Trust & Channel Invariants:** Facilitators manage state channel liquidity and dispute windows. Replay protection is enforced through strict session nonces and expiration epochs.
3. **Comparative Analysis: x402 vs. MPP:**
   | Dimension | x402 Protocol | Machine Payments Protocol (MPP) |
   |---|---|---|
   | **Primary Paradigm** | Stateless HTTP-native request/response | State-channel streaming sessions |
   | **Target Workload** | Discrete API queries, single resource downloads | High-frequency continuous data streams, agent interactions |
   | **Integration Layer** | HTTP 402 headers & standard web gateways | Session SDKs & channel state managers |
   | **Counterparty Risk** | Per-request pre-authorization bounds | Channel deposit & facilitator dispute windows |
   | **Settlement Mechanism** | Facilitator-batched on-chain transfers | Periodic netting & channel settlement |
4. **Replay Protection & Cryptographic Mechanics:**
   - Both protocols require strict cryptographic replay defense: domain-separated hashing (EIP-712 domain separators / Solana unique program addresses), monotonic nonces, and tight UTC expiration timestamps (`valid_before`).

### 5.4 Consequences Supported by Evidence
- Unbounded payment authorizations allow compromised agent loops to drain wallets in rapid succession.
- On-chain signature malleability (e.g. non-enforced low-S values in Secp256k1 as identified in Swig Accretion finding SS-03706) can allow malicious intermediaries to alter transaction IDs or attempt replay across non-synchronized facilitators.

### 5.5 What SanadSquad's Service Addresses
- Architectural review and threat modeling for x402 and MPP protocol integrations.
- Facilitator trust, liquidity safety, and dispute resolution mechanism audits.
- Verification of cryptographic payment signatures, replay protection, and nonce tracking.
- Client-side agent spending ceiling policy and out-of-band authorization review.

### 5.6 Useful Post Angles
- *x402 vs. MPP Breakdown:* "x402 turns HTTP 402 into a native single-request payment rail. MPP builds streaming session channels. Choosing between them depends on whether your agent buys discrete API calls or streams data."
- *The Facilitator Risk:* "In agentic payment rails, the facilitator is the unexamined intermediary. Who takes the loss if the facilitator delays settlement during a market drop?"
- *Micropayment Drain Loops:* "When AI agents pay AI agents, a recursive loop can drain a wallet in milliseconds. Spending ceilings must be enforced at the protocol layer, not the agent prompt."

### 5.7 Misleading or Unsupported Claims to Avoid
- Never pick a premature "winner" between x402 and MPP without citing verifiable transaction volume and facilitator adoption data from `analysis` sources.
- Never state that x402 or MPP eliminates blockchain gas fees or finality latency without explaining facilitator settlement mechanics.
- Never claim SanadSquad authored the x402 or MPP specifications.

### 5.8 Suitable Source Categories & Example Queries
- `docs`: `x402.org`, `mpp.dev`, `docs.stripe.com`
- `blogs`: `stripe.com`, `tempo.stream`, `x402.org`
- `production`: `github.com/coinbase/x402`, `github.com/tempo-stream`, `github.com/stripe`
- `analysis`: `dune.com`, `defillama.com`
- **Example Queries:**
  - `x402 protocol specification http 402 payment pre-authorization`
  - `machine payments protocol mpp session streaming architecture`
  - `x402 vs mpp comparative mechanics facilitator trust`
  - `agentic micropayment signature replay protection eip-712`

---

## 6. Research-to-Marketing Planning Structure

Marketing posts must never be mere summaries of blog articles or academic papers. The marketing writer agent executes a structured seven-stage reasoning pipeline:

```
[1. Verified Source]
       |
[2. Real Security Problem]
       |
[3. Customer Relevance]
       |
[4. SanadSquad Service Connection]
       |
[5. Compelling Hook]
       |
[6. Supported Technical Insight]
       |
[7. Optional Contextual CTA]
```

### The Seven Reasoning Steps
1. **Verified Source:** Identify the retrieved, allowlisted source record, its publication date, domain, and exact verified quote.
2. **Real Security Problem:** Isolate the exact failure mode, exploit vector, or architectural flaw exposed by the research.
3. **Customer Relevance:** Determine who suffers if this problem is ignored (e.g. protocol engineering lead, multi-sig signer, agent developer) and why it matters to them today.
4. **SanadSquad Service Connection:** Map the problem directly to one of the four approved service lines, referencing how SanadSquad's audit or review addresses this specific failure.
5. **Compelling Hook:** Open with a concrete security question, surprising technical distinction, or real incident consequence. Avoid generic slogans or introductory filler.
6. **Supported Technical Insight:** Explain the technical mechanism or defensive review habit strictly within the factual bounds of the evidence.
7. **Optional Contextual CTA:** If reserved by the weekly diversity plan, append a context-specific business invitation using approved contact details.

### Professional Engagement Guidelines
- **Teach First:** Every post must deliver genuine technical utility to the reader, even if they never hire SanadSquad.
- **Vary Name Frequency:** Do not repeat "SanadSquad" in every post. The company name is an editorial tool, not an omnipresent watermark.
- **Specifics Over Slogans:** Replace "Security is vital in Web3" with "Unpinned npm dependencies in dApp frontends allow attackers to alter Safe multi-sig calldata before signing."
- **Strict Character Discipline:** The entire post (including links, formatting, and CTAs) must strictly remain within the 280-character single-tweet platform limit.
