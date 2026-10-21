"""End-to-End qualification tests for SanadSquad V3 architecture.

Tests:
1. Full 6-slot fixture run (3 tech threads, 3 marketing posts) with weekly diversity constraints.
2. Independent slot failure isolation.
3. Rejection actionable reason recording.
4. CSV export exact schema ('Post Text,Image').
5. Marketing vulnerability-class exception bounded supplemental KB.
"""
import asyncio
import json
import pytest
from pathlib import Path

from content_pipeline.config import ROOT, load_brand, load_kb, load_registry
from content_pipeline.graph import build_week_graph
from content_pipeline.schemas import (
    Draft,
    MarketingDraft,
    MarketingDraftWithLink,
    TechThreadDraft,
    Plan,
    Slot,
    SlotResult,
    Review,
    Claim,
    ClaimSupport,
)
from content_pipeline.export import export_run
from content_pipeline.marketing_planner import validate_weekly_marketing_results
from content_pipeline.marketing_policy import detect_commercial_cta
from content_pipeline.conformance import ModelConformanceDecision
from content_pipeline.research.service import ResearchService
from content_pipeline.research.provider import FixtureResearchProvider
from content_pipeline.business_policy import load_business_policy
from content_pipeline.proposition_catalog import load_catalog


class V3EndToEndMockModel:
    """Mock model that returns high-quality human-like compliant drafts and reviews."""

    def __init__(self, fail_slot_id: str | None = None):
        self.fail_slot_id = fail_slot_id
        self.active = 0
        self.peak_active = 0
        self.lock = asyncio.Lock()

    async def structured(self, prompt, schema):
        async with self.lock:
            self.active += 1
            self.peak_active = max(self.peak_active, self.active)
            try:
                system = prompt[0].content if isinstance(prompt, list) else str(prompt)
                user_msg = prompt[-1].content if isinstance(prompt, list) else ""

                if self.fail_slot_id and self.fail_slot_id in user_msg:
                    raise RuntimeError(f"Simulated model failure for slot {self.fail_slot_id}")

                if schema in (Draft, TechThreadDraft, MarketingDraft, MarketingDraftWithLink):
                    if "Technical Writer" in system:
                        if '"topic_id": "SWC-105"' in user_msg or '"slot_id": "thread_2"' in user_msg:
                            tweets = [
                                "Due to missing or insufficient access controls, malicious parties can withdraw Ether from the contract account.",
                                "Unprotected withdrawal bugs are sometimes caused by unintentionally exposing contract initialization functions.",
                                "In legacy Solidity versions prior to 0.4.22, wrongly naming a function intended to be a constructor places the code in runtime bytecode where anyone can call it to re-initialize the contract.",
                                "Implement access controls so Ether withdrawals can be initiated only by authorized parties or as specified by the contract.",
                                "Inheriting OpenZeppelin Ownable module provides an onlyOwner modifier to restrict function execution to the authorized owner address.",
                            ]
                        elif '"topic_id": "SCWE-028"' in user_msg or '"slot_id": "thread_3"' in user_msg:
                            tweets = [
                                "Price oracle manipulation refers to exploiting vulnerabilities in price oracles to manipulate contract execution logic.",
                                "Oracle manipulation can lead to unauthorized actions, loss of funds, and exploitation of contract logic.",
                                "Contracts should aggregate multiple oracle and DEX price sources and reject anomalous outlier deviations.",
                                "Use Time-Weighted Average Prices (TWAPs) over sufficient windows and reject stale prices exceeding maximum staleness thresholds.",
                                "Implement fail-safe behaviors that halt sensitive operations like borrowing or liquidations when oracle data is suspicious or unavailable.",
                            ]
                        else:
                            tweets = [
                                "Calling external contracts allows them to take over the execution control flow.",
                                "In a reentrancy attack, an external contract calls back into the caller before the initial invocation completes.",
                                "Recursive callbacks can cause separate function invocations to interact in undesirable ways.",
                                "The Checks-Effects-Interactions pattern recommends performing all internal state changes before external calls are executed.",
                                "Explicitly verify that every external transfer happens only after internal accounting is updated.",
                            ]
                        return TechThreadDraft(tweets=tweets), {"prompt_tokens": 120, "completion_tokens": 80}
                    else:
                        import re
                        m = re.search(r'(?:Mandatory Source URL|Include source link|exact source link|mandatory URL is)[:\s]*[\'"]?(https://[^\s",\']+)', user_msg)
                        m_cta = re.search(r"(?:Include this exact company-approved contact CTA at the end of the tweet|Approved Contact CTA)[:\s]*'([^']+)'", user_msg)
                        cta_suffix = f" {m_cta.group(1)}" if m_cta else ""
                        target_url = m.group(1).rstrip(".,;'\"") if m else None
                        if target_url and ("learning" in user_msg.lower() or "news" in user_msg.lower() or schema == MarketingDraftWithLink):
                            if "x402" in target_url or "stripe" in target_url or "coinbase" in target_url or "payments" in user_msg.lower():
                                tweet = f"Coinbase x402 specification defines HTTP 402 signaling while facilitators verify and settle payments. Breakdown: {target_url}.{cta_suffix}".rstrip(".")
                            elif "simonwillison.net" in target_url or "genai.owasp.org" in target_url or "agent" in user_msg.lower():
                                tweet = f"OWASP reported in their Agentic Security guide how prompt injection reaches tool execution and why spending limits must be enforced outside the model context: {target_url}"
                            elif "top10.owasp.org" in target_url or "api-security" in target_url or "pentest" in user_msg.lower():
                                tweet = f"OWASP guide explains software integrity failures in CI/CD pipelines. Essential breakdown for engineering teams on securing deployment build infrastructure: {target_url}"
                            else:
                                tweet = f"Solana documentation guide explains verified builds proving bytecode matches audited Git commits. Essential breakdown on locking upgrade authority: {target_url}"
                            if schema == MarketingDraftWithLink:
                                return MarketingDraftWithLink(tweets=[tweet], mandatory_link=target_url), {"prompt_tokens": 100, "completion_tokens": 40}
                            return MarketingDraft(tweets=[tweet], mandatory_link=target_url), {"prompt_tokens": 100, "completion_tokens": 40}
                        elif "differentiation" in user_msg.lower():
                            tweet = f"Auditing smart contracts is necessary, but protocols also face infrastructure and frontend risks. SanadSquad audits smart contracts and assesses deployment infrastructure.{cta_suffix}"
                            return MarketingDraft(tweets=[tweet]), {"prompt_tokens": 100, "completion_tokens": 40}
                        else:
                            # Short tip: sharp observation, strictly no link
                            tweet = f"Prompt injection can reach signing tools if policies rely on authentication rather than strict wallet limits. Scope your agent execution budgets tightly.{cta_suffix}"
                            return MarketingDraft(tweets=[tweet]), {"prompt_tokens": 100, "completion_tokens": 40}

                if schema == Review:
                    return Review(
                        factual_support=5,
                        technical_correctness=5,
                        brand_voice=5,
                        clarity=5,
                        platform_format=5,
                        usefulness=5,
                        approved=True,
                        grounding_assessment="Fully grounded in retrieved evidence.",
                        claim_support=[],
                    ), {"prompt_tokens": 80, "completion_tokens": 30}

                if schema == ModelConformanceDecision:
                    return ModelConformanceDecision(
                        verdict="CONFORMS",
                        reason="Realizes planned propositions faithfully without unlicensed claims.",
                        meaning_preserved=True,
                        extra_unlicensed_facts_detected=False,
                        causal_direction_reversed=False,
                        mitigation_overstated_as_guarantee=False,
                        confidence=1.0,
                    ), {"prompt_tokens": 70, "completion_tokens": 25}

                raise ValueError(f"Unexpected schema: {schema}")
            finally:
                self.active -= 1


@pytest.mark.anyio
async def test_v3_full_six_slot_fixture_execution(tmp_path):
    """Full 6-slot weekly execution in V3 fixture research mode."""
    kb = load_kb()
    registry = load_registry()
    brand_text, brand_rules = load_brand()
    catalog = load_catalog(ROOT / "knowledge" / "evidence_first_v2" / "catalog.json")
    policy = load_business_policy(ROOT / "knowledge" / "evidence_first_v2" / "policies" / "security_audit_firm.json")

    res_service = ResearchService()
    model = V3EndToEndMockModel()

    graph, _ = build_week_graph(
        model=model,
        kb=kb,
        registry=registry,
        brand_text=brand_text,
        brand_rules=brand_rules,
        mode="v3",
        catalog=catalog,
        business_policy=policy,
        authorization_mode="publication_eligible",
        research_service=res_service,
    )

    plan = Plan(slots=[
        Slot(id="thread_1", type="tech-thread", focus="reentrancy"),
        Slot(id="post_1", type="marketing-post", focus=None),
        Slot(id="thread_2", type="tech-thread", focus="access control"),
        Slot(id="post_2", type="marketing-post", focus="infrastructure"),
        Slot(id="thread_3", type="tech-thread", focus="oracle manipulation"),
        Slot(id="post_3", type="marketing-post", focus=None),
    ])

    out = await graph.ainvoke({
        "plan": plan,
        "results": [],
        "research_mode": "fixture",
        "authorization_mode": "publication_eligible",
    })

    results = out["results"]
    assert len(results) == 6

    tech_results = [r for r in results if r.slot.type == "tech-thread"]
    marketing_results = [r for r in results if r.slot.type == "marketing-post"]

    assert len(tech_results) == 3
    assert len(marketing_results) == 3

    # All accepted
    for r in results:
        assert r.status == "accepted", f"Slot {r.slot.id} failed: {r.reason}"

    # Verify technical thread constraints (5-10 tweets)
    for r in tech_results:
        tweet_count = len(r.drafts[-1].tweets)
        assert 5 <= tweet_count <= 10, f"Tech thread {r.slot.id} had {tweet_count} tweets"

    # Verify marketing post constraints (exactly 1 tweet, <= 280 chars)
    for r in marketing_results:
        tweet_count = len(r.drafts[-1].tweets)
        assert tweet_count == 1, f"Marketing post {r.slot.id} had {tweet_count} tweets"
        assert len(r.drafts[-1].tweets[0]) <= 280

    # Verify link and no-link diversity across marketing posts
    has_link = [("https://" in r.drafts[-1].tweets[0] or "http://" in r.drafts[-1].tweets[0]) for r in marketing_results]
    assert any(has_link), "At least one marketing post must carry a link"
    assert not all(has_link), "At least one marketing post must have no link"

    # Verify CTA limit (max 1 out of 3)
    cta_count = sum(1 for r in marketing_results if detect_commercial_cta(r.drafts[-1].tweets[0])[0])
    assert cta_count <= 1

    # Verify CSV export format
    export_dir = tmp_path / "v3_e2e_export"
    summary = export_run(export_dir, plan, results, 2.5, "qwen3.5:4b", 1, mode="v3")

    csv_path = export_dir / "posts.csv"
    assert csv_path.exists()
    import csv
    with csv_path.open(encoding="utf-8") as f:
        rows = list(csv.reader(f))
    assert rows[0] == ["Post Text", "Image"]
    assert len(rows) == 7  # Header + 6 accepted posts
    assert summary["shipped"] == 6
    assert summary["failed"] == 0


@pytest.mark.anyio
async def test_v3_independent_slot_failure_isolation(tmp_path):
    """An injected failure in one slot does not fail neighboring slots."""
    kb = load_kb()
    registry = load_registry()
    brand_text, brand_rules = load_brand()
    catalog = load_catalog(ROOT / "knowledge" / "evidence_first_v2" / "catalog.json")
    policy = load_business_policy(ROOT / "knowledge" / "evidence_first_v2" / "policies" / "security_audit_firm.json")

    res_service = ResearchService()
    # Fail slot thread_2
    model = V3EndToEndMockModel(fail_slot_id="thread_2")

    graph, _ = build_week_graph(
        model=model,
        kb=kb,
        registry=registry,
        brand_text=brand_text,
        brand_rules=brand_rules,
        mode="v3",
        catalog=catalog,
        business_policy=policy,
        authorization_mode="publication_eligible",
        research_service=res_service,
    )

    plan = Plan(slots=[
        Slot(id="thread_1", type="tech-thread", focus="reentrancy"),
        Slot(id="thread_2", type="tech-thread", focus="access control"),
        Slot(id="post_1", type="marketing-post", focus=None),
    ])

    out = await graph.ainvoke({
        "plan": plan,
        "results": [],
        "research_mode": "fixture",
        "authorization_mode": "publication_eligible",
    })

    results = {r.slot.id: r for r in out["results"]}
    assert results["thread_1"].status == "accepted"
    assert results["thread_2"].status == "failed"
    assert results["post_1"].status == "accepted"

    export_dir = tmp_path / "v3_isolation_export"
    summary = export_run(export_dir, plan, list(results.values()), 1.5, "qwen3.5:4b", 1, mode="v3")
    assert summary["shipped"] == 2
    assert summary["failed"] == 1


@pytest.mark.anyio
async def test_v3_rejection_records_actionable_reason():
    """Deterministic validation failures record specific actionable rejection reasons."""
    kb = load_kb()
    registry = load_registry()
    brand_text, brand_rules = load_brand()
    catalog = load_catalog(ROOT / "knowledge" / "evidence_first_v2" / "catalog.json")
    policy = load_business_policy(ROOT / "knowledge" / "evidence_first_v2" / "policies" / "security_audit_firm.json")

    class BadWritingModel:
        def __init__(self):
            self.peak_active = 1
        async def structured(self, prompt, schema):
            if schema in (Draft, MarketingDraft):
                return MarketingDraft(tweets=["In today's fast-paced world, we leverage robust AI—guaranteed 100% secure! 🚀"]), {"prompt_tokens": 10, "completion_tokens": 10}
            if schema == Review:
                return Review(
                    factual_support=5, technical_correctness=5, brand_voice=5, clarity=5,
                    platform_format=5, usefulness=5, approved=True, grounding_assessment="ok", claim_support=[]
                ), {"prompt_tokens": 10, "completion_tokens": 10}
            raise ValueError(f"Unexpected schema: {schema}")

    res_service = ResearchService()
    graph, _ = build_week_graph(
        model=BadWritingModel(),
        kb=kb,
        registry=registry,
        brand_text=brand_text,
        brand_rules=brand_rules,
        mode="v3",
        catalog=catalog,
        business_policy=policy,
        authorization_mode="publication_eligible",
        research_service=res_service,
    )

    plan = Plan(slots=[Slot(id="post_bad", type="marketing-post", focus=None)])
    out = await graph.ainvoke({
        "plan": plan,
        "results": [],
        "research_mode": "fixture",
        "authorization_mode": "publication_eligible",
    })

    result = out["results"][0]
    assert result.status in ("dropped", "failed")
    assert any("leverage" in reason or "banned vocabulary" in reason or "filler" in reason for reason in result.validations[0])


@pytest.mark.anyio
async def test_three_post_marketing_sample_demonstration(tmp_path, monkeypatch):
    """Demonstrate complete 3-post marketing run meeting Directive SANADSQUAD_V3_CONTACT_CTA_CLOSURE_01.
    
    Demonstrates:
    - Exactly ONE post with a contextual business CTA, approved email and phone.
    - Exactly TWO posts without commercial CTAs.
    - Valid evidence, correct formats, weekly diversity, and clean CSV export ('Post Text,Image').
    - Every post strictly within 280 characters.
    """
    import csv
    from content_pipeline.contact_config import CompanyContactConfig

    approved_cfg = CompanyContactConfig(
        company_name="SanadSquad",
        business_inquiries_email="frank@sanadsquad.com",
        business_phone_number=None,
        contact_form_url="https://sanadsquad.com/contact/",
        telegram="@castle_chain",
        x_handle="@SanadSquad",
        official_website="https://sanadsquad.com",
        approved=True,
        status="APPROVED",
    )
    monkeypatch.setattr(
        "content_pipeline.contact_config.load_company_contact",
        lambda *args, **kwargs: approved_cfg,
    )
    monkeypatch.setattr(
        "content_pipeline.marketing_policy.load_company_contact",
        lambda *args, **kwargs: approved_cfg,
    )

    kb = load_kb()
    registry = load_registry()
    brand_text, brand_rules = load_brand()
    catalog = load_catalog(ROOT / "knowledge" / "evidence_first_v2" / "catalog.json")
    policy = load_business_policy(ROOT / "knowledge" / "evidence_first_v2" / "policies" / "security_audit_firm.json")
    res_service = ResearchService()

    model = V3EndToEndMockModel()
    graph, _ = build_week_graph(
        model=model,
        kb=kb,
        registry=registry,
        brand_text=brand_text,
        brand_rules=brand_rules,
        mode="v3",
        catalog=catalog,
        business_policy=policy,
        authorization_mode="pilot_evaluation",
        research_service=res_service,
    )

    # 3 weekly marketing slots
    slots = [
        Slot(id="post_1", type="marketing-post", focus="post-audit deployment drift"),
        Slot(id="post_2", type="marketing-post", focus="AI agent prompt injection"),
        Slot(id="post_3", type="marketing-post", focus="x402 versus MPP settlement mechanics"),
    ]
    plan = Plan(slots=slots)

    out = await graph.ainvoke({
        "plan": plan,
        "results": [],
        "research_mode": "fixture",
        "authorization_mode": "pilot_evaluation",
    })

    results = out["results"]
    assert len(results) == 3
    assert all(r.status == "accepted" for r in results)

    # Export to clean CSV
    export_dir = tmp_path / "marketing_demo"
    summary = export_run(
        output=export_dir,
        plan=plan,
        results=results,
        elapsed=2.5,
        model_name="mock_v3_contact",
        peak_active=1,
        mode="v3",
    )
    assert summary["shipped"] == 3

    # Inspect the actual exported posts.csv
    csv_file = export_dir / "posts.csv"
    assert csv_file.exists()
    with csv_file.open("r", encoding="utf-8") as f:
        reader = list(csv.reader(f))

    assert reader[0] == ["Post Text", "Image"]
    assert len(reader) == 4  # Header + 3 posts

    post_texts = [row[0] for row in reader[1:]]

    # Verify character length limit on all posts
    for idx, text in enumerate(post_texts, 1):
        assert len(text) <= 280, f"Post {idx} exceeds 280 characters: {len(text)}"

    # Post 1 (Differentiation): No CTA, approved positioning
    assert "SanadSquad audits smart contracts" in post_texts[0]
    assert "contact@sanadsquad.com" not in post_texts[0]
    assert "+1-555-0199" not in post_texts[0]

    # Post 2 (News Reaction): Has link, No CTA, grounded in agentic security
    assert "https://" in post_texts[1]
    assert "OWASP reported" in post_texts[1]
    assert "contact@sanadsquad.com" not in post_texts[1]
    assert "+1-555-0199" not in post_texts[1]

    # Post 3 (Learning Resource): Contextual CTA + email
    assert "Coinbase x402 specification defines HTTP 402 signaling" in post_texts[2]
    assert "facilitators verify and settle" in post_texts[2]
    assert "Building a payment agent? SanadSquad reviews authorization and facilitator integrations." in post_texts[2]
    assert "Email: frank@sanadsquad.com" in post_texts[2]
    assert "+1-555-0199" not in post_texts[2]
    assert "contact@sanadsquad.com" not in post_texts[2]

    # Verify weekly mix: exactly 1 CTA across 3 marketing posts
    weekly_errors = validate_weekly_marketing_results(results)
    assert weekly_errors == []

