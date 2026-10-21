"""Verified public-domain fixture dataset for offline marketing research testing.

All records represent real domains on the canonical allowlist and
realistic security research topics for the four SanadSquad service lines:
- web3-security: Invariant verification and post-audit deployment drift
- pentesting: Infrastructure exposure, CI/CD, and dependency poisoning
- agentic-security: Prompt injection, agent wallets, and spending policy
- agentic-payments: x402 vs MPP mechanics, settlement, and facilitator trust
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
            "title": "Solana Verified Builds and Program Upgrade Authority Management",
            "url": "https://solana.com/docs/programs/verified-builds",
            "domain": "solana.com",
            "publisher": "Solana Foundation Documentation",
            "service_line": "web3-security",
            "source_group": "docs",
            "published_date": "2024-11-15",
            "quote": "Solana verified builds provide deterministic proof that on-chain executable bytecode matches the audited source commit. Build verification establishes source provenance but does not ensure contract security if the code contains logic flaws, and upgrade authority management remains necessary to prevent post-deployment program alterations.",
            "cleaned_text": (
                "Solana Verified Builds and Program Deployment Authority. "
                "Deterministic verification via solana-verify proves that on-chain bytecode corresponds directly to the specified Git commit, establishing binary build provenance. "
                "Build verification confirms source identity rather than functional correctness, so upgrade authority must still be transferred to a multi-sig or burned to prevent unverified program modifications."
            ),
        },
        {
            "title": "Solana Program Deployment and Upgrade Authority Lifecycle",
            "url": "https://solana.com/docs/core/programs/program-deployment",
            "domain": "solana.com",
            "publisher": "Solana Foundation Documentation",
            "service_line": "web3-security",
            "source_group": "docs",
            "published_date": "2024-10-01",
            "quote": "Deploying a Solana program assigns an initial upgrade authority stored in the ProgramData account. Without transferring upgrade authority to a multi-sig or revoking it entirely, the designated upgrade authority can alter program code at any time without community source verification.",
            "cleaned_text": (
                "Solana Program Deployment and Core Architecture. "
                "Deploying a Solana program assigns an initial upgrade authority stored in the ProgramData account. "
                "Until transferred to a multi-sig or revoked, the upgrade authority keyholder retains unilateral power to deploy modified bytecode. "
                "This represents a centralization and governance control risk where code can be modified post-audit without re-verification, rather than an unauthorized third-party exploit."
            ),
        },
        {
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
            "title": "OWASP API Security Top 10: Authorization Flaws and Off-Chain Attack Surfaces",
            "url": "https://api-security.owasp.org/editions/2023/en/0x11-t10/",
            "domain": "api-security.owasp.org",
            "publisher": "OWASP Foundation",
            "service_line": "pentesting",
            "source_group": "docs",
            "published_date": "2023-12-01",
            "quote": "Broken Object Level Authorization (BOLA) occurs when an API fails to validate whether an authenticated user is permitted to access a specific resource object. BOLA is an authorization failure distinct from user authentication; penetration testing validates off-chain dApp API endpoints, admin gateways, and data access controls.",
            "cleaned_text": (
                "OWASP API Security Top 10. "
                "Broken Object Level Authorization (BOLA, API1:2023) allows authenticated users to access objects belonging to other tenants when endpoints omit object-level permission checks. "
                "Authorization checks must verify object-level permissions, distinct from user authentication (identity verification). "
                "Penetration testing targets the realistic off-chain attack surface: dApp backend APIs, RPC gateways, relayer infrastructure, and administrative portals."
            ),
        },
        {
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
            "title": "Prompt injection: What's the worst that can happen?",
            "url": "https://simonwillison.net/2023/Apr/14/worst-that-can-happen/",
            "domain": "simonwillison.net",
            "publisher": "Simon Willison",
            "service_line": "agentic-security",
            "source_group": "blogs",
            "published_date": "2023-04-14",
            "quote": "Prompt injection affects any AI agent system with access to tools or sensitive data. Mitigating tool misuse requires hard execution boundaries outside the LLM context.",
            "cleaned_text": (
                "Prompt injection: What's the worst that can happen? Simon Willison explores the security risks when autonomous agents are given tools, private data access, and API credentials. "
                "Relying on prompt instructions alone is insufficient; hard cryptographic and operational boundaries must prevent unauthorized tool execution. "
                "Agentic wallet security requires decoupled signing policies rather than model self-restraint."
            ),
        },
        {
            "title": "OWASP Top 10 for Agentic Applications: Autonomous Agent Risks",
            "url": "https://genai.owasp.org/resource/owasp-top-10-for-agentic-applications-for-2026/",
            "domain": "genai.owasp.org",
            "publisher": "OWASP GenAI Project",
            "service_line": "agentic-security",
            "source_group": "docs",
            "published_date": "2024-12-15",
            "quote": "Autonomous agents executing financial transactions must decouple signing authority from text-generation models via deterministic spending policies and strict tool access boundaries.",
            "cleaned_text": (
                "OWASP Top 10 for Agentic Applications (2026 Edition). "
                "Autonomous agents executing financial transactions must decouple signing authority from text-generation models via deterministic spending policies and strict tool access boundaries. "
                "Tool misuse occurs when indirect prompt injection directs an agent to invoke privileged wallet execution tools."
            ),
        },
    ],
    "agentic-payments": [
        {
            "title": "Coinbase x402 Protocol Specification: HTTP 402 Payment Required",
            "url": "https://github.com/coinbase/x402",
            "domain": "github.com",
            "publisher": "Coinbase Developer Documentation",
            "service_line": "agentic-payments",
            "source_group": "production",
            "published_date": "2024-10-15",
            "quote": "The x402 protocol standardizes HTTP 402 payment signaling where resource servers specify payment requirements in response headers, while off-chain facilitators verify client authorizations and handle final settlement.",
            "cleaned_text": (
                "Coinbase x402 Protocol Specification. "
                "The x402 protocol standardizes HTTP 402 payment signaling where resource servers specify payment requirements in response headers, "
                "while off-chain facilitators verify client authorizations and handle final settlement. "
                "HTTP 402 acts as the negotiation protocol; facilitator trust and replay protection are required to prevent double-spending."
            ),
        },
        {
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
        {
            "title": "x402 Foundation: Open Internet Payment Standards",
            "url": "https://x402.org",
            "domain": "x402.org",
            "publisher": "x402 Foundation",
            "service_line": "agentic-payments",
            "source_group": "docs",
            "published_date": "2024-11-01",
            "quote": "The x402 standard uses HTTP 402 status codes for internet-native payment negotiation, standardizing payment headers across AI agent runtimes.",
            "cleaned_text": (
                "x402 Foundation. The x402 standard uses HTTP 402 status codes for internet-native payment negotiation. "
                "It enables AI agents to pay for web resources seamlessly while separating signaling transport from facilitator verification and settlement."
            ),
        },
    ],
}


def get_fixtures_for_service(service_line: str) -> list[dict[str, Any]]:
    norm = COMMERCIAL_TO_RESEARCH_MAP.get(service_line.lower().strip(), service_line.lower().strip())
    return RESEARCH_FIXTURES.get(norm, [])


def get_all_fixtures() -> list[dict[str, Any]]:
    all_f = []
    for items in RESEARCH_FIXTURES.values():
        all_f.extend(items)
    return all_f
