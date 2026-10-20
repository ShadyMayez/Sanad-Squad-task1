"""Tests for Phase 4 Weekly Marketing Planner and Diversity Constraints.

Enforces:
- Six-slot plan (3 tech-threads, 3 marketing-posts).
- Service line diversity: no service line duplicated among marketing slots.
- Link diversity: >= 1 with link, >= 1 with no link.
- Format diversity: formats differ, no format appearing > 2 times.
- CTA policy: <= 1/3 of marketing posts have commercial CTAs (max 1 for 3 slots).
- Per-post CTA limit: max 1 per post.
- Topic deduplication: normalized token fingerprint catches and blocks collision.
- Final export validation: validate_weekly_marketing_results verifies constraints.
"""
from __future__ import annotations

import pytest
from content_pipeline.marketing_format import MarketingFormat
from content_pipeline.marketing_planner import (
    MarketingSlotMetadata,
    WeeklyMarketingPlan,
    MarketingSlotPlanner,
    compute_topic_fingerprint,
    validate_weekly_marketing_results,
)
from content_pipeline.schemas import Slot, SlotResult, Draft, Evidence


def test_weekly_marketing_plan_valid():
    """Compliant weekly marketing plan passes all constraint checks."""
    plan = WeeklyMarketingPlan(slots=[
        MarketingSlotMetadata(
            slot_id="post_1",
            service_line="web3-security",
            research_angle="deployment drift",
            selected_format=MarketingFormat.DIFFERENTIATION,
            requires_link=False,
            forbids_link=False,
            has_cta=False,
            topic_fingerprint="web3_drift_invariants",
        ),
        MarketingSlotMetadata(
            slot_id="post_2",
            service_line="agentic-security",
            research_angle="prompt injection",
            selected_format=MarketingFormat.NEWS_REACTION,
            requires_link=True,
            forbids_link=False,
            has_cta=False,
            topic_fingerprint="agent_prompt_injection",
        ),
        MarketingSlotMetadata(
            slot_id="post_3",
            service_line="agentic-payments",
            research_angle="x402 settlement",
            selected_format=MarketingFormat.LEARNING_RESOURCE,
            requires_link=True,
            forbids_link=False,
            has_cta=True,
            topic_fingerprint="x402_mpp_settlement",
        ),
    ])
    errors = plan.validate_constraints()
    assert errors == []


def test_duplicate_service_line_rejected():
    """Duplicate service line in weekly marketing plan triggers constraint violation."""
    plan = WeeklyMarketingPlan(slots=[
        MarketingSlotMetadata(
            slot_id="post_1",
            service_line="web3-security",
            research_angle="invariants",
            selected_format=MarketingFormat.SHORT_TIP,
            requires_link=False,
            forbids_link=True,
            has_cta=False,
            topic_fingerprint="fp1",
        ),
        MarketingSlotMetadata(
            slot_id="post_2",
            service_line="web3-security",  # DUPLICATE
            research_angle="reentrancy",
            selected_format=MarketingFormat.NEWS_REACTION,
            requires_link=True,
            forbids_link=False,
            has_cta=False,
            topic_fingerprint="fp2",
        ),
    ])
    errors = plan.validate_constraints()
    assert any("duplicate service lines" in e for e in errors)


def test_missing_link_diversity_rejected():
    """Plan where all posts lack links fails link diversity rule."""
    plan = WeeklyMarketingPlan(slots=[
        MarketingSlotMetadata(
            slot_id="post_1",
            service_line="web3-security",
            research_angle="invariants",
            selected_format=MarketingFormat.SHORT_TIP,
            requires_link=False,
            forbids_link=True,
            has_cta=False,
            topic_fingerprint="fp1",
        ),
        MarketingSlotMetadata(
            slot_id="post_2",
            service_line="pentesting",
            research_angle="infrastructure",
            selected_format=MarketingFormat.SHORT_TIP,
            requires_link=False,
            forbids_link=True,
            has_cta=False,
            topic_fingerprint="fp2",
        ),
    ])
    errors = plan.validate_constraints()
    assert any("at least 1 marketing post must require a source link" in e for e in errors)


def test_excessive_ctas_rejected():
    """Plan where > 1/3 posts contain commercial CTAs fails CTA rule."""
    plan = WeeklyMarketingPlan(slots=[
        MarketingSlotMetadata(
            slot_id="post_1",
            service_line="web3-security",
            research_angle="invariants",
            selected_format=MarketingFormat.SHORT_TIP,
            requires_link=False,
            forbids_link=True,
            has_cta=True,  # CTA 1
            topic_fingerprint="fp1",
        ),
        MarketingSlotMetadata(
            slot_id="post_2",
            service_line="agentic-security",
            research_angle="prompt injection",
            selected_format=MarketingFormat.NEWS_REACTION,
            requires_link=True,
            forbids_link=False,
            has_cta=True,  # CTA 2 (2 out of 3 = 66% > 33%)
            topic_fingerprint="fp2",
        ),
        MarketingSlotMetadata(
            slot_id="post_3",
            service_line="agentic-payments",
            research_angle="settlement",
            selected_format=MarketingFormat.LEARNING_RESOURCE,
            requires_link=True,
            forbids_link=False,
            has_cta=False,
            topic_fingerprint="fp3",
        ),
    ])
    errors = plan.validate_constraints()
    assert any("posts contain CTAs (max allowed is 1" in e for e in errors)


def test_topic_similarity_fingerprint_deduplication():
    """Topic fingerprinting catches semantic and token collisions."""
    fp1 = compute_topic_fingerprint("web3 security runtime invariant testing on svm")
    fp2 = compute_topic_fingerprint("runtime invariant testing for web3 contracts")
    # Meaningful overlapping tokens produce collision or identical key tokens
    tokens1 = set(fp1.split("_"))
    tokens2 = set(fp2.split("_"))
    shared = tokens1.intersection(tokens2)
    assert len(shared) >= 3


def test_marketing_slot_planner_generates_coordinated_plan():
    """MarketingSlotPlanner assigns non-colliding service lines, formats, and link requirements."""
    slots = [
        Slot(id="thread_1", type="tech-thread", focus="reentrancy"),
        Slot(id="post_1", type="marketing-post"),
        Slot(id="thread_2", type="tech-thread", focus="oracle"),
        Slot(id="post_2", type="marketing-post"),
        Slot(id="thread_3", type="tech-thread", focus="access-control"),
        Slot(id="post_3", type="marketing-post"),
    ]
    plan = MarketingSlotPlanner.plan_weekly_slots(slots)
    assert len(plan.slots) == 3
    # Check distinct service lines
    service_lines = [s.service_line for s in plan.slots]
    assert len(service_lines) == len(set(service_lines))
    # Check link requirements (at least 1 requires link, at least 1 does not)
    assert any(s.requires_link for s in plan.slots)
    assert any(not s.requires_link for s in plan.slots)
    # Check CTA cap
    assert sum(1 for s in plan.slots if s.has_cta) <= 1


def test_validate_weekly_marketing_results():
    """validate_weekly_marketing_results checks accepted results at export."""
    res1 = SlotResult(
        slot=Slot(id="p1", type="marketing-post"),
        status="accepted",
        drafts=[Draft(tweets=["One sharp observation on runtime invariant testing with no link."])],
        evidence=[Evidence(id="ev1", url="https://trailofbits.com/invariants", excerpt="Valid evidence excerpt text over twelve characters.", source_title="Trail of Bits", source_type="web", scope="service_line:web3-security")],
    )
    res2 = SlotResult(
        slot=Slot(id="p2", type="marketing-post"),
        status="accepted",
        drafts=[Draft(tweets=["AI prompt injection bypassed signing authorization: https://genai.owasp.org/incident"])],
        evidence=[Evidence(id="ev2", url="https://genai.owasp.org/incident", excerpt="Another valid evidence excerpt over twelve characters.", source_title="OWASP GenAI", source_type="web", scope="service_line:agentic-security")],
    )
    errors = validate_weekly_marketing_results([res1, res2])
    assert errors == []
