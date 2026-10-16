"""Independent deterministic controls around the real semantic model judgment."""
from __future__ import annotations

import asyncio
import hashlib
from pathlib import Path

from content_pipeline.claim_extraction import extract_claims
from content_pipeline.config import load_kb
from content_pipeline.provenance import evidence_errors, knowledge_base_errors
from content_pipeline.schemas import AtomicClaim, Claim, Draft, SemanticReport, SemanticVerdict, SupportingSpan, ModelSemanticDecision
from content_pipeline.semantic_verification import SemanticVerifier
from content_pipeline.text_spans import sentence_matches, source_span_options
from tests.relation_helpers import relation_fields


def test_pinned_provenance_and_tamper_detection(tmp_path):
    kb = load_kb()
    assert not knowledge_base_errors(kb)
    assert len({e.id for topic in kb.vulnerabilities for e in topic.evidence}) >= 17
    item = kb.vulnerabilities[0].evidence[0]
    assert not evidence_errors(item)
    assert any("hash mismatch" in e for e in evidence_errors(item.model_copy(update={"snapshot_sha256": "0" * 64})))
    assert any("quote" in e for e in evidence_errors(item.model_copy(update={"source_quote": "invented quote"})))
    assert any("unavailable" in e for e in evidence_errors(item.model_copy(update={"snapshot_path": "source_snapshots/missing.txt"})))
    assert any("escapes" in e for e in evidence_errors(item.model_copy(update={"snapshot_path": "../outside.txt"})))


def test_abbreviations_and_source_bullets_remain_complete_exact_spans():
    quote = load_kb().vulnerabilities[0].evidence[0].source_quote
    options = source_span_options(quote)
    assert all(option in quote for option in options)
    lock = "Use a reentrancy lock (ie. OpenZeppelin's ReentrancyGuard)."
    assert lock in options
    assert "This is known as the Checks-Effects-Interactions pattern" in options
    assert [lock[m.start():m.end()] for m in sentence_matches(lock)] == [lock]
    draft = Draft(tweets=[lock], claims=[Claim(text=lock, evidence_ids=["SWC-107"])])
    claims, errors = extract_claims(draft, load_kb().vulnerabilities[0].evidence)
    assert not errors and len(claims) == 1 and claims[0].span == lock


def test_atomic_extraction_preserves_universal_clause_and_covers_text():
    evidence = load_kb().vulnerabilities[0].evidence
    text = "An external contract can take control, and a lock always eliminates every risk."
    draft = Draft(tweets=[text], claims=[Claim(text=text, evidence_ids=["SWC-107"])])
    claims, errors = extract_claims(draft, evidence)
    assert not errors
    assert len(claims) == 2
    assert "always" in claims[1].proposition and "every" in claims[1].qualifiers
    assert all(text[c.start:c.end] == c.span == c.proposition for c in claims)
    claims, errors = extract_claims(Draft(tweets=[text], claims=[]), evidence)
    assert not claims and any("no Writer evidence mapping" in e for e in errors)


def test_atomic_extraction_retains_negation_number_and_condition():
    evidence = load_kb().vulnerabilities[0].evidence
    text = "If 500 contracts are audited, no callback can ever occur."
    draft = Draft(tweets=[text], claims=[Claim(text=text, evidence_ids=["SWC-107"])])
    claims, errors = extract_claims(draft, evidence)
    assert not errors and len(claims) == 1
    assert {"If", "500", "no", "can"}.issubset(set(claims[0].qualifiers))


def test_semantic_verifier_rejects_forged_quote_and_missing_verdict():
    item = load_kb().vulnerabilities[0].evidence[0]
    claim = AtomicClaim(id="x", tweet_index=0, start=0, end=20, span="External calls recur.",
        proposition="External calls recur.", sentence="External calls recur.", candidate_evidence_ids=[item.id])

    class Fake:
        def __init__(self, quote, omit=False):
            self.quote = quote
            self.omit = omit

        async def structured(self, prompt, schema):
            if self.omit:
                return {"missing_verdict": True}, {"input_tokens": 1, "output_tokens": 1}
            chosen = "SWC-107#0" if self.quote in item.source_quote else "SWC-107#999"
            return ModelSemanticDecision(verdict="SUPPORTED", support_option_ids=[chosen],
                reason="Mock positive judgment", **relation_fields()), {"input_tokens": 1, "output_tokens": 1}

    valid = asyncio.run(SemanticVerifier(Fake(item.source_quote[:35])).run([claim], [item]))[0]
    assert valid.verdicts[0].verdict == "SUPPORTED"
    forged = asyncio.run(SemanticVerifier(Fake("fabricated quote outside pinned source")).run([claim], [item]))[0]
    assert forged.verdicts[0].verdict == "VERIFICATION_ERROR"
    omitted = asyncio.run(SemanticVerifier(Fake("", omit=True)).run([claim], [item]))[0]
    assert omitted.verdicts[0].verdict == "VERIFICATION_ERROR"


def test_verifier_resolves_only_real_pinned_span_options():
    item = load_kb().vulnerabilities[0].evidence[0]
    claim = AtomicClaim(id="x", tweet_index=0, start=0, end=20, span="External calls recur.",
        proposition="External calls recur.", sentence="External calls recur.", candidate_evidence_ids=[item.id])

    class Select:
        def __init__(self, chosen):
            self.chosen = chosen

        async def structured(self, messages, schema):
            return ModelSemanticDecision(verdict="SUPPORTED", support_option_ids=[self.chosen],
                reason="Exact option chosen", **relation_fields()), {"input_tokens": 2, "output_tokens": 2}

    good = asyncio.run(SemanticVerifier(Select("SWC-107#0")).run([claim], [item]))[0].verdicts[0]
    assert good.verdict == "SUPPORTED" and good.supporting_spans[0].quote in item.source_quote
    bad = asyncio.run(SemanticVerifier(Select("SWC-107#999")).run([claim], [item]))[0].verdicts[0]
    assert bad.verdict == "VERIFICATION_ERROR"


def test_independent_skeptical_pass_vetoes_tentative_support():
    item = load_kb().vulnerabilities[0].evidence[0]
    sentence = "A reentrancy lock prevents the external callee from gaining control flow."
    claim = AtomicClaim(id="overclaim", tweet_index=0, start=0, end=len(sentence),
        span=sentence, proposition=sentence, sentence=sentence, candidate_evidence_ids=[item.id])

    class TwoPass:
        calls = 0

        async def structured(self, messages, schema):
            self.calls += 1
            if self.calls == 1:
                return ModelSemanticDecision(verdict="SUPPORTED", support_option_ids=["SWC-107#4", "SWC-107#5"],
                    reason="Tentative support from remediation words", **relation_fields()), {"input_tokens": 3, "output_tokens": 4}
            return ModelSemanticDecision(verdict="INSUFFICIENT_EVIDENCE", reason="Selected spans do not say the callee loses control",
                **relation_fields("INSUFFICIENT_EVIDENCE")), {"input_tokens": 5, "output_tokens": 6}

    model = TwoPass()
    report, usage, _ = asyncio.run(SemanticVerifier(model).run([claim], [item]))
    assert model.calls == 2
    assert report.verdicts[0].verdict == "INSUFFICIENT_EVIDENCE"
    assert report.verdicts[0].supporting_spans == []
    assert usage["input_tokens"] == 8 and usage["output_tokens"] == 10


def test_semantic_verifier_distinguishes_missing_evidence_from_model_uncertainty():
    item = load_kb().vulnerabilities[0].evidence[0]
    claim = AtomicClaim(id="x", tweet_index=0, start=0, end=10, span="A claim.",
        proposition="A claim.", sentence="A claim.", candidate_evidence_ids=["MISSING"])

    class NeverCall:
        async def structured(self, prompt, schema):
            raise AssertionError("model must not run on unresolved source")

    report = asyncio.run(SemanticVerifier(NeverCall()).run([claim], [item]))[0]
    assert report.verdicts[0].verdict == "VERIFICATION_ERROR"
    assert "Missing evidence IDs" in report.verdicts[0].reason


def test_source_disappearance_isolated_after_research(monkeypatch):
    from content_pipeline import graph as graph_module
    from content_pipeline.config import load_brand, load_registry
    from content_pipeline.graph import build_week_graph
    from content_pipeline.schemas import Draft, Plan, Review, ClaimSupport, Slot
    from tests.test_pipeline import FakeModel

    original = graph_module.evidence_errors
    monkeypatch.setattr(graph_module, "evidence_errors", lambda e: ["SWC-107: missing pinned source"] if e.id == "SWC-107" else original(e))
    text, rules = load_brand()
    app, _ = build_week_graph(FakeModel(), load_kb(), load_registry(), text, rules)
    plan = Plan(slots=[Slot(id="broken", type="marketing-post", focus="reentrancy"),
                       Slot(id="healthy", type="marketing-post", focus="oracle manipulation")])
    results = asyncio.run(app.ainvoke({"plan": plan, "results": []}))["results"]
    assert {r.slot.id: r.status for r in results} == {"broken": "failed", "healthy": "accepted"}
    assert all(r.visual_spec is None for r in results if r.slot.id == "broken")


def test_missing_pinned_source_fails_only_selected_slot():
    from content_pipeline.config import load_brand, load_registry
    from content_pipeline.graph import build_week_graph
    from content_pipeline.schemas import Plan, Slot
    from tests.test_pipeline import FakeModel

    kb = load_kb().model_copy(deep=True)
    kb.vulnerabilities[0].evidence[0].snapshot_path = "source_snapshots/does-not-exist.txt"
    text, rules = load_brand()
    app, _ = build_week_graph(FakeModel(), kb, load_registry(), text, rules)
    plan = Plan(slots=[Slot(id="missing_source", type="marketing-post", focus="reentrancy"),
        Slot(id="healthy", type="marketing-post", focus="oracle manipulation")])
    results = asyncio.run(app.ainvoke({"plan": plan, "results": []}))["results"]
    assert {r.slot.id: r.status for r in results} == {"missing_source": "failed", "healthy": "accepted"}
    assert "Source provenance failed" in next(r.reason for r in results if r.slot.id == "missing_source")


def test_verifier_transport_or_schema_failure_does_not_spend_content_revision():
    from content_pipeline.config import load_brand, load_registry
    from content_pipeline.graph import build_week_graph
    from content_pipeline.schemas import Plan, Slot
    from tests.test_pipeline import FakeModel

    class BrokenVerifier(FakeModel):
        async def structured(self, messages, schema):
            if schema is ModelSemanticDecision:
                raise TimeoutError("injected verifier timeout")
            return await super().structured(messages, schema)

    text, rules = load_brand()
    app, _ = build_week_graph(BrokenVerifier(), load_kb(), load_registry(), text, rules)
    result = asyncio.run(app.ainvoke({"plan": Plan(slots=[Slot(id="piece", type="marketing-post", focus="reentrancy")]),
        "results": []}))["results"][0]
    assert result.status == "failed" and len(result.drafts) == 1 and not result.reviews
    assert "Semantic verifier failed" in result.reason


def test_export_rechecks_exact_claim_ids_and_real_selected_spans(tmp_path):
    import pytest
    from content_pipeline.export import export_run
    from content_pipeline.schemas import Plan, Slot
    from tests.test_pipeline import FakeModel, run_plan

    plan = Plan(slots=[Slot(id="piece", type="marketing-post", focus="reentrancy")])
    results, _ = run_plan(plan, FakeModel())
    assert results[0].status == "accepted"
    forged = results[0].model_copy(deep=True)
    forged.semantic_reports[-1].verdicts[0].supporting_spans[0].quote = "fabricated quote"
    with pytest.raises(ValueError, match="final grounding"):
        export_run(tmp_path / "forged", plan, [forged], 0.1, "fake", 1)
    assert not (tmp_path / "forged").exists()
    mismatched = results[0].model_copy(deep=True)
    mismatched.semantic_reports[-1].verdicts[0].claim_id = "wrong-claim"
    with pytest.raises(ValueError, match="final grounding"):
        export_run(tmp_path / "mismatch", plan, [mismatched], 0.1, "fake", 1)
    forged_option = results[0].model_copy(deep=True)
    forged_option.semantic_reports[-1].verdicts[0].supporting_span_ids[0] = "SWC-107#999"
    with pytest.raises(ValueError, match="final grounding"):
        export_run(tmp_path / "forged-option", plan, [forged_option], 0.1, "fake", 1)
