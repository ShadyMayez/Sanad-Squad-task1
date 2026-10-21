"""Marketing policy validation enforcing claims, confidentiality, contact, and CTA rules.

Directive: SANADSQUAD_V3_OFFICIAL_BRAND_INTEGRATION_01
"""
from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any
from pydantic import BaseModel, Field
from .config import ROOT

from .contact_config import (
    CompanyContactConfig,
    load_company_contact,
    is_synthetic_contact,
    is_recruitment_email,
    EMAIL_PATTERN,
    PHONE_PATTERN,
)

DEFAULT_MARKETING_RULES_PATH = ROOT / "marketing-rules.md"

# Direct commercial solicitation patterns (distinguished from educational recommendations)
COMMERCIAL_CTA_PATTERNS = [
    r"\b(?:work\s+with\s+sanadsquad|hire\s+sanadsquad|partner\s+with\s+sanadsquad)\b",
    r"\b(?:contact\s+sanadsquad|consult\s+sanadsquad|discuss\s+with\s+sanadsquad)\b",
    r"\b(?:schedule\s+(?:an?\s+)?audit|book\s+(?:an?\s+)?audit|request\s+(?:an?\s+)?audit)\b",
    r"\b(?:contact\s+our\s+team|contact\s+us|reach\s+out\s+to\s+us|get\s+in\s+touch)\b",
    r"\b(?:dm\s+us\s+to|email\s+us\s+at|reach\s+out\s+for\s+an?\s+assessment)\b",
    r"\b(?:security\s+consultation|discuss\s+(?:your\s+)?architecture)\b",
    r"\b(?:request\s+(?:a\s+)?(?:sanadsquad\s+)?penetration\s+test)\b",
]

# Educational security recommendations (permitted advice, NOT commercial solicitation)
EDUCATIONAL_ACTION_PATTERNS = [
    r"\b(?:enforce|verify|isolate|inspect|audit|review|check|validate|structure|implement)\b",
]

DEFAULT_BANNED_COMPETITORS = [
    "certik",
    "open zeppelin",
    "openzeppelin",
    "trail of bits",
    "trailofbits",
    "consensys diligence",
    "halborn",
    "spearbit",
    "code4rena",
    "sherlock",
]

DEFAULT_GUARANTEE_PHRASES = [
    "guaranteed security",
    "100% secure",
    "completely secure",
    "unhackable",
    "zero risk",
    "eliminate all risk",
    "bulletproof",
    "guarantees safety",
    "guarantee safety",
]

OFFICIAL_SERVICES = [
    "blockchain-security-audits",
    "penetration-testing",
    "agentic-security-tooling",
    "agentic-payments",
    "security-consulting",
]

LEGACY_SERVICE_ALIASES = {
    "web3-security": "blockchain-security-audits",
    "pentesting": "penetration-testing",
    "agentic-security": "agentic-security-tooling",
    "consulting": "security-consulting",
}


class MarketingPolicy(BaseModel):
    policy_name: str = "sanadsquad_marketing_rules"
    version: str = "2.0.0"
    max_tweets_per_post: int = 1
    max_chars_per_tweet: int = 280
    service_lines: list[str] = Field(default_factory=lambda: [
        "web3-security",
        "pentesting",
        "agentic-security",
        "agentic-payments",
    ])
    commercial_services: list[str] = Field(default_factory=lambda: list(OFFICIAL_SERVICES))
    banned_competitor_names: list[str] = Field(default_factory=lambda: list(DEFAULT_BANNED_COMPETITORS))
    prohibited_guarantee_phrases: list[str] = Field(default_factory=lambda: list(DEFAULT_GUARANTEE_PHRASES))


def load_marketing_policy(path: Path | None = None) -> MarketingPolicy:
    """Load marketing policy from markdown JSON block or defaults."""
    rules_path = path or DEFAULT_MARKETING_RULES_PATH
    if rules_path.exists():
        content = rules_path.read_text(encoding="utf-8")
        match = re.search(r"```json\s*\n(.*?)\n```", content, re.DOTALL)
        if match:
            try:
                data = json.loads(match.group(1))
                return MarketingPolicy.model_validate(data)
            except Exception:
                pass
    return MarketingPolicy()


def detect_commercial_cta(text: str) -> tuple[bool, int, list[str]]:
    """Detect direct commercial solicitation CTAs.
    
    Returns (has_cta, cta_count, matched_snippets).
    Distinguishes practical educational advice from commercial sales pitches.
    Counts distinct CTA instances across sentences and conjunction clauses.
    """
    sentences = re.split(r"(?<=[.!?])\s+|\n+", text)
    matched_snippets: list[str] = []
    cta_count = 0

    for sent in sentences:
        s_clean = sent.lower().strip()
        if not s_clean:
            continue
        sent_matches = []
        for pat in COMMERCIAL_CTA_PATTERNS:
            for m in re.finditer(pat, s_clean, re.IGNORECASE):
                sent_matches.append(m.group(0))
        if sent_matches:
            distinct_clauses = re.split(r"[,;]\s*(?:and|or|also)\s+", s_clean)
            sub_matches = 0
            for clause in distinct_clauses:
                if any(re.search(pat, clause, re.IGNORECASE) for pat in COMMERCIAL_CTA_PATTERNS):
                    sub_matches += 1
            cta_count += max(1, sub_matches)
            matched_snippets.extend(sent_matches)

    return cta_count > 0, cta_count, matched_snippets


def validate_contact_cta(
    tweets: list[str],
    contact_config: CompanyContactConfig | None = None,
    allow_cta: bool = False,
    content_type: str = "marketing-post",
) -> list[str]:
    """Automated deterministic validation for commercial contact CTAs.
    
    Enforces:
    1. Reject unapproved or synthetic email addresses and phone numbers.
    2. Reject contact details when approval status is false.
    3. Reject contact CTAs on posts where CTA eligibility was not reserved (or exceeding 1 per week).
    4. Reject multiple CTAs within one post.
    5. Verify that displayed email/channel matches approved configuration without requiring phone if none exists.
    6. Verify the 280-character limit after contact information is inserted.
    7. Bar technical threads strictly from commercial contact CTAs.
    8. Bar recruitment email career@sanadsquad.com from commercial marketing CTAs.
    """
    errors: list[str] = []
    full_text = " ".join(tweets)
    cfg = contact_config if contact_config is not None else load_company_contact()

    # Detect emails and phone numbers in tweets
    found_emails = EMAIL_PATTERN.findall(full_text)
    found_phones = PHONE_PATTERN.findall(full_text)
    real_phones: list[str] = []
    for p in found_phones:
        p_clean = p.strip().rstrip(".,;")
        digits = re.sub(r"\D", "", p_clean)
        if len(digits) >= 7:
            if not re.match(r"^0\.\d+\.\d+$", p_clean):
                real_phones.append(p_clean)

    has_cta, cta_count, cta_matches = detect_commercial_cta(full_text)
    has_contact_marker = bool(
        found_emails
        or real_phones
        or re.search(r"\b(?:email:|phone:|contact sanadsquad|consult sanadsquad|discuss your architecture:)\b", full_text, re.IGNORECASE)
    )

    # 1. Technical thread prohibition
    if content_type == "tech-thread":
        if has_cta or has_contact_marker or found_emails or real_phones:
            errors.append(
                "Technical threads are strictly barred from containing commercial CTAs or company contact details."
            )
        return errors

    # 2. Recruitment email prohibition
    for em in found_emails:
        if is_recruitment_email(em):
            errors.append(
                f"Recruitment email '{em}' is reserved for careers/hiring and must not be used for commercial business inquiries. "
                "Use verified inquiries channel frank@sanadsquad.com."
            )

    # 3. Synthetic placeholder contact prohibition
    for em in found_emails:
        if is_synthetic_contact(em):
            errors.append(
                f"Fictional or unapproved contact placeholder '{em}' rejected from commercial publication."
            )
    for ph in real_phones:
        if is_synthetic_contact(ph):
            errors.append(
                f"Fictional telephone placeholder '{ph}' rejected from commercial publication."
            )

    # 4. Rejection when approval status is False or configuration is missing
    if (found_emails or real_phones or has_cta) and not cfg.is_operational():
        missing = cfg.get_missing_fields()
        errors.append(
            f"Contact details rejected: company-contact.json approval status is false or contact info is missing. "
            f"Missing fields: {missing}. Only company-approved contact details may be published."
        )
        return errors

    # 5. Multiple CTAs within a single post
    if cta_count > 1 or len(found_emails) > 1 or len(real_phones) > 1:
        errors.append(
            f"Post contains multiple CTAs or contact entries (found {cta_count} CTAs, {len(found_emails)} emails, {len(real_phones)} phones). "
            "Maximum 1 CTA permitted per post."
        )

    # 6. CTA eligibility reservation check (planner must reserve CTA eligibility)
    if (has_cta or found_emails or real_phones) and not allow_cta:
        errors.append(
            "Commercial contact CTA detected, but CTA eligibility is not reserved for this marketing slot "
            "(maximum one CTA permitted across three weekly marketing posts)."
        )

    # 7. Match verification of displayed email and phone against approved configuration
    if allow_cta and (has_cta or has_contact_marker):
        appr_email = cfg.business_inquiries_email.strip() if cfg.business_inquiries_email else ""
        appr_phone = cfg.business_phone_number.strip() if cfg.business_phone_number else ""
        appr_form = cfg.contact_form_url.strip() if cfg.contact_form_url else ""

        # Email match
        if found_emails:
            for em in found_emails:
                if appr_email and em.lower() != appr_email.lower():
                    errors.append(
                        f"Unapproved email address '{em}'. Displayed email must exactly match approved configuration '{appr_email}'."
                    )
        elif not appr_email and not appr_form and not real_phones:
            errors.append("Approved commercial CTA is missing approved business inquiries contact channel.")

        # Phone match: if a phone number was included in the tweet
        if real_phones:
            if not appr_phone:
                errors.append(
                    f"Unapproved telephone number '{real_phones[0]}' published: SanadSquad does not publish an approved phone number."
                )
            else:
                for ph in real_phones:
                    norm_ph = re.sub(r"[^\d+]", "", ph)
                    norm_appr = re.sub(r"[^\d+]", "", appr_phone)
                    if norm_ph != norm_appr and ph != appr_phone:
                        errors.append(
                            f"Unapproved phone number '{ph}'. Displayed phone must match approved configuration '{appr_phone}'."
                        )

    # 8. Character limit verification after contact information is inserted
    for i, tweet in enumerate(tweets, 1):
        if len(tweet) > 280:
            errors.append(
                f"Tweet {i} exceeds 280-character limit after contact information insertion ({len(tweet)} > 280)."
            )

    return errors


def validate_marketing_claims(
    tweets: list[str],
    policy: MarketingPolicy | None = None,
    service_line: str | None = None,
) -> list[str]:
    """Validate claim restrictions, competitor naming, guarantees, and service boundaries."""
    if policy is None:
        policy = load_marketing_policy()

    errors: list[str] = []
    full_text = " ".join(tweets)

    # 1. Guarantee / absolute outcome check
    if re.search(r"\b(?:guarantee\w*|unhackable|bulletproof|100%\s*secure|zero\s+risk|bug-free)\b", full_text, re.IGNORECASE):
        errors.append(
            "Prohibited guarantee claim: SanadSquad reduces risk; we do not eliminate it."
        )
    for phrase in policy.prohibited_guarantee_phrases:
        if re.search(rf"\b{re.escape(phrase)}\b", full_text, re.IGNORECASE):
            errors.append(
                f"Prohibited guarantee claim: '{phrase}'. SanadSquad reduces risk; we do not eliminate it."
            )

    # 2. Named competitor check (critique contract-only coverage model, not named firms)
    for competitor in policy.banned_competitor_names:
        if re.search(rf"\b{re.escape(competitor)}\b", full_text, re.IGNORECASE):
            errors.append(
                f"Prohibited named competitor attack: '{competitor}'. "
                "Critique the limits of contract-only auditing models, never name competitor firms."
            )

    # 3. Accretion third-party findings misattribution check
    if re.search(r"\b(?:accretion|swig|light\s+protocol|privacy\s+cash|ss-03\d{3})\b", full_text, re.IGNORECASE):
        if re.search(r"\b(?:we\s+audited|our\s+audit|we\s+found|our\s+findings|client\s+history|discovered)\b", full_text, re.IGNORECASE):
            errors.append(
                "Misattribution: Third-party audit material (Accretion) must never be claimed "
                "as SanadSquad client engagements, audits, or achievements."
            )

    # 4. Unsupported superiority claims check
    if re.search(r"\b(?:industry-leading|unmatched\s+expertise|best\s+security\s+firm|market\s+leader|number\s+one\s+in\s+security|world's\s+best|unrivaled\s+protection)\b", full_text, re.IGNORECASE):
        errors.append(
            "Unsupported superiority claim: SanadSquad does not make unverified superlative superiority claims."
        )

    # 5. Generic marketing claims prohibition
    if re.search(r"\b(?:(?:we\s+secure|secures?)\s+everything|(?:we\s+provide\s+)?(?:the\s+)?best\s+blockchain\s+security|contact\s+us\s+for\s+all\s+your\s+cybersecurity\s+needs|(?:we\s+protect|protects?)\s+everything)\b", full_text, re.IGNORECASE):
        errors.append(
            "Generic marketing claims prohibited: SanadSquad provides specific, evidence-backed service descriptions, not generic 'secure everything' or 'best security' slogans."
        )

    # 6. Unsupported company experience & audit statistics check
    if re.search(r"\b(?:(?:we\s+audited|our\s+audit\s+of|we\s+secured|our\s+client|we\s+penetration\s+tested|we\s+tested)\s+(?:bybit|safe|solana|ethereum|stripe|bybit's|safe's))\b", full_text, re.IGNORECASE) or \
       re.search(r"\b(?:we\s+audited\s+the\s+affected\s+contract|we\s+discovered\s+the\s+bybit\s+flaw|our\s+client\s+experienced\s+this\s+breach)\b", full_text, re.IGNORECASE):
        errors.append(
            "Unverified company experience: A retrieved vulnerability or incident does not prove SanadSquad worked on that target. "
            "Never claim external targets or breaches as SanadSquad client engagements."
        )

    # Reject unverified historical audit statistics without explicit approval
    if re.search(r"\b(?:\d+\+?\s+(?:rust|solana|smart\s+contract|evm)?\s*audits?|\d+\+?\s+(?:criticals?|highs?|mediums?)|300\+\s+criticals|\d+%\s+success\s+rate)\b", full_text, re.IGNORECASE):
        errors.append(
            "Unsupported company statistics: Historical audit counts, severity statistics, and researcher counts require explicit marketing approval before publication. Preserve company audit confidentiality."
        )

    # 7. Check individual post CTA cap (max 1 CTA per post)
    has_cta, cta_count, cta_matches = detect_commercial_cta(full_text)
    if cta_count > 1:
        errors.append(
            f"Individual marketing post contains {cta_count} CTAs ({cta_matches}). "
            "At most 1 CTA is permitted per post."
        )

    # 8. Overbroad coverage / absolute security claims check
    if re.search(r"\b(?:secures?\s+(?:the\s+)?entire\s+(?:connected\s+)?stack|complete\s+(?:connected\s+)?stack\s+security|guarantees?\s+(?:total|complete|entire)\s+coverage|total\s+stack\s+protection|bulletproof\s+coverage)\b", full_text, re.IGNORECASE):
        errors.append(
            "Overbroad coverage claim: SanadSquad does not claim to secure the entire connected stack or promise comprehensive security coverage beyond approved service-positioning statements."
        )

    # 9. Inaccurate x402 specification settlement claim check
    if re.search(r"\b(?:uses?\s+http\s+402\s+for\s+(?:facilitator\s+)?settlement|http\s+402\s+settles?|settlement\s+via\s+http\s+402|settles?\s+via\s+http\s+402)\b", full_text, re.IGNORECASE):
        errors.append(
            "Inaccurate x402 specification claim: HTTP 402 is an RFC status code for payment signaling/transport; off-chain facilitators verify client authorizations and handle settlement. Posts must distinguish HTTP 402 signaling from facilitator verification and settlement."
        )

    # 10. Wrong-service marketing claims check
    sl_norm = (service_line or "").lower().strip()
    if sl_norm:
        if "pentest" in sl_norm or "penetration" in sl_norm:
            if re.search(r"\b(?:smart\s+contract\s+invariants?|formal\s+verification|svm\s+bytecode|solidity\s+invariants?)\b", full_text, re.IGNORECASE):
                errors.append(
                    "Wrong-service claim: Penetration testing covers web applications, APIs, node infrastructure, SDKs, and off-chain components; smart contract invariant verification belongs to Blockchain security audits."
                )
        elif "audit" in sl_norm or "web3" in sl_norm or "blockchain" in sl_norm:
            if re.search(r"\b(?:cloud\s+iam\s+pentest|ci/cd\s+pipeline\s+audit|workstation\s+phishing)\b", full_text, re.IGNORECASE):
                errors.append(
                    "Wrong-service claim: Blockchain security audits review smart contract systems, protocol invariants, and token economics; cloud IAM and CI/CD testing belong to Penetration testing."
                )
        elif "tool" in sl_norm:
            if re.search(r"\b(?:x402\s+clearing\s+settlement|payment\s+facilitator\s+escrow)\b", full_text, re.IGNORECASE):
                errors.append(
                    "Wrong-service claim: Agentic security tooling builds custom AI detectors and PR reviewers; payment clearing belongs to Agentic payments."
                )

    # 11. Source-to-claim alignment check
    infra_claims = bool(re.search(r"\b(?:cloud\s+apis?|ci\s+pipelines?|ci/cd|kubernetes|infrastructure\s+exposure)\b", full_text, re.IGNORECASE))
    agent_claims = bool(re.search(r"\b(?:prompt\s+injection|agent\s+wallets?|spending\s+caps?|tool\s+authorization)\b", full_text, re.IGNORECASE))
    payment_claims = bool(re.search(r"\b(?:x402|machine\s+payments\s+protocol|mpp|facilitator\s+trust|payment\s+signaling)\b", full_text, re.IGNORECASE))

    links_in_tweet = re.findall(r"https?://[^\s)]+", full_text)
    for link in links_in_tweet:
        clean_link = link.rstrip(".,;").lower()
        if "simonwillison.net" in clean_link or "genai.owasp.org" in clean_link:
            if infra_claims and not agent_claims:
                errors.append(
                    f"Source-to-claim mismatch: Tweet claims 'cloud APIs and CI pipelines', but cited source '{link}' is an agent-wallet/prompt injection source. Citing source does not support infrastructure/CI claims."
                )
        elif "api-security.owasp.org" in clean_link or "top10.owasp.org" in clean_link:
            if (payment_claims or agent_claims) and not infra_claims:
                errors.append(
                    f"Source-to-claim mismatch: Tweet claims agentic/payment mechanisms, but cited source '{link}' is an infrastructure penetration testing source."
                )
        elif "x402" in clean_link or "stripe.com" in clean_link or "mpp.dev" in clean_link:
            if infra_claims and not payment_claims:
                errors.append(
                    f"Source-to-claim mismatch: Tweet claims infrastructure/CI mechanisms, but cited source '{link}' is an agentic payment protocol source."
                )

    # 12. Technical accuracy & source fidelity checks (SANADSQUAD_V3_FINAL_SOURCE_TRUTH_GATE_01)
    # 12a. Formal verification overstatement check
    if re.search(r"\bformal\s+verification\s+prevents?\b", full_text, re.IGNORECASE):
        errors.append(
            "Technical overstatement: Formal verification evaluates mathematical conformance to formal specifications; "
            "it does not dynamically 'prevent' runtime vulnerabilities or eliminate unmodeled design flaws."
        )

    # 12b. Solana upgrade authority inaccuracy check
    if re.search(r"\benables?\s+unauthorized\s+changes\b", full_text, re.IGNORECASE) or \
       re.search(r"\b(?:upgrade\s+authority|program\s+deployment)\b.*?\bunauthorized\s+changes\b", full_text, re.IGNORECASE):
        errors.append(
            "Technical inaccuracy: Solana upgrade authority allows modifications by the designated keyholder "
            "(a centralization and governance control risk), not 'unauthorized' changes."
        )

    # 12c. Smart contract audits proving code correctness check
    if re.search(r"\b(?:audits?|auditing)\s+(?:proves?|guarantees?)\s+(?:code\s+)?correctness\b|\bproves?\s+(?:code\s+)?correctness\b", full_text, re.IGNORECASE):
        errors.append(
            "Technical overstatement: Smart contract audits evaluate point-in-time code logic and known vulnerability classes; "
            "they do not prove absolute code correctness."
        )

    # 12d. BOLA vs authentication conflation check
    if re.search(r"\b(?:broken\s+object\s+level\s+authorization|bola)\b", full_text, re.IGNORECASE) and \
       re.search(r"\b(?:verify\s+user\s+identity|verifying\s+identity|user\s+identity\s+at\s+every\s+access\s+point)\b", full_text, re.IGNORECASE):
        errors.append(
            "Technical inaccuracy: Broken Object Level Authorization (BOLA) is an authorization failure "
            "(accessing another tenant's resource), distinct from user identity verification (authentication)."
        )

    # 12e. OWASP cryptographic spending caps misattribution check
    if re.search(r"\bowasp\s+(?:genai\s+)?specifies\s+.*?(?:cryptographic\s+policy|spending\s+caps?)\b", full_text, re.IGNORECASE):
        errors.append(
            "Source misattribution: OWASP Agentic Security Initiative defines agent risk taxonomies and "
            "Agent Control Standards (ACS), not specific cryptographic wallet policies or spending caps."
        )

    return errors


def validate_editorial_semantic_conformance(
    tweets: list[str],
    service_line: str | None = None,
    fetched_urls: list[str] | None = None,
    evidence: list[Any] | None = None,
) -> list[str]:
    """Bounded semantic-conformance validation for editorial accuracy, publisher concordance, and service alignment.

    Directive: SANADSQUAD_V3_EDITORIAL_SEMANTIC_CLOSURE_02

    Enforces:
    1. Publisher-URL Concordance:
       - If post attributes claims to OWASP (e.g. 'OWASP Agent Control Standards', 'OWASP ACS', 'OWASP spec'),
         the cited link must resolve to an authentic OWASP domain (owasp.org, genai.owasp.org, api-security.owasp.org),
         NOT a third-party personal blog (e.g. simonwillison.net).
       - If post cites simonwillison.net, it must not describe the linked resource as an OWASP standard or specification.
       - Legitimate sources cannot be described as an official standard of a different organization.
       - Successful HTTP retrieval does not authorize misattributing content to an unrelated publisher.
    2. Epistemic Scope and Stated Certainty:
       - No absolute claims that security controls 'prevent prompt injection' (they restrict unauthorized actions
         and mitigate exploit consequences, but prompt injection remains an active research challenge).
       - No claims stating that all x402 deployments require third-party facilitators (facilitator settlement is optional;
         direct peer-to-peer settlement is supported).
       - No claims that verified builds guarantee application security or prove code correctness (they establish
         source-to-deployment correspondence).
       - No claims that program upgrades automatically bypass all verification.
    3. Meaningful Service Representation:
       - Agentic security tooling must represent SanadSquad's official software offering (custom security detectors,
         automated PR reviewers, or monitoring agents).
       - Security consulting must connect observations to consulting services (architecture review, threat modeling,
         governance design, security requirements, or ongoing development review).
       - Penetration testing must connect observations to dApp APIs, RPC gateways, relayer infrastructure, or off-chain pentesting.
       - Blockchain security audits must connect to smart contract audits, invariant verification, or access control reviews.
       - Agentic payments must represent payment agent architecture, tool authorization limits, or replay protection.
    """
    errors: list[str] = []
    full_text = " ".join(tweets).strip()
    links = [l.rstrip(".,;") for l in re.findall(r"https?://[^\s)]+", full_text)]

    # 1. Publisher-URL Concordance
    has_owasp_claim = bool(re.search(r"\bowasp\b", full_text, re.IGNORECASE))
    has_acs_claim = bool(re.search(r"\b(?:agent\s+control\s+standards?|acs)\b", full_text, re.IGNORECASE))
    has_simon_claim = bool(re.search(r"\bsimon\s+willison\b", full_text, re.IGNORECASE))

    # Reject claiming OWASP specification/standard when URL is non-OWASP
    if re.search(r"\bowasp\s+(?:genai\s+)?(?:specifications?|standards?|docs?|guidance|project)\b", full_text, re.IGNORECASE):
        for link in links:
            if not any(domain in link.lower() for domain in ("owasp.org", "genai.owasp.org")):
                errors.append(
                    f"Publisher attribution mismatch: Post attributes specification/standard to OWASP, "
                    f"but cites non-OWASP resource '{link}'."
                )

    for link in links:
        link_lower = link.lower()
        # Defect 1: Simon Willison URL linked to OWASP / ACS claim
        if "simonwillison.net" in link_lower:
            if has_owasp_claim or (has_acs_claim and not has_simon_claim):
                errors.append(
                    f"Publisher attribution mismatch: Post links to Simon Willison's personal blog ('{link}') "
                    "while attributing the claim or specification to OWASP / Agent Control Standard. "
                    "Simon Willison's article is not an OWASP standard; cite the authentic OWASP ACS standard "
                    "('https://genai.owasp.org/resource/agent-control-standard-acs/') or attribute the research directly to Simon Willison."
                )
            if re.search(r"\b(?:review|read|inspect|check)\s+the\s+spec\b.*?" + re.escape(link), full_text, re.IGNORECASE):
                errors.append(
                    f"Publisher attribution mismatch: Simon Willison's personal blog ('{link}') is an analytical research article, "
                    "not a formal specification. Do not refer to it as 'the spec'."
                )
        elif "genai.owasp.org" in link_lower or "owasp.org" in link_lower:
            if has_simon_claim and not has_owasp_claim:
                errors.append(
                    f"Publisher attribution mismatch: Post cites an OWASP URL ('{link}') while attributing the content to Simon Willison."
                )

        # Canonical x402 upstream check
        if "github.com/coinbase/x402" in link_lower and re.search(r"\bcanonical\s+(?:upstream\s+)?spec\b", full_text, re.IGNORECASE):
            errors.append(
                "Upstream specification mismatch: 'https://github.com/coinbase/x402' is Coinbase's protocol implementation. "
                "The canonical upstream specification repository is 'https://github.com/x402-foundation/x402'."
            )

    # 2. Epistemic Scope & Stated Certainty
    # 2a. Universal Prompt Injection Prevention
    if re.search(r"\b(?:to\s+prevent|prevents?|preventing)\s+prompt\s+injection\b", full_text, re.IGNORECASE):
        errors.append(
            "Overstated certainty: Runtime execution controls restrict tool execution and mitigate exploit blast radius, "
            "but do not universally 'prevent prompt injection'."
        )

    # 2b. Mandatory x402 Facilitator Claim
    if re.search(r"\b(?:all\s+x402\s+(?:deployments\s+)?requires?\s+(?:a\s+)?(?:third-party\s+)?facilitator|mandatory\s+facilitators?|requires?\s+facilitators?\s+for\s+all|facilitators?\s+are\s+mandatory|must\s+use\s+(?:a\s+)?facilitator)\b", full_text, re.IGNORECASE):
        errors.append(
            "Inaccurate x402 requirement: x402 standardizes HTTP 402 payment signaling where facilitator-based verification "
            "and settlement is optional; clients and servers can settle directly peer-to-peer."
        )

    # 2c. Verified Builds Confusing Bytecode Matching with Security
    if re.search(r"\bverified\s+builds?\b.*?\b(?:guarantees?|ensures?|proves?)\s+(?:application\s+security|contract\s+safety|protocol\s+security|security|code\s+safety|safe\s+code|bug-free)\b", full_text, re.IGNORECASE) or \
       re.search(r"\bverified\s+builds?\s+(?:guarantees?|proves?|ensures?)\s+(?:application\s+security|contract\s+safety|security|code\s+safety|safe\s+code|bug-free)\b", full_text, re.IGNORECASE):
        errors.append(
            "Inaccurate verified build claim: Verified builds establish source-to-deployment correspondence "
            "(proving deployed bytecode matches audited Git commit), but do not guarantee application security or functional correctness."
        )

    # 2d. Upgrades Bypassing All Verification
    if re.search(r"\b(?:upgrades?\s+automatically\s+bypass(?:es)?\s+all\s+verification|without\s+(?:community\s+)?verification|alters?\s+code\s+anytime\s+without\s+verification)\b", full_text, re.IGNORECASE):
        errors.append(
            "Inaccurate upgrade authority claim: An upgrade changes the deployed executable and calls for re-verification "
            "of the new version; avoid implying that upgrades automatically bypass all verification."
        )

    # 3. Official SanadSquad Service Alignment
    sl_norm = (service_line or "").lower().strip()
    if sl_norm:
        if "tool" in sl_norm or "agentic-security" in sl_norm:
            has_tooling_mention = bool(re.search(
                r"\b(?:detectors?|pr\s+reviewers?|monitoring\s+agents?|custom\s+(?:security\s+)?tools?|security\s+tooling|security\s+software|automated\s+reviewers?|guardrail\s+tools?|enforcement\s+tooling)\b",
                full_text,
                re.IGNORECASE,
            ))
            if not has_tooling_mention:
                errors.append(
                    "Weak service alignment: Agentic security tooling posts must meaningfully represent SanadSquad's official "
                    "software offering (custom security detectors, automated PR reviewers, or monitoring agents)."
                )

        elif "consulting" in sl_norm:
            has_consulting_mention = bool(re.search(
                r"\b(?:consulting|architecture\s+reviews?|threat\s+model(?:ing)?|governance\s+design|security\s+requirements|ongoing\s+review|pre-implementation\s+review|design\s+reviews?|advisory)\b",
                full_text,
                re.IGNORECASE,
            ))
            if not has_consulting_mention:
                errors.append(
                    "Weak service alignment: Security consulting posts must meaningfully connect observations to consulting "
                    "services (architecture review, threat modeling, governance design, or ongoing development review)."
                )

        elif "pentest" in sl_norm or "penetration" in sl_norm:
            has_pentest_mention = bool(re.search(
                r"\b(?:penetration\s+testing|pentest\w*|dapp\s+apis?|rpc\s+gateways?|relayer|off-chain\s+infrastructure|admin\s+gateways?|backend\s+apis?)\b",
                full_text,
                re.IGNORECASE,
            ))
            if not has_pentest_mention:
                errors.append(
                    "Weak service alignment: Penetration testing posts must meaningfully connect observations to dApp APIs, "
                    "RPC gateways, relayer infrastructure, or off-chain penetration testing."
                )

        elif "audit" in sl_norm or "blockchain" in sl_norm or "web3" in sl_norm:
            has_audit_mention = bool(re.search(
                r"\b(?:audits?|smart\s+contract\s+audits?|invariant\s+verification|protocol\s+invariants?|code\s+review|access\s+control\s+reviews?)\b",
                full_text,
                re.IGNORECASE,
            ))
            if not has_audit_mention:
                errors.append(
                    "Weak service alignment: Blockchain security audit posts must meaningfully represent audit services "
                    "(smart contract audits, invariant verification, or access control reviews)."
                )

        elif "payment" in sl_norm:
            has_payment_mention = bool(re.search(
                r"\b(?:payment|x402|mpp|facilitator|authorization\s+ceilings?|replay\s+protection|settlement)\b",
                full_text,
                re.IGNORECASE,
            ))
            if not has_payment_mention:
                errors.append(
                    "Weak service alignment: Agentic payment posts must meaningfully represent payment agent review, "
                    "tool authorization limits, or replay protection."
                )

    return errors

