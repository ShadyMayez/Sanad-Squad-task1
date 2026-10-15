import asyncio
import csv
import json
from pathlib import Path

import pytest
from pydantic import ValidationError

from content_pipeline.config import ROOT, load_brand, load_kb, load_plan, load_registry
from content_pipeline.export import export_run
from content_pipeline.graph import build_week_graph
from content_pipeline.schemas import Claim, ClaimSupport, Draft, Evidence, KnowledgeBase, Plan, Review, Slot, WriterConfig, SemanticReport, SemanticVerdict, SupportingSpan, ModelSemanticDecision
from content_pipeline.skills import EvidenceLookup
from content_pipeline.validation import validate_draft
from content_pipeline.cli import week_main, piece_main
from content_pipeline.llm import LocalModel


class FakeModel:
    def __init__(self, reject_first=False, reject_always=False, fail_topic=None, invalid_draft=False, invalid_quote=False, low_score=False, omit_quote=False):
        self.reject_first = reject_first
        self.reject_always = reject_always
        self.fail_topic = fail_topic
        self.invalid_draft = invalid_draft
        self.invalid_quote = invalid_quote
        self.low_score = low_score
        self.omit_quote = omit_quote
        self.review_calls = 0
        self.active = 0
        self.peak_active = 0
        self.lock = asyncio.Semaphore(1)

    async def structured(self, prompt, schema):
        async with self.lock:
            self.active += 1
            self.peak_active = max(self.peak_active, self.active)
            await asyncio.sleep(0.001)
            try:
                task = json.loads(prompt[-1].content) if isinstance(prompt, list) else {}
                system = prompt[0].content if isinstance(prompt, list) else str(prompt)
                if self.fail_topic and self.fail_topic in json.dumps(task):
                    raise TimeoutError("injected source/model failure")
                if schema is Draft:
                    evidence_id = "SCWE-028" if "SCWE-028" in json.dumps(task) else "SWC-107"
                    count = 5 if "Technical Writer" in system else 1
                    tweets = [f"Review the source-backed contract behavior point {i}." for i in range(count)]
                    if self.invalid_draft:
                        tweets[0] += " #forbidden"
                    return Draft(tweets=tweets, claims=[Claim(text=t, evidence_ids=[evidence_id]) for t in tweets]), {"input_tokens": 10, "output_tokens": 20}
                if schema is Review:
                    self.review_calls += 1
                    reject = self.reject_always or (self.reject_first and self.review_calls == 1)
                    draft_data = task["draft"]
                    evidence_data = task["evidence"]
                    excerpts = {e["id"]: e["source_quote"] for e in evidence_data}
                    supports = [ClaimSupport(claim_text=c["text"], evidence_id=c["evidence_ids"][0],
                        evidence_quote="fabricated supporting text" if self.invalid_quote else excerpts[c["evidence_ids"][0]][:35], supported=True) for c in draft_data["claims"]]
                    if self.omit_quote:
                        supports = []
                    return Review(factual_support=2 if self.low_score else 5, technical_correctness=5, brand_voice=5, clarity=2 if reject else 5,
                        platform_format=5, usefulness=5, approved=not reject,
                        reasons=["Revise clarity"] if reject else [], corrections=["Use simpler language"] if reject else [],
                        grounding_assessment="Evidence matches the text", claim_support=supports), {"input_tokens": 8, "output_tokens": 9}
                if schema is ModelSemanticDecision:
                    return ModelSemanticDecision(verdict="SUPPORTED", support_option_ids=[task["exact_span_options"][0]["span_id"]],
                        reason="Mocked positive semantic decision"), {"input_tokens": 6, "output_tokens": 7}
                raise AssertionError(schema)
            finally:
                self.active -= 1


def components():
    brand_text, brand = load_brand()
    return load_kb(), load_registry(), brand_text, brand


def run_plan(plan, model):
    kb, registry, brand_text, brand = components()
    graph, lookup = build_week_graph(model, kb, registry, brand_text, brand)
    result = asyncio.run(graph.ainvoke({"plan": plan, "results": []}))
    return result["results"], lookup


def test_input_contracts_and_topic_selection():
    kb, registry, _, _ = components()
    plan = load_plan(ROOT / "plan.json", registry)
    assert len(plan.slots) == 6
    assert sum(s.type == "tech-thread" for s in plan.slots) == 3
    lookup = EvidenceLookup(kb)
    assert lookup.select(None, 0).id == kb.vulnerabilities[0].id
    assert lookup.select("oracle manipulation", 0).id == "SCWE-028"
    with pytest.raises(ValueError, match="No grounded"):
        lookup.select("unrelated astrophysics", 0)
    with pytest.raises(ValueError, match="No grounded"):
        lookup.select("smart contract astrology", 0)
    with pytest.raises(ValidationError):
        KnowledgeBase(vulnerabilities=kb.vulnerabilities[:14])
    with pytest.raises(ValidationError):
        Plan(slots=[Slot(id="same", type="tech-thread"), Slot(id="same", type="tech-thread")])


def test_unapproved_company_number_is_a_hard_rule():
    kb, registry, _, brand = components()
    topic = kb.vulnerabilities[0]
    text = "SanadSquad audited 500 protocols."
    draft = Draft(tweets=[text], claims=[Claim(text=text, evidence_ids=[topic.evidence[0].id])])
    errors = validate_draft(draft, registry.types["marketing-post"], brand, topic.evidence, EvidenceLookup(kb))
    assert any("unapproved company statistic" in error for error in errors)
    approved = brand.model_copy(update={"approved_statistics": [text]})
    errors = validate_draft(draft, registry.types["marketing-post"], approved, topic.evidence, EvidenceLookup(kb))
    assert not any("unapproved company statistic" in error for error in errors)


def test_weekly_plan_shape(tmp_path):
    registry = load_registry()
    path = tmp_path / "short.json"
    path.write_text(json.dumps({"slots": [{"id": "one", "type": "tech-thread", "focus": None}]}))
    with pytest.raises(ValueError, match="six slots"):
        load_plan(path, registry)
    path.write_text(json.dumps({"slots": [{"id": f"s_{i}", "type": "tech-thread"} for i in range(6)]}))
    with pytest.raises(ValueError, match="three tech-thread"):
        load_plan(path, registry)


def test_rules_and_claim_ids():
    kb, registry, _, brand = components()
    evidence = kb.vulnerabilities[0].evidence
    lookup = EvidenceLookup(kb)
    spec = registry.types["marketing-post"]
    tweet = "A revolutionary #audit — https://bad.example"
    draft = Draft(tweets=[tweet], claims=[Claim(text=tweet, evidence_ids=["FAKE"])])
    errors = validate_draft(draft, spec, brand, evidence, lookup)
    assert any("hashtag" in e for e in errors)
    assert any("banned character" in e for e in errors)
    assert any("banned phrase" in e for e in errors)
    assert any("unapproved link" in e for e in errors)
    assert any("unknown evidence" in e for e in errors)
    long = "x" * 281
    errors = validate_draft(Draft(tweets=[long], claims=[Claim(text=long, evidence_ids=[evidence[0].id])]), spec, brand, evidence, lookup)
    assert any("exceeds" in e for e in errors)


def test_sentence_level_claim_coverage():
    kb, registry, _, brand = components()
    evidence = kb.vulnerabilities[0].evidence
    lookup = EvidenceLookup(kb)
    first = "External calls can transfer control."
    second = "Review state changes before external calls."
    draft = Draft(tweets=[first + " " + second], claims=[
        Claim(text=first, evidence_ids=["SWC-107"]),
        Claim(text=second, evidence_ids=["SWC-107"]),
    ])
    assert validate_draft(draft, registry.types["marketing-post"], brand, evidence, lookup) == []
    draft.claims.pop()
    assert any("unmapped sentence" in e for e in validate_draft(draft, registry.types["marketing-post"], brand, evidence, lookup))


def test_thread_numbering_counts_toward_character_limit():
    kb, registry, _, brand = components()
    evidence = kb.vulnerabilities[0].evidence
    tweet = "x" * 277
    draft = Draft(tweets=[tweet] * 5, claims=[Claim(text=tweet, evidence_ids=["SWC-107"])])
    errors = validate_draft(draft, registry.types["tech-thread"], brand, evidence, EvidenceLookup(kb))
    assert any("exceeds 280" in e for e in errors)


def test_named_technique_requires_matching_cited_evidence():
    kb, registry, _, brand = components()
    oracle = next(v for v in kb.vulnerabilities if v.id == "SCWE-028")
    tweet = "Review time-weighted averages to reduce short-lived manipulation."
    draft = Draft(tweets=[tweet], claims=[Claim(text=tweet, evidence_ids=["SCWE-028"])])
    errors = validate_draft(draft, registry.types["marketing-post"], brand, oracle.evidence, EvidenceLookup(kb))
    assert any("technical term 'time-weighted'" in e for e in errors)
    draft.claims[0].evidence_ids = ["OWASP-SC03"]
    assert validate_draft(draft, registry.types["marketing-post"], brand, oracle.evidence, EvidenceLookup(kb)) == []


def test_marketing_requires_review_invitation():
    kb, registry, _, brand = components()
    tweet = "Unchecked calls may fail silently."
    draft = Draft(tweets=[tweet], claims=[Claim(text=tweet, evidence_ids=["SWC-104"])])
    errors = validate_draft(draft, registry.types["marketing-post"], brand, kb.vulnerabilities[1].evidence, EvidenceLookup(kb))
    assert any("practical security action" in error for error in errors)
    source_action = "Make sure to handle the possibility that the call will fail by checking the return value."
    action_draft = Draft(tweets=[source_action], claims=[Claim(text=source_action, evidence_ids=["SWC-104"])])
    assert not validate_draft(action_draft, registry.types["marketing-post"], brand, kb.vulnerabilities[1].evidence, EvidenceLookup(kb))
    isolation = "Isolate each external call into its own transaction."
    isolation_draft = Draft(tweets=[isolation], claims=[Claim(text=isolation, evidence_ids=["SWC-113"])])
    failed_call = next(item for item in kb.vulnerabilities if item.id == "SWC-113")
    assert not validate_draft(isolation_draft, registry.types["marketing-post"], brand, failed_call.evidence, EvidenceLookup(kb))


def test_shared_skill_and_revision_gate():
    plan = Plan(slots=[Slot(id="piece_1", type="marketing-post", focus="reentrancy")])
    model = FakeModel(reject_first=True)
    results, lookup = run_plan(plan, model)
    assert results[0].status == "accepted"
    assert len(results[0].drafts) == 2
    assert len(results[0].reviews) == 2
    assert "research" in lookup.calls and "reviewer" in lookup.calls
    model = FakeModel(reject_always=True)
    results, _ = run_plan(plan, model)
    assert results[0].status == "dropped"
    assert len(results[0].drafts) == 2
    assert results[0].visual_spec is None


def test_hard_validation_overrides_approving_reviewer():
    plan = Plan(slots=[Slot(id="piece_1", type="marketing-post", focus="reentrancy")])
    results, _ = run_plan(plan, FakeModel(invalid_draft=True))
    assert results[0].status == "dropped"
    assert len(results[0].drafts) == 2
    assert all(any("hashtag" in error for error in attempt) for attempt in results[0].validations)
    assert results[0].visual_spec is None


def test_fabricated_reviewer_quote_cannot_approve():
    plan = Plan(slots=[Slot(id="piece_1", type="marketing-post", focus="reentrancy")])
    results, _ = run_plan(plan, FakeModel(invalid_quote=True))
    assert results[0].status == "dropped"
    assert all(any("No verified supporting excerpt" in reason for reason in review.reasons) for review in results[0].reviews)


def test_omitted_duplicate_reviewer_quote_uses_complete_atomic_support():
    plan = Plan(slots=[Slot(id="piece_1", type="marketing-post", focus="reentrancy")])
    results, _ = run_plan(plan, FakeModel(omit_quote=True))
    assert results[0].status == "accepted"
    assert results[0].reviews[0].claim_support == []
    assert all(verdict.verdict == "SUPPORTED" for verdict in results[0].semantic_reports[0].verdicts)


def test_low_reviewer_score_cannot_approve():
    plan = Plan(slots=[Slot(id="piece_1", type="marketing-post", focus="reentrancy")])
    results, _ = run_plan(plan, FakeModel(low_score=True))
    assert results[0].status == "dropped"
    assert all(not review.approved for review in results[0].reviews)


def test_parallel_isolation_and_export(tmp_path):
    plan = Plan(slots=[Slot(id="first", type="marketing-post", focus="reentrancy"),
                       Slot(id="second", type="marketing-post", focus="oracle manipulation"),
                       Slot(id="third", type="marketing-post", focus="nonexistent astronomy")])
    model = FakeModel()
    results, _ = run_plan(plan, model)
    assert {r.slot.id: r.status for r in results} == {"first": "accepted", "second": "accepted", "third": "failed"}
    assert model.peak_active == 1
    output = tmp_path / "run"
    summary = export_run(output, plan, results, 1.2, "fake", model.peak_active)
    assert summary["shipped"] == 2 and summary["failed"] == 1
    with (output / "posts.csv").open(newline="") as file:
        rows = list(csv.reader(file))
    assert rows[0] == ["Post Text", "Image"]
    assert len(rows) == 3
    assert rows[1][1].startswith("spec:")
    assert (output / rows[1][1].removeprefix("spec:")).exists()
    assert json.loads((output / "summary.json").read_text())["prompt_tokens_recorded"] == 60
    with pytest.raises(FileExistsError):
        export_run(output, plan, results, 1.2, "fake", 1)


def test_slots_reach_writer_concurrently():
    class BarrierModel(FakeModel):
        def __init__(self):
            super().__init__()
            self.started = 0
            self.both_started = asyncio.Event()

        async def structured(self, prompt, schema):
            if schema is Draft:
                self.started += 1
                if self.started == 2:
                    self.both_started.set()
                await asyncio.wait_for(self.both_started.wait(), timeout=1)
            return await super().structured(prompt, schema)

    plan = Plan(slots=[Slot(id="first", type="marketing-post", focus="reentrancy"),
                       Slot(id="second", type="marketing-post", focus="oracle manipulation")])
    results, _ = run_plan(plan, BarrierModel())
    assert [result.status for result in results] == ["accepted", "accepted"]


def test_model_failure_preserves_research_source():
    plan = Plan(slots=[Slot(id="failure", type="marketing-post", focus="reentrancy"),
                       Slot(id="healthy", type="marketing-post", focus="oracle manipulation")])
    results, _ = run_plan(plan, FakeModel(fail_topic='"topic": "Reentrancy"'))
    by_id = {r.slot.id: r for r in results}
    assert by_id["failure"].status == "failed"
    assert by_id["failure"].topic == "Reentrancy"
    assert by_id["failure"].source_ids == ["SWC-107"]
    assert by_id["healthy"].status == "accepted"


def test_registry_allows_new_type_without_graph_changes():
    kb, registry, brand_text, brand = components()
    registry.types["new-type"] = WriterConfig(instruction_file="instructions/marketing-post.md")
    model = FakeModel()
    graph, _ = build_week_graph(model, kb, registry, brand_text, brand)
    result = asyncio.run(graph.ainvoke({"plan": Plan(slots=[Slot(id="new", type="new-type", focus="reentrancy")]), "results": []}))
    assert result["results"][0].status == "accepted"


def test_thread_csv_order_and_dropped_exclusion(tmp_path):
    plan = Plan(slots=[Slot(id="thread", type="tech-thread", focus="reentrancy"),
                       Slot(id="drop", type="marketing-post", focus="nonexistent astronomy")])
    results, _ = run_plan(plan, FakeModel())
    output = tmp_path / "run"
    export_run(output, plan, results, 0.2, "fake", 1)
    with (output / "posts.csv").open(newline="") as file:
        rows = list(csv.reader(file))
    assert len(rows) == 2
    assert rows[1][0].startswith("1/5 ")
    assert "\n\n5/5 " in rows[1][0]


def test_cli_errors_and_override(monkeypatch, tmp_path):
    captured = {}

    async def fake_execute(plan, output, model=None):
        captured["plan"] = plan
        captured["output"] = output
        return {"failed": 0, "shipped": 1}

    monkeypatch.setattr("content_pipeline.cli.execute", fake_execute)
    assert week_main(["--plan", str(ROOT / "plan.json"), "--set", "thread_2=oracle manipulation", "--output", str(tmp_path / "week")]) == 0
    assert next(s for s in captured["plan"].slots if s.id == "thread_2").focus == "oracle manipulation"
    assert week_main(["--plan", str(ROOT / "plan.json"), "--set", "unknown=x"]) == 2
    assert piece_main(["--type", "tech-thread", "--topic", "reentrancy"]) == 0
    assert len(captured["plan"].slots) == 1
    assert piece_main(["--type", "unsupported", "--topic", "x"]) == 2


def test_brand_and_source_validation(tmp_path):
    from content_pipeline.config import load_brand
    bad = tmp_path / "bad.md"
    bad.write_text("```json\n{bad}\n```")
    with pytest.raises(ValueError, match="Invalid brand"):
        load_brand(bad)
    with pytest.raises(ValidationError):
        Evidence(id="bad", url="ftp://invalid", excerpt="Source evidence text")


def test_instructions_are_read_from_files(monkeypatch, tmp_path):
    from content_pipeline import agents
    (tmp_path / "writer.md").write_text("First instruction")
    monkeypatch.setattr(agents, "ROOT", tmp_path)
    assert agents.instruction("writer.md") == "First instruction"
    (tmp_path / "writer.md").write_text("Changed instruction")
    assert agents.instruction("writer.md") == "Changed instruction"


def test_unavailable_usage_is_not_zero(tmp_path):
    from content_pipeline.schemas import SlotResult
    plan = Plan(slots=[Slot(id="one", type="marketing-post", focus="reentrancy")])
    results = [SlotResult(slot=plan.slots[0], status="failed", reason="model timeout")]
    summary = export_run(tmp_path / "run", plan, results, 0.1, "fake", 0)
    assert summary["prompt_tokens_recorded"] is None
    assert summary["completion_tokens_recorded"] is None
    assert summary["usage_complete"] is False


def test_local_model_semaphore(monkeypatch):
    from types import SimpleNamespace
    model = LocalModel("qwen3.5:4b", "http://mock.local:11434", 1, 10)

    class Runnable:
        async def ainvoke(self, prompt):
            await asyncio.sleep(0.01)
            return {"parsed": Draft(tweets=["a"], claims=[]), "parsing_error": None,
                    "raw": SimpleNamespace(usage_metadata={"input_tokens": 2, "output_tokens": 3})}

    monkeypatch.setattr(type(model.model), "with_structured_output", lambda *a, **k: Runnable())

    async def two_calls():
        return await asyncio.gather(model.structured("one", Draft), model.structured("two", Draft))

    responses = asyncio.run(two_calls())
    assert model.peak_active == 1
    assert responses[0][1]["input_tokens"] == 2


def test_transport_retry_is_bounded_and_separate_from_revision(monkeypatch):
    from types import SimpleNamespace
    model = LocalModel("qwen3.5:4b", "http://mock.local:11434", 1, 10, transport_retries=1)
    calls = []

    class Runnable:
        async def ainvoke(self, prompt):
            calls.append(prompt)
            if len(calls) == 1:
                raise TimeoutError("temporary timeout")
            return {"parsed": Draft(tweets=["a"], claims=[]), "parsing_error": None,
                    "raw": SimpleNamespace(usage_metadata={"input_tokens": 2, "output_tokens": 3})}

    monkeypatch.setattr(type(model.model), "with_structured_output", lambda *a, **k: Runnable())
    parsed, usage = asyncio.run(model.structured("prompt", Draft))
    assert parsed.tweets == ["a"] and usage["output_tokens"] == 3
    assert len(calls) == 2 and model.peak_active == 1

    class AlwaysTimeout:
        async def ainvoke(self, prompt):
            calls.append(prompt)
            raise TimeoutError("persistent timeout")

    monkeypatch.setattr(type(model.model), "with_structured_output", lambda *a, **k: AlwaysTimeout())
    with pytest.raises(TimeoutError):
        asyncio.run(model.structured("another", Draft))
    assert len(calls) == 4

