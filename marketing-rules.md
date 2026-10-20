# SanadSquad Marketing Policy & Editorial Guide

Directive: `SANADSQUAD_V3_OFFICIAL_BRAND_INTEGRATION_01`

Rules for every `marketing-post`. Read alongside `brand-voice.md`, which covers tone and banned language. This file covers what we say, where we get it, what formats we use, and our claim boundaries.

Technical threads are not governed by this file.

---

## 1. Positioning

Security for Blockchain and AI financial systems. We review design, implementation, and operational controls for Web3 protocols and AI agents that hold funds.

**The contract and the agent transacting with it are one system. We review and build across all of it.**

### Five Official Commercial Services

| Official Commercial Service | What it covers | Canonical Research Category |
|---|---|---|
| **Blockchain security audits** | Manual, line-by-line review of smart contract systems across EVM, Solana/SVM, Sui, and Monad. Protocol invariants, accounting/rounding, access control, oracle/price manipulation, reentrancy, economic/incentive vulnerabilities. Optional fuzzing/formal verification and continuous mitigation review. | `web3-security` |
| **Penetration testing** | Simulated real-world attacks against web applications, APIs, blockchain infrastructure (validator/node setups, SDKs, Layer 1), and Web3 off-chain components (wallets, bridge SDKs, KMS). | `pentesting` |
| **Agentic security tooling** | Building custom AI security software: protocol-specific security detectors, automated pull-request reviewers, and real-time cloud monitoring agents. | `agentic-security` |
| **Agentic payments** | Building and securing AI payment agents accepting micro-payments on x402 and MPP, MCP server security under load and attack, facilitator layer integration, payment authorization, prompt injection, and replay defense. | `agentic-payments` |
| **Security consulting** | Design review before code is written, building secure-by-default system architecture, security requirements before implementation, ongoing development review, and follow-up support. | Cross-cutting (`web3-security`) |

**The connective argument:** These are not five isolated business divisions. An autonomous financial agent transacting on-chain requires smart contract security, API/infrastructure pentesting, prompt injection defense, and payment rail authorization simultaneously.

---

## 2. Research Sources and Taxonomy Mapping

Every marketing post is grounded in evidence retrieved during the current run. Never write a marketing post from ungrounded memory or static vulnerability catalogs.

`sources.json` (aliased as `source.json`) organizes marketing research into **four canonical research categories**:
1. `web3-security`: Smart contracts, invariant verification, Solana/SVM verified builds.
2. `pentesting`: Web/API infrastructure, CI/CD, dependency poisoning, off-chain components.
3. `agentic-security`: Prompt injection, tool authorization, agent wallets and spending policy.
4. `agentic-payments`: x402 vs MPP mechanics, facilitator trust, payment signaling vs settlement.

The 5 commercial services map directly into these 4 research categories. For example, `security-consulting` draws research from `web3-security` or cross-service allowlists depending on the specific architectural engagement.

---

## 3. Supported Marketing Formats

Single-tweet platform limit ($\le 280$ characters) is mandatory for all `marketing-post` slots.

Across a week, no single format should appear more than twice.

1. **Short tip:** 1 to 3 sentences. One concrete observation or actionable review habit. No link. No preamble.
2. **Differentiation post:** Medium length. Names a gap contract-only firms leave open and shows which SanadSquad service closes it. Grounded in real incidents or figures.
3. **Service overview:** Explains what a service covers and why it matters now.
4. **News reaction:** Recent event plus SanadSquad technical interpretation. Source link is mandatory.
5. **Learning resource:** Highlights an article, documentation page, or roadmap worth reading. Link is mandatory and must resolve. Plainly attributed.

---

## 4. Required Editorial Structure

`Verified security problem → Why a customer should care → Relevant official SanadSquad service → Concrete insight → Optional CTA.`

The marketing writer must produce specific, accurate descriptions of the security concern and the offering that addresses it.

---

## 5. Claims, Confidentiality, and Prohibitions

### Prohibitions
- **No generic marketing claims:** Never write "We secure everything", "We provide the best blockchain security", or "Contact us for all your cybersecurity needs".
- **No unapproved client names:** Do not invent client engagements or associate third-party incidents with SanadSquad.
- **No unsupported company statistics:** Do not publish historical audit counts, severity statistics (e.g., "60+ audits", "300+ criticals", "50+ audits"), or success rates without explicit marketing approval. Keep private engagement data confidential.
- **No wrong-service claims:** Do not claim penetration testing verifies smart contract invariants, or that blockchain audits test cloud IAM.
- **No guarantees of security:** SanadSquad reduces risk; we do not eliminate it. Never claim unhackable, 100% secure, zero risk, or bulletproof.
- **Never attack named competitors:** Critique the limits of contract-only auditing models, never name competitor firms.
- **Third-party findings separation:** Third-party audit reports (such as Accretion findings) must never be presented as SanadSquad work or client stats.

### Calls to Action (CTA)
- Maximum **one CTA across three weekly marketing posts** (and $\le 1/3$ of weekly posts).
- Maximum one CTA per post.
- **Zero CTAs in technical threads.**
- Only publish verified company contact channels from `company-contact.json`:
  * Business email: `frank@sanadsquad.com`
  * Official contact form: `https://sanadsquad.com/contact/`
  * Telegram: `@castle_chain`
  * X: `@SanadSquad`
- Zero invented contact information or phone numbers. The website does not list a public phone number; do not invent one (+1-555-0199 strictly banned).
- Never use recruitment email (`career@sanadsquad.com`) for commercial inquiries.
- If unapproved, fail closed.
- Entire post must remain strictly $\le 280$ characters, including contact details.
- Contact details are company metadata, NOT external research evidence.

---

## 6. Enforceable Policy Rules

```json
{
  "policy_name": "sanadsquad_marketing_rules",
  "version": "2.0.0",
  "max_tweets_per_post": 1,
  "max_chars_per_tweet": 280,
  "service_lines": ["web3-security", "pentesting", "agentic-security", "agentic-payments"],
  "commercial_services": [
    "blockchain-security-audits",
    "penetration-testing",
    "agentic-security-tooling",
    "agentic-payments",
    "security-consulting"
  ],
  "formats": {
    "short-tip": {"requires_link": false, "forbids_link": true, "max_sentences": 3},
    "differentiation": {"requires_link": false, "forbids_link": false},
    "service-overview": {"requires_link": false, "forbids_link": false},
    "news-reaction": {"requires_link": true, "forbids_link": false},
    "learning-resource": {"requires_link": true, "forbids_link": false}
  },
  "weekly_constraints": {
    "max_posts_per_service_line": 1,
    "max_posts_per_format": 2,
    "min_posts_with_link": 1,
    "min_posts_without_link": 1,
    "max_cta_fraction": 0.334,
    "max_weekly_ctas": 1,
    "max_cta_per_post": 1,
    "allow_tech_thread_ctas": false
  },
  "banned_competitor_names": [
    "certik", "open zeppelin", "openzeppelin", "trail of bits", "trailofbits",
    "consensys diligence", "halborn", "spearbit", "code4rena", "sherlock"
  ],
  "prohibited_guarantee_phrases": [
    "guaranteed security", "100% secure", "completely secure", "unhackable",
    "zero risk", "eliminate all risk", "bulletproof"
  ]
}
```

---

## 7. Company Contact Configuration & Validation

All commercial invitations draw from verified channels in `company-contact.json`:

| Field | Requirement | Validation Rule |
|---|---|---|
| `company_name` | "SanadSquad" | Strict string match |
| `business_inquiries_email` | frank@sanadsquad.com | Regex-verified; verified official public email |
| `contact_form_url` | https://sanadsquad.com/contact/ | Official website contact form |
| `telegram` | @castle_chain | Official Telegram channel |
| `x_handle` | @SanadSquad | Official X channel |
| `business_phone_number` | Optional / null | No phone published on website; never invent one |
| `approved` | Explicit approval boolean | If `false`, contact info cannot be published |

### Contextual CTA Generation
Generate natural, context-specific invitations aligned to the service line:
- **Blockchain security audits:** `"Reviewing protocol security? Contact SanadSquad to discuss an audit: frank@sanadsquad.com"`
- **Penetration testing:** `"Assessing infrastructure risks? Request a SanadSquad penetration test: frank@sanadsquad.com"`
- **Agentic security tooling:** `"Building protocol security tools? Consult SanadSquad on custom AI detectors: frank@sanadsquad.com"`
- **Agentic payments:** `"Building a payment agent? SanadSquad reviews authorization and facilitator integrations: frank@sanadsquad.com"`
- **Security consulting:** `"Designing your protocol architecture? Request a security consultation with SanadSquad: frank@sanadsquad.com"`

All separators must use clean ASCII (`|` or `,` or `:`). Never use banned em dashes (`—`) or separator en dashes (`–`).
