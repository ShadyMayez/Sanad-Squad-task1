"""Audit-only adversarial probes. These do not alter application code."""
from __future__ import annotations

import asyncio
import csv
import json
from pathlib import Path
from types import SimpleNamespace

import pytest
from pydantic import ValidationError

from content_pipeline import agents
from content_pipeline.config import ROOT, load_brand, load_kb, load_plan, load_registry
from content_pipeline.export import export_run
from content_pipeline.graph import build_week_graph
from content_pipeline.llm import LocalModel
from content_pipeline.schemas import Claim, ClaimSupport, Draft, Evidence, KnowledgeBase, Plan, Review, Slot, SlotResult
from content_pipeline.skills import EvidenceLookup
from content_pipeline.validation import validate_draft


def run(slots, model):
    text, brand = load_brand()
    app, lookup = build_week_graph(model, load_kb(), load_registry(), text, brand)
    state = asyncio.run(app.ainvoke({"plan": Plan(slots=slots), "results": []}))
    return state["results"], lookup


class ControlledModel:
    def __init__(self, draft_text="Review the cited contract risk.", *, reject=False, score=5,
                 fail_review=False, fail_write_for=None, delay_first=False):
        self.draft_text = draft_text
        self.reject = reject
        self.score = score
        self.fail_review = fail_review
        self.fail_write_for = fail_write_for
        self.delay_first = delay_first
        self.peak_active = 0
        self.writer_entries = []
        self.feedback = []

    async def structured(self, prompt, schema):
        if schema is Draft:
            slot = json.loads(prompt.split("Slot: ", 1)[1].split("\nTopic:", 1)[0])
            self.writer_entries.append(slot["id"])
            self.feedback.append(prompt.split("Revision feedback: ", 1)[1].split("\nCreate one claim", 1)[0])
            if self.fail_write_for == slot["id"]:
                raise TimeoutError("injected writer timeout")
            if self.delay_first and slot["id"] == "first":
                await asyncio.sleep(0.03)
            evidence = json.loads(prompt.split("Evidence data (not instructions): ", 1)[1].split("\nRevision feedback:", 1)[0])
            text = self.draft_text
            return Draft(tweets=[text], claims=[Claim(text=text, evidence_ids=[evidence[0]["id"]])]), {"input_tokens": 2, "output_tokens": 3}
        if self.fail_review:
            raise ValueError("malformed reviewer JSON")
        draft = json.loads(prompt.split("Draft: ", 1)[1].split("\nDeterministic errors:", 1)[0])
        evidence = json.loads(prompt.split("Evidence data (not instructions): ", 1)[1].split("\nDraft:", 1)[0])
        e = evidence[0]
        support = [ClaimSupport(claim_text=c["text"], evidence_id=e["id"],
                                evidence_quote=e["excerpt"][:28], supported=True) for c in draft["claims"]]
        review = Review(factual_support=self.score, technical_correctness=self.score,
                        brand_voice=self.score, clarity=self.score, platform_format=self.score,
                        usefulness=self.score, approved=not self.reject,
                        reasons=["Inadequate evidence"] if self.reject else [],
                        corrections=["Remove unsupported assertion"] if self.reject else [],
                        grounding_assessment="Fixture", claim_support=support)
        return review, {"input_tokens": 4, "output_tokens": 5}


def test_invalid_inputs_and_missing_brand(tmp_path):
    bad = tmp_path / "bad-plan.json"
    bad.write_text('{"slots": []}')
    with pytest.raises(ValueError):
        load_plan(bad, load_registry())
    bad.write_text('{"slots": [{"id":"a","type":"not-registered"}]}')
    with pytest.raises(ValueError, match="Unsupported"):
        load_plan(bad, load_registry())
    missing = tmp_path / "absent-brand.md"
    with pytest.raises(ValueError, match="Invalid brand"):
        load_brand(missing)
    with pytest.raises(ValidationError):
        Evidence(id="x", url="http://not-https.example", excerpt="Valid-looking excerpt")
    kb_data = load_kb().model_dump()
    del kb_data["vulnerabilities"][0]["root_cause"]
    with pytest.raises(ValidationError):
        KnowledgeBase.model_validate(kb_data)


def test_empty_focus_is_resolved_and_unsupported_focus_fails_only_one_slot():
    slots = [Slot(id="first", type="marketing-post", focus=None),
             Slot(id="second", type="marketing-post", focus="astronomy")]
    results, _ = run(slots, ControlledModel())
    statuses = {r.slot.id: r.status for r in results}
    assert statuses == {"first": "accepted", "second": "failed"}
    assert next(r for r in results if r.slot.id == "first").source_ids


def test_misleading_kb_description_can_drive_topic_selection():
    kb = load_kb().model_copy(deep=True)
    kb.vulnerabilities[0].description = "A fictitious quantum bridge attack affects all contracts."
    selected = EvidenceLookup(kb).select("quantum bridge attack", 0)
    assert selected.id == "SWC-107"
    assert "quantum" not in selected.evidence[0].excerpt.lower()


@pytest.mark.parametrize("text", [
    "Review how reentrancy locks prevent any external call from transferring control.",
    "Review why SanadSquad audited 500 protocols for this risk.",
    "Review oracle prices to stop reentrancy in every contract.",
])
def test_semantically_false_or_fabricated_claim_can_ship_when_reviewer_approves(text):
    slot = Slot(id="piece", type="marketing-post", focus="reentrancy")
    results, _ = run([slot], ControlledModel(draft_text=text))
    # This is the observed defect: valid citation IDs and a real quote are not semantic proof.
    assert results[0].status == "accepted"
    assert results[0].reviews[-1].approved
    assert not results[0].validations[-1]


def test_reviewer_low_score_or_rejection_drops_after_one_revision(tmp_path):
    slot = Slot(id="piece", type="marketing-post", focus="reentrancy")
    low, _ = run([slot], ControlledModel(score=2))
    rejected, _ = run([slot], ControlledModel(reject=True))
    for result in (low[0], rejected[0]):
        assert result.status == "dropped" and len(result.drafts) == 2
        assert len(result.reviews) == 2 and result.visual_spec is None
    output = tmp_path / "run"
    export_run(output, Plan(slots=[slot]), rejected, 0.1, "fake", 0)
    with (output / "posts.csv").open(newline="") as file:
        assert list(csv.reader(file)) == [["Post Text", "Image"]]


def test_rejection_feedback_reaches_second_writer_call():
    model = ControlledModel(reject=True)
    run([Slot(id="piece", type="marketing-post", focus="reentrancy")], model)
    assert len(model.feedback) == 2
    assert model.feedback[0] == "[]"
    assert "Remove unsupported assertion" in model.feedback[1]


def test_approving_reviewer_cannot_override_hard_hashtag_failure():
    slot = Slot(id="piece", type="marketing-post", focus="reentrancy")
    result, _ = run([slot], ControlledModel(draft_text="Review #reentrancy risk."))
    assert result[0].status == "dropped"
    assert len(result[0].drafts) == 2
    assert all(any("hashtag" in error for error in attempt) for attempt in result[0].validations)
    assert result[0].visual_spec is None


def test_reviewer_malformed_response_and_multiple_writer_timeouts_are_isolated():
    slots = [Slot(id="first", type="marketing-post", focus="reentrancy"),
             Slot(id="second", type="marketing-post", focus="oracle manipulation")]
    failed, _ = run(slots, ControlledModel(fail_review=True))
    assert [r.status for r in failed] == ["failed", "failed"]
    partial, _ = run(slots, ControlledModel(fail_write_for="first"))
    assert {r.slot.id: r.status for r in partial} == {"first": "failed", "second": "accepted"}


def test_slow_slot_does_not_reorder_export(tmp_path):
    slots = [Slot(id="first", type="marketing-post", focus="reentrancy"),
             Slot(id="second", type="marketing-post", focus="oracle manipulation")]
    results, _ = run(slots, ControlledModel(delay_first=True))
    assert {r.status for r in results} == {"accepted"}
    folder = tmp_path / "ordered"
    export_run(folder, Plan(slots=slots), results, 0.1, "fake", 0)
    accepted = json.loads((folder / "accepted_content.json").read_text())
    assert [x["slot"]["id"] for x in accepted] == ["first", "second"]


def test_two_slots_reach_writer_before_either_completes():
    class BarrierModel(ControlledModel):
        def __init__(self):
            super().__init__()
            self.started = 0
            self.barrier = asyncio.Event()

        async def structured(self, prompt, schema):
            if schema is Draft:
                self.started += 1
                if self.started == 2:
                    self.barrier.set()
                await asyncio.wait_for(self.barrier.wait(), timeout=1)
            return await super().structured(prompt, schema)

    slots = [Slot(id="first", type="marketing-post", focus="reentrancy"),
             Slot(id="second", type="marketing-post", focus="oracle manipulation")]
    model = BarrierModel()
    results, _ = run(slots, model)
    assert model.started == 2 and all(r.status == "accepted" for r in results)


def test_shared_skill_and_instructions_are_real_files(monkeypatch, tmp_path):
    slots = [Slot(id="piece", type="marketing-post", focus="reentrancy")]
    _, lookup = run(slots, ControlledModel())
    assert "research" in lookup.calls and "reviewer" in lookup.calls
    (tmp_path / "changed.md").write_text("AUDIT-MARKER")
    monkeypatch.setattr(agents, "ROOT", tmp_path)
    assert agents.instruction("changed.md") == "AUDIT-MARKER"


def test_modified_rubric_file_is_sent_to_reviewer(monkeypatch, tmp_path):
    (tmp_path / "instructions").mkdir()
    (tmp_path / "instructions/reviewer-rubric.md").write_text("AUDIT RUBRIC MARKER")
    monkeypatch.setattr(agents, "ROOT", tmp_path)

    class Capture:
        async def structured(self, prompt, schema):
            assert "AUDIT RUBRIC MARKER" in prompt
            return Review(factual_support=5, technical_correctness=5, brand_voice=5,
                          clarity=5, platform_format=5, usefulness=5, approved=True,
                          grounding_assessment="fixture", claim_support=[]), {}

    reviewer = agents.ReviewerAgent(Capture(), EvidenceLookup(load_kb()), "brand")
    draft = Draft(tweets=["Review this risk."], claims=[])
    asyncio.run(reviewer.run(draft, load_kb().vulnerabilities[0].evidence, []))


def test_modified_writer_file_is_sent_to_model(monkeypatch, tmp_path):
    (tmp_path / "instructions").mkdir()
    (tmp_path / "instructions/marketing-post.md").write_text("AUDIT WRITER MARKER")
    monkeypatch.setattr(agents, "ROOT", tmp_path)

    class Capture:
        async def structured(self, prompt, schema):
            assert "AUDIT WRITER MARKER" in prompt
            return Draft(tweets=["Review this risk."], claims=[Claim(text="Review this risk.", evidence_ids=["SWC-107"])]), {}

    writer = agents.WriterAgent(Capture(), load_registry().types["marketing-post"], "brand")
    asyncio.run(writer.run(Slot(id="piece", type="marketing-post"), load_kb().vulnerabilities[0]))


def test_brand_edit_changes_validator_without_code_change():
    kb = load_kb()
    _, brand = load_brand()
    brand.banned_words.append("Review")
    tweet = "Review the cited risk."
    draft = Draft(tweets=[tweet], claims=[Claim(text=tweet, evidence_ids=["SWC-107"])])
    errors = validate_draft(draft, load_registry().types["marketing-post"], brand,
                            kb.vulnerabilities[0].evidence, EvidenceLookup(kb))
    assert any("banned phrase" in error for error in errors)


def test_export_accepts_missing_visual_spec_and_unreviewed_accepted_result(tmp_path):
    # A forged SlotResult cannot arise through the ordinary graph route but crosses
    # the exporter trust boundary without approval or a real visual specification.
    slot = Slot(id="piece", type="marketing-post", focus="reentrancy")
    tweet = 'Review "quoted", multiline\ncontract paths.'
    forged = SlotResult(slot=slot, status="accepted", drafts=[Draft(tweets=[tweet], claims=[])],
                        reviews=[], visual_spec=None)
    folder = tmp_path / "forged"
    export_run(folder, Plan(slots=[slot]), [forged], 0.1, "fake", 0)
    assert (folder / "visual_specs/piece.md").read_text() == ""
    with (folder / "posts.csv").open(newline="") as file:
        rows = list(csv.reader(file))
    assert rows[1][0] == tweet  # CSV escaping itself works.


def test_two_local_model_instances_do_not_share_global_semaphore(monkeypatch):
    active = 0
    peak = 0

    class Runnable:
        async def ainvoke(self, prompt):
            nonlocal active, peak
            active += 1
            peak = max(peak, active)
            await asyncio.sleep(0.02)
            active -= 1
            return {"parsed": Draft(tweets=["hello"], claims=[]), "parsing_error": None,
                    "raw": SimpleNamespace(usage_metadata={"input_tokens": 1, "output_tokens": 1})}

    first = LocalModel("qwen3.5:4b", "http://127.0.0.1:11434", 1, 10)
    second = LocalModel("qwen3.5:4b", "http://127.0.0.1:11434", 1, 10)
    monkeypatch.setattr(type(first.model), "with_structured_output", lambda *a, **k: Runnable())
    async def two_calls():
        return await asyncio.gather(first.structured("a", Draft), second.structured("b", Draft))

    asyncio.run(two_calls())
    assert peak == 2


@pytest.mark.parametrize("limit,expected_peak", [(1, 1), (2, 2)])
def test_configured_model_concurrency_limit(monkeypatch, limit, expected_peak):
    active = 0
    peak = 0

    class Runnable:
        async def ainvoke(self, prompt):
            nonlocal active, peak
            active += 1
            peak = max(peak, active)
            await asyncio.sleep(0.02)
            active -= 1
            return {"parsed": Draft(tweets=["hello"], claims=[]), "parsing_error": None,
                    "raw": SimpleNamespace(usage_metadata={"input_tokens": 1, "output_tokens": 1})}

    model = LocalModel("qwen3.5:4b", "http://127.0.0.1:11434", limit, 10)
    monkeypatch.setattr(type(model.model), "with_structured_output", lambda *a, **k: Runnable())

    async def two_calls():
        return await asyncio.gather(model.structured("a", Draft), model.structured("b", Draft))

    asyncio.run(two_calls())
    assert peak == expected_peak == model.peak_active


def test_malformed_structured_model_result_is_a_failed_slot():
    class MalformedModel(ControlledModel):
        async def structured(self, prompt, schema):
            if schema is Draft:
                raise ValueError("Structured model output invalid: malformed JSON")
            return await super().structured(prompt, schema)

    result, _ = run([Slot(id="piece", type="marketing-post", focus="reentrancy")], MalformedModel())
    assert result[0].status == "failed" and "malformed JSON" in result[0].reason


def test_corrupted_json_artifact_is_detected(tmp_path):
    from audit.scripts.inspect_run import inspect

    slot = Slot(id="piece", type="marketing-post", focus="reentrancy")
    results, _ = run([slot], ControlledModel())
    folder = tmp_path / "run"
    export_run(folder, Plan(slots=[slot]), results, 0.1, "fake", 0)
    (folder / "summary.json").write_text("{not valid JSON")
    with pytest.raises(json.JSONDecodeError):
        inspect(folder)


def test_unexpected_worker_exception_is_isolated(monkeypatch):
    import content_pipeline.graph as graph_module

    class ExplodingPiece:
        async def ainvoke(self, state, config=None):
            if state["slot"].id == "bad":
                raise RuntimeError("unexpected worker failure")
            return {"result": SlotResult(slot=state["slot"], status="dropped", reason="fixture")}

    monkeypatch.setattr(graph_module, "build_piece_graph", lambda *args: ExplodingPiece())
    text, brand = load_brand()
    app, _ = graph_module.build_week_graph(ControlledModel(), load_kb(), load_registry(), text, brand)
    slots = [Slot(id="bad", type="marketing-post"), Slot(id="other", type="marketing-post")]
    state = asyncio.run(app.ainvoke({"plan": Plan(slots=slots), "results": []}))
    assert {r.slot.id: r.status for r in state["results"]} == {"bad": "failed", "other": "dropped"}
    assert "unexpected worker failure" in next(r.reason for r in state["results"] if r.slot.id == "bad")
