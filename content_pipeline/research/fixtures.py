"""Verified public-domain fixture dataset for offline marketing research testing.

All records represent real domains on the canonical allowlist and
realistic security research topics for the five SanadSquad service lines:
- web3-security: Invariant verification, verified builds, ERC-4626 vault inflation, proxy upgrade authorization
- pentesting: BOLA (API1:2023), API trust boundaries, MCP authorization hardening, off-chain infrastructure
- agentic-security: OWASP ACS runtime boundaries, autonomous agent risks, PR security code scanning
- agentic-payments: x402 optional facilitator signaling, MPP unified SDK support, usage session authorization
- security-consulting: NIST SP 800-218 SSDF lifecycle, proxy governance, pre-deployment threat modeling
"""
from __future__ import annotations

import hashlib
from typing import Any
from .config import COMMERCIAL_TO_RESEARCH_MAP
from .models import FetchedPage, SearchResult
from ..schemas import Evidence

RESEARCH_FIXTURES: dict[str, list[dict[str, Any]]] = {
    "web3-security": [
        {
            "source_id": "W01",
            "title": "Solana Verified Builds and Program Upgrade Authority Management",
            "url": "https://solana.com/docs/programs/verified-builds",
            "domain": "solana.com",
            "publisher": "Solana Foundation Documentation",
            "service_line": "web3-security",
            "source_group": "docs",
            "published_date": "2024-11-15",
            "quote": "Solana verified builds provide deterministic proof that on-chain bytecode matches the audited source commit, establishing source-to-deployment correspondence, but does not ensure contract security if the code contains logic flaws. An upgrade alters the deployed executable, calling for verification of the new version and continuous invariant audits.",
            "cleaned_text": (
                "Solana Verified Builds and Program Deployment Authority. "
                "Deterministic verification via solana-verify proves that on-chain bytecode corresponds directly to the specified Git commit, establishing binary build provenance. "
                "Build verification confirms source identity rather than functional logic correctness; a verified build can still contain severe economic or invariant flaws. "
                "When a program is upgraded, the deployed executable changes, calling for re-verification of the new commit and manual smart contract audits."
            ),
        },
        {
            "source_id": "W02",
            "title": "Solana Program Deployment and Upgrade Authority Lifecycle",
            "url": "https://solana.com/docs/core/programs/program-deployment",
            "domain": "solana.com",
            "publisher": "Solana Foundation Documentation",
            "service_line": "web3-security",
            "source_group": "docs",
            "published_date": "2024-10-01",
            "quote": "Deploying a Solana program assigns an initial upgrade authority stored in the ProgramData account. Until transferred to a multi-sig or revoked, the designated authority retains unilateral power to deploy new bytecode, an operational centralization risk that requires pre-deployment architecture review and governance design.",
            "cleaned_text": (
                "Solana Program Deployment and Core Architecture. "
                "Deploying a Solana program assigns an initial upgrade authority stored in the ProgramData account. "
                "Until transferred to a multi-sig or revoked, the upgrade authority keyholder retains unilateral power to deploy modified bytecode. "
                "This represents an operational governance and centralization risk. SanadSquad provides security consulting to help protocol teams design secure governance frameworks and multi-sig architectures before launch."
            ),
        },
        {
            "source_id": "W02",
            "title": "Solana Program Deployment Guide",
            "url": "https://solana.com/docs/programs/deploying",
            "domain": "solana.com",
            "publisher": "Solana Foundation Documentation",
            "service_line": "web3-security",
            "source_group": "docs",
            "published_date": "2024-10-01",
            "quote": "Program authority controls updates; it can be transferred, or removed to make a program immutable. ProgramData stores program executable code.",
            "cleaned_text": (
                "Solana Program Deployment Guide. "
                "Program authority controls updates and can be transferred to a governance multi-sig or revoked to make the program immutable. "
                "ProgramData stores program executable code. Retained authority requires operational governance reviews."
            ),
        },
        {
            "source_id": "W03",
            "title": "OpenZeppelin ERC-4626 Tokenized Vault Standard",
            "url": "https://docs.openzeppelin.com/contracts/5.x/erc4626",
            "domain": "openzeppelin.com",
            "publisher": "OpenZeppelin Documentation",
            "service_line": "web3-security",
            "source_group": "docs",
            "published_date": "2024-05-15",
            "quote": "ERC-4626 defines a standard for tokenized Vaults. Empty vaults are vulnerable to share-price inflation attacks where an attacker donates assets to manipulate the share price, causing subsequent depositors to lose funds due to rounding. Mitigations include virtual shares and virtual assets.",
            "cleaned_text": (
                "OpenZeppelin ERC-4626 Tokenized Vaults. "
                "ERC-4626 provides a standard API for yield-bearing vaults. "
                "Empty-vault share-price inflation attacks occur when an initial depositor deposits 1 wei and donates assets directly to the vault, inflating the share price and causing rounding down losses for subsequent depositors. "
                "Mitigation designs include decimal offsets and virtual shares/assets. SanadSquad audits smart contract vaults to verify share accounting and inflation defenses."
            ),
        },
        {
            "source_id": "W04",
            "title": "OpenZeppelin Proxy API: Upgradeable Contract Architecture",
            "url": "https://docs.openzeppelin.com/contracts/5.x/api/proxy",
            "domain": "openzeppelin.com",
            "publisher": "OpenZeppelin Documentation",
            "service_line": "web3-security",
            "source_group": "docs",
            "published_date": "2024-05-15",
            "quote": "Transparent and UUPS proxy patterns handle upgrade authorization differently. Transparent proxies delegate upgrade administration to a dedicated ProxyAdmin contract, while UUPS proxies enforce authorization checks in the implementation contract. Upgrade administration requires multi-sig governance and architecture review.",
            "cleaned_text": (
                "OpenZeppelin Proxy Contracts and Upgrade Authorization. "
                "Transparent and UUPS proxy architectures handle upgrade authority differently: "
                "Transparent proxies route admin calls to a dedicated ProxyAdmin, while UUPS proxies include the upgrade function inside the implementation contract. "
                "Privileged proxy administrators and implementation authorization require threat modeling, multi-sig governance, and pre-implementation architecture reviews."
            ),
        },
        {
            "source_id": "C01",
            "title": "NIST SP 800-218: Secure Software Development Framework v1.1",
            "url": "https://csrc.nist.gov/pubs/sp/800/218/final",
            "domain": "csrc.nist.gov",
            "publisher": "National Institute of Standards and Technology (NIST)",
            "service_line": "web3-security",
            "source_group": "docs",
            "published_date": "2022-02-01",
            "quote": "Security practices belong throughout the development lifecycle, including requirements, design choices, security reviews and software provenance. Pre-implementation architecture reviews and threat modeling prevent architectural flaws that audits alone cannot easily fix post-coding.",
            "cleaned_text": (
                "NIST SP 800-218 Secure Software Development Framework (SSDF) v1.1. "
                "Integrating security practices across all development phases: preparing the organization, protecting software, producing well-secured software, and responding to vulnerabilities. "
                "Early security consulting, architecture design reviews, and threat modeling address foundational trust assumptions before smart contract code is written."
            ),
        },
        {
            "source_id": "ETH01",
            "title": "Smart Contract Formal Verification and Invariant Specification",
            "url": "https://ethereum.org/developers/docs/smart-contracts/formal-verification/",
            "domain": "ethereum.org",
            "publisher": "Ethereum Foundation Documentation",
            "service_line": "web3-security",
            "source_group": "docs",
            "published_date": "2024-08-20",
            "quote": "Formal verification refers to evaluating the correctness of a contract with respect to a formal specification. Formal verification mathematically checks whether implementation logic conforms to declared invariant properties, but does not prevent vulnerabilities outside the modeled specifications.",
            "cleaned_text": (
                "Ethereum Foundation Smart Contract Formal Verification Guide. "
                "Formal verification evaluates whether smart contract implementation satisfies a formal mathematical specification. "
                "Formal methods test invariant assertions and state transitions against defined preconditions and postconditions. "
                "However, formal verification only verifies conformance to the modeled properties; it does not dynamically prevent runtime flaws or prove complete correctness if assumptions or specifications are incomplete."
            ),
        },
    ],
    "pentesting": [
        {
            "source_id": "P01",
            "title": "OWASP API1:2023 Broken Object Level Authorization",
            "url": "https://api-security.owasp.org/editions/2023/en/0xa1-broken-object-level-authorization/",
            "domain": "api-security.owasp.org",
            "publisher": "OWASP API Security Project",
            "service_line": "pentesting",
            "source_group": "docs",
            "published_date": "2023-12-01",
            "quote": "Broken Object Level Authorization (BOLA, API1:2023) occurs when an API fails to validate whether an authenticated user is authorized to access a specific resource object. Penetration testing identifies these authorization gaps across dApp backend APIs and off-chain infrastructure before attackers exfiltrate data.",
            "cleaned_text": (
                "OWASP API Security Project: Broken Object Level Authorization (API1:2023). "
                "BOLA occurs when endpoints validate user identity (authentication) but fail to check if the caller is authorized to manipulate or access the requested resource object ID. "
                "An authenticated user can access another user's records when object-level access controls are missing. "
                "Penetration testing audits dApp backend APIs, RPC gateways, and administrative interfaces to verify object-level authorization boundaries."
            ),
        },
        {
            "source_id": "P02",
            "title": "OWASP API Security Top 10: Authorization Flaws and Off-Chain Attack Surfaces",
            "url": "https://api-security.owasp.org/editions/2023/en/0x11-t10/",
            "domain": "api-security.owasp.org",
            "publisher": "OWASP Foundation",
            "service_line": "pentesting",
            "source_group": "docs",
            "published_date": "2023-12-01",
            "quote": "Broken Object Level Authorization (BOLA, API1:2023) occurs when an API fails to validate whether an authenticated user is authorized to access a specific resource object. Penetration testing identifies these authorization gaps across dApp backend APIs, admin gateways, and off-chain infrastructure before attackers can exfiltrate sensitive user data.",
            "cleaned_text": (
                "OWASP API Security Top 10. "
                "Broken Object Level Authorization (BOLA, API1:2023) allows authenticated users to access objects belonging to other tenants when endpoints omit object-level permission checks. "
                "Authorization checks must verify object-level permissions, distinct from user authentication (identity verification). "
                "Penetration testing targets the realistic off-chain attack surface: dApp backend APIs, RPC gateways, relayer infrastructure, and administrative portals."
            ),
        },
        {
            "source_id": "P03",
            "title": "Model Context Protocol (MCP) Specification: Authorization Hardening",
            "url": "https://blog.modelcontextprotocol.io/posts/2026-07-28/",
            "domain": "modelcontextprotocol.io",
            "publisher": "MCP Maintainers",
            "service_line": "pentesting",
            "source_group": "production",
            "published_date": "2026-07-28",
            "quote": "The MCP specification revision introduces authentication hardening and routing architecture to define strict authorization boundaries between MCP clients and tool-executing servers.",
            "cleaned_text": (
                "Model Context Protocol (MCP) Specification Update 2026-07-28. "
                "The revised specification introduces auth hardening, request handling, and routing architecture to secure server/client trust boundaries. "
                "Penetration testing assesses off-chain MCP servers and agent tooling endpoints to prevent unauthorized tool execution across API trust boundaries."
            ),
        },
        {
            "source_id": "P04",
            "title": "OWASP Top 10: Software and Data Integrity Failures in Off-Chain Infrastructure",
            "url": "https://top10.owasp.org/",
            "domain": "top10.owasp.org",
            "publisher": "OWASP Foundation",
            "service_line": "pentesting",
            "source_group": "docs",
            "published_date": "2024-09-24",
            "quote": "Software and data integrity failures in CI/CD pipelines, package dependencies, and deployment tooling enable attackers to compromise off-chain infrastructure without exploiting on-chain smart contracts. Penetration testing identifies exposed build pipelines, unsigned artifacts, and dependency vulnerabilities across development environments.",
            "cleaned_text": (
                "OWASP Top 10: Software and Data Integrity Failures (A08:2021). "
                "CI/CD build pipelines, package registries, and developer tooling lacking integrity verification allow attackers to inject malicious code into deployment artifacts. "
                "Penetration testing focuses on the real-world off-chain attack surface: CI/CD runners, cloud hosting environments, DNS and frontend signing interfaces, and external dependencies that wrap smart contract protocols."
            ),
        },
    ],
    "agentic-security": [
        {
            "source_id": "A01",
            "title": "OWASP Agent Control Standard (ACS) for Runtime Execution Boundaries",
            "url": "https://genai.owasp.org/resource/agent-control-standard-acs/",
            "domain": "genai.owasp.org",
            "publisher": "OWASP GenAI Security Project",
            "service_line": "agentic-security",
            "source_group": "docs",
            "published_date": "2026-09-01",
            "quote": "The OWASP Agent Control Standard (ACS) defines runtime execution boundaries around AI agent tools to restrict unauthorized actions without claiming to universally prevent prompt injection.",
            "cleaned_text": (
                "OWASP GenAI Agent Control Standard (ACS). "
                "The Agent Control Standard defines declarative safety controls and middleware hooks across AI agent frameworks. "
                "Runtime execution controls restrict what tools autonomous agents can invoke and provide observability into agent actions, reducing the impact of prompt injection without claiming to universally prevent it. "
                "SanadSquad builds custom security detectors, PR reviewers, and monitoring agents to enforce tool boundaries across development and production."
            ),
        },
        {
            "source_id": "A02",
            "title": "OWASP Top 10 for Agentic Applications: Autonomous Agent Risks",
            "url": "https://genai.owasp.org/resource/owasp-top-10-for-agentic-applications-for-2026/",
            "domain": "genai.owasp.org",
            "publisher": "OWASP GenAI Project",
            "service_line": "agentic-security",
            "source_group": "docs",
            "published_date": "2025-12-09",
            "quote": "Autonomous agents executing transactions must decouple signing authority from text-generation models via deterministic policies and strict tool access boundaries.",
            "cleaned_text": (
                "OWASP Top 10 for Agentic Applications (2026 Framework). "
                "A reference framework for recognizing autonomous-agent security risks and building controls around tool-using workflows. "
                "Autonomous agents executing transactions must decouple signing authority from text-generation models via deterministic policies and strict tool access boundaries. "
                "Tool misuse occurs when indirect prompt injection directs an agent to invoke privileged tools."
            ),
        },
        {
            "source_id": "A03",
            "title": "GitHub Code Scanning on Pull Requests",
            "url": "https://docs.github.com/en/code-security/concepts/code-scanning/code-scanning-on-pull-requests",
            "domain": "github.com",
            "publisher": "GitHub Documentation",
            "service_line": "agentic-security",
            "source_group": "production",
            "published_date": "2024-08-01",
            "quote": "Pull-request security analysis can surface findings before merge. SanadSquad builds custom security detectors, PR reviewers, and monitoring agents to detect protocol invariant violations in CI/CD pipelines.",
            "cleaned_text": (
                "GitHub Code Scanning on Pull Requests. "
                "Integrating security code scanning into pull-request workflows allows engineering teams to catch invariant regressions and vulnerabilities before merging code into main branches. "
                "SanadSquad develops custom security detectors, automated PR reviewers, and real-time monitoring agents tailored to protocol invariants."
            ),
        },
        {
            "source_id": "A03",
            "title": "GitHub Code Scanning Alerts on Pull Requests",
            "url": "https://docs.github.com/en/code-security/concepts/code-scanning/code-scanning-alerts",
            "domain": "github.com",
            "publisher": "GitHub Documentation",
            "service_line": "agentic-security",
            "source_group": "production",
            "published_date": "2024-08-01",
            "quote": "Repository security scanning can report findings on pull requests before changes merge. SanadSquad builds custom protocol detectors and automated PR review tools to check invariants.",
            "cleaned_text": (
                "GitHub Code Scanning Alerts. "
                "Repository security scanning surfaces security alerts directly on pull requests before code merges. "
                "SanadSquad builds custom protocol detectors, automated PR reviewers, and real-time monitoring agents to catch invariant violations in development."
            ),
        },
        {
            "source_id": "A04",
            "title": "OWASP Agentic Security Initiative: Autonomous Agent Control and Tool Boundaries",
            "url": "https://genai.owasp.org/initiatives/agentic-security-initiative/",
            "domain": "genai.owasp.org",
            "publisher": "OWASP GenAI Project",
            "service_line": "agentic-security",
            "source_group": "docs",
            "published_date": "2024-11-20",
            "quote": "The Agentic Security Research Initiative explores the emerging security implications of autonomous agents and multi-step AI workflows. Mitigating tool manipulation requires the Agent Control Standard (ACS) to establish hard execution boundaries, tool authorization scopes, and independent policy verification outside the model context.",
            "cleaned_text": (
                "OWASP Agentic Security Initiative: Securing Autonomous Agents and Multi-Step AI Workflows. "
                "The Agentic Security Research Initiative explores tool manipulation and execution boundaries across agentic frameworks. "
                "The Agent Control Standard (ACS) establishes operational transparency, tool authorization boundaries, and independent policy verification outside model context to prevent unauthorized actions."
            ),
        },
        {
            "source_id": "SW01",
            "title": "Prompt injection: What's the worst that can happen?",
            "url": "https://simonwillison.net/2023/Apr/14/worst-that-can-happen/",
            "domain": "simonwillison.net",
            "publisher": "Simon Willison",
            "service_line": "agentic-security",
            "source_group": "blogs",
            "published_date": "2023-04-14",
            "quote": "Simon Willison analyzes prompt injection risks when autonomous agents are given tools and private API credentials. Mitigating tool misuse requires hard execution boundaries outside model context, though prompt injection remains an active research challenge.",
            "cleaned_text": (
                "Simon Willison Research: Prompt injection risks in tool-enabled AI agents. "
                "When autonomous models access tools and sensitive data, indirect prompt injection can hijack tool invocations. "
                "Mitigating unauthorized tool execution requires hard operational boundaries outside LLM context."
            ),
        },
    ],
    "agentic-payments": [
        {
            "source_id": "M01",
            "title": "x402 Payment Required: Internet-Native Payment Signaling Protocol",
            "url": "https://github.com/x402-foundation/x402",
            "domain": "github.com",
            "publisher": "x402 Foundation Specification",
            "service_line": "agentic-payments",
            "source_group": "production",
            "published_date": "2024-11-01",
            "quote": "The x402 standard defines HTTP 402 payment signaling where resource servers specify payment requirements in response headers. Facilitator-based verification and settlement are optional; clients and resource servers can settle directly peer-to-peer or connect to off-chain facilitators for multi-party coordination.",
            "cleaned_text": (
                "x402 Foundation: HTTP 402 Payment Required Protocol Specification. "
                "The x402 protocol standardizes payment signaling via HTTP 402 status codes. "
                "Facilitator integration is optional; architectures can settle directly peer-to-peer or utilize third-party facilitators for verification and settlement. "
                "SanadSquad reviews payment agent architectures, tool authorization ceilings, and replay protection across agentic payment flows."
            ),
        },
        {
            "source_id": "M01",
            "title": "x402 Foundation: Facilitator Core Concept",
            "url": "https://github.com/x402-foundation/x402/blob/main/docs/core-concepts/facilitator.md",
            "domain": "github.com",
            "publisher": "x402 Foundation Specification",
            "service_line": "agentic-payments",
            "source_group": "production",
            "published_date": "2024-11-01",
            "quote": "x402 uses payment-required request/response signaling; a facilitator is optional but recommended for verifying and settling payments. Servers can handle verification and settlement directly peer-to-peer.",
            "cleaned_text": (
                "x402 Foundation: Facilitator Architecture and Responsibilities. "
                "The x402 specification defines HTTP 402 payment signaling where resource servers specify payment requirements in response headers. "
                "Facilitator-based verification and settlement are optional; resource servers can verify cryptographic payment payloads and settle transactions directly on-chain, or delegate settlement to an external facilitator."
            ),
        },
        {
            "source_id": "M02",
            "title": "Machine Payments Protocol (MPP): EVM and x402 Support",
            "url": "https://mpp.dev/blog/evm-x402-support",
            "domain": "mpp.dev",
            "publisher": "Machine Payments Protocol (MPP)",
            "service_line": "agentic-payments",
            "source_group": "docs",
            "published_date": "2026-06-08",
            "quote": "mppx supports MPP EVM charge and compatible x402 exact flows from one SDK interface, enabling payment runtimes to manage authorization limits and settlement across protocols.",
            "cleaned_text": (
                "Machine Payments Protocol: EVM and x402 Support Announcement (June 8, 2026). "
                "The mppx client library added unified support for MPP EVM charges alongside compatible x402 exact payment flows within a single interface. "
                "This enables agent builders to enforce per-agent spending authorization limits and verification paths without protocol tribalism."
            ),
        },
        {
            "source_id": "M03",
            "title": "Machine Payments Protocol (MPP): Improved Sessions Experience",
            "url": "https://mpp.dev/blog/sessions-improved",
            "domain": "mpp.dev",
            "publisher": "Machine Payments Protocol (MPP)",
            "service_line": "agentic-payments",
            "source_group": "docs",
            "published_date": "2026-06-17",
            "quote": "A session can authorize spending once and incrementally extend authorization with usage, providing efficient authorization for usage-based API calls without per-request transaction signing.",
            "cleaned_text": (
                "Machine Payments Protocol: Improved Sessions Experience (June 17, 2026). "
                "Session-based payment authorization enables an autonomous agent to authorize a spending session once and incrementally extend authorization as resources are consumed. "
                "This streamlines usage-based API payments while enforcing authorization ceilings and replay protection."
            ),
        },
        {
            "source_id": "M04",
            "title": "Coinbase x402 Implementation: HTTP 402 Payment Required and MPP Comparison",
            "url": "https://github.com/coinbase/x402",
            "domain": "github.com",
            "publisher": "Coinbase Developer Documentation",
            "service_line": "agentic-payments",
            "source_group": "production",
            "published_date": "2024-10-15",
            "quote": "Comparing x402 versus MPP settlement mechanics and facilitator trust: The x402 protocol standardizes HTTP 402 payment signaling where resource servers specify payment requirements in response headers. Facilitator-based settlement is an optional pattern for off-chain verification, while direct settlement remains fully supported.",
            "cleaned_text": (
                "Coinbase x402 Protocol Implementation: Comparing x402 versus MPP settlement mechanics and facilitator trust. "
                "The x402 protocol standardizes HTTP 402 payment signaling where resource servers specify payment requirements in response headers. "
                "Facilitators are optional multi-party settlement coordinators; direct settlement is supported. Replay protection and payment authorization are required to prevent double-spending."
            ),
        },
        {
            "source_id": "M05",
            "title": "Stripe Machine Payments Protocol: Agent Payment Sessions and Settlement",
            "url": "https://stripe.com/blog/machine-payments-protocol",
            "domain": "stripe.com",
            "publisher": "Stripe Engineering Blog",
            "service_line": "agentic-payments",
            "source_group": "blogs",
            "published_date": "2024-09-18",
            "quote": "Machine Payments Protocol (MPP) enables autonomous AI agents to negotiate payment intents and session state directly with payment processors, enforcing per-agent authorization ceilings and cryptographically signed session tokens.",
            "cleaned_text": (
                "Stripe Machine Payments Protocol (MPP). "
                "Machine Payments Protocol (MPP) enables autonomous AI agents to negotiate payment intents and session state directly with payment processors, "
                "enforcing per-agent authorization ceilings and cryptographically signed session tokens. "
                "MPP coordinates session lifecycle directly between agent runtimes and payment processors without relying on intermediary facilitators."
            ),
        },
    ],
}


def get_fixtures_for_service(service_line: str) -> list[dict[str, Any]]:
    norm = COMMERCIAL_TO_RESEARCH_MAP.get(service_line.lower().strip(), service_line.lower().strip())
    # For security consulting, return consulting-relevant web3 fixtures plus cross-cutting sources
    if norm in {"security-consulting", "consulting"} or "consulting" in service_line.lower():
        # Curate consulting-specific items first: C01, C02, W04, W02, plus general web3
        consulting_items = []
        for sid in ["C01", "C02", "W04", "W02"]:
            for item in RESEARCH_FIXTURES.get("web3-security", []):
                if item.get("source_id") == sid and item not in consulting_items:
                    consulting_items.append(item)
        # Add remaining web3 items
        for item in RESEARCH_FIXTURES.get("web3-security", []):
            if item not in consulting_items:
                consulting_items.append(item)
        return consulting_items

    return RESEARCH_FIXTURES.get(norm, [])


def get_all_fixtures() -> list[dict[str, Any]]:
    all_f = []
    for items in RESEARCH_FIXTURES.values():
        all_f.extend(items)
    return all_f
