"""Independent model judgment, with deterministic provenance and output gates."""
from __future__ import annotations

import json
import re
import time
from langchain_core.messages import HumanMessage, SystemMessage
from .agents import instruction
from .provenance import evidence_errors
from .relation_integrity import ABSOLUTE_PREVENTION, EXPLICIT_OPPOSITION, STRONG_CERTAINTY, UNIVERSAL_QUANTIFIER, assess_positive, claim_relation_hints, source_span_relation_hints, verify_sentence_relation
from .schemas import AtomicClaim, Evidence, EvidenceContext, ModelSemanticDecision, SemanticReport, SemanticVerdict, SentenceRelationRecord, SupportingSpan, VerificationPass
from .text_spans import bounded_context, source_span_options


def error_report(claims: list[AtomicClaim], reason: str) -> SemanticReport:
    return SemanticReport(verdicts=[SemanticVerdict(claim_id=c.id, verdict="VERIFICATION_ERROR", reason=reason,
        verification_error=reason) for c in claims])


class SemanticVerifier:
    def __init__(self, model):
        self.model = model
        self._cache: dict[tuple, SemanticVerdict] = {}

    async def run(self, claims: list[AtomicClaim], evidence: list[Evidence], relations: list[SentenceRelationRecord] | None = None) -> tuple[SemanticReport, dict, float]:
        started = time.monotonic()
        source_errors = [error for item in evidence for error in evidence_errors(item)]
        if source_errors:
            return error_report(claims, "; ".join(source_errors)), {}, time.monotonic() - started
        by_id = {item.id: item for item in evidence}
        for claim in claims:
            missing = [id for id in claim.candidate_evidence_ids if id not in by_id]
            if missing:
                return error_report(claims, f"Missing evidence IDs: {missing}"), {}, time.monotonic() - started
        verdicts = []
        usage_total: dict[str, int] = {}
        usage_complete = True
        system = SystemMessage(content=instruction("instructions/semantic-verifier.md"))
        skeptic = SystemMessage(content=instruction("instructions/semantic-skeptic.md"))
        for claim in claims:
            cache_key = (claim.proposition, tuple(sorted(claim.candidate_evidence_ids)))
            if cache_key in self._cache:
                cached = self._cache[cache_key].model_copy(update={"claim_id": claim.id})
                verdicts.append(cached)
                continue
            records = [{"id": e.id, "source_title": e.source_title, "source_type": e.source_type,
                        "source_url": e.url, "snapshot_sha256": e.snapshot_sha256,
                        "source_quote": e.source_quote, "scope": e.scope} for e in evidence if e.id in claim.candidate_evidence_ids]
            options: dict[str, tuple[str, str]] = {}
            for record in records:
                pieces = source_span_options(record["source_quote"])
                for index, piece in enumerate(pieces):
                    options[f"{record['id']}#{index}"] = (record["id"], piece)
            messages = [system, HumanMessage(content=json.dumps({"source_quotations": records,
                "exact_span_options": [{"span_id": id, "evidence_id": pair[0], "text": pair[1]} for id, pair in options.items()],
                "atomic_claims": [claim.model_dump()], "task": "Return one semantic decision. Python assigns claim and evidence IDs from your selected exact_span_options."}, ensure_ascii=False))]
            try:
                response, usage = await self.model.structured(messages, ModelSemanticDecision)
                for key in ("input_tokens", "output_tokens"):
                    if usage.get(key) is not None:
                        usage_total[key] = usage_total.get(key, 0) + usage[key]
                    else:
                        usage_complete = False
                if not isinstance(response, ModelSemanticDecision):
                    response = ModelSemanticDecision.model_validate(response)
                if any(id not in options for id in response.support_option_ids):
                    raise ValueError(f"{claim.id}: verifier selected an unknown exact span option")
                if response.verdict == "SUPPORTED" and not response.support_option_ids:
                    raise ValueError(f"{claim.id}: supported verdict lacks exact source span selection")
                initial = VerificationPass(verdict=response.verdict, support_option_ids=response.support_option_ids,
                    reason=response.reason, claim_relations=response.claim_relations,
                    evidence_relation=response.evidence_relation, relationship_verdict=response.relationship_verdict,
                    contradiction_detected=response.contradiction_detected,
                    uncertainty_detected=response.uncertainty_detected,
                    selected_source_roles={id: source_span_relation_hints(options[id][1]) for id in response.support_option_ids})
                audit_record = None
                context_windows: list[EvidenceContext] = []
                proposed: list[SupportingSpan] = []
                relation_error = ""
                relation_passed = False
                effective_roles = list(dict.fromkeys([*claim_relation_hints(claim.proposition), *response.claim_relations]))
                if response.verdict == "SUPPORTED":
                    selected = [{"span_id": id, "evidence_id": options[id][0], "text": options[id][1]} for id in response.support_option_ids]
                    proposed = [SupportingSpan(evidence_id=entry["evidence_id"], quote=entry["text"]) for entry in selected]
                    first_check = assess_positive(response, claim, [entry["text"] for entry in selected])
                    effective_roles = first_check.roles
                    if not first_check.passed:
                        relation_error = first_check.reason
                        response = response.model_copy(update={
                            "verdict": "VERIFICATION_ERROR" if first_check.invalid else "INSUFFICIENT_EVIDENCE",
                            "support_option_ids": [], "relationship_verdict": "NOT_ENTAILED",
                            "evidence_relation": "CONTRADICTORY_RELATION" if "contradict" in relation_error else "INSUFFICIENT_RELATION",
                            "reason": f"Source-to-claim relation gate: {relation_error}"})
                        initial.relation_error = relation_error
                    else:
                        for option_id in dict.fromkeys(response.support_option_ids):
                            evidence_id, _ = options[option_id]
                            item = by_id[evidence_id]
                            index = int(option_id.rsplit("#", 1)[1])
                            context, start, end, truncated = bounded_context(item.source_quote or "", index)
                            window = EvidenceContext(evidence_id=evidence_id, snapshot_sha256=item.snapshot_sha256 or "",
                                source_scope=item.scope or "",
                                start=(item.quote_start or 0) + start, end=(item.quote_start or 0) + end,
                                text=context, truncated=truncated,
                                window_partial=start > 0 or end < len(item.source_quote or ""),
                                token_upper_bound=len(context.encode("utf-8")))
                            if window not in context_windows:
                                context_windows.append(window)
                        audit_messages = [skeptic, HumanMessage(content=json.dumps({
                            "atomic_claims": [claim.model_dump()], "exact_span_options": selected,
                            "context_windows": [w.model_dump() for w in context_windows],
                            "tentative_verdict": initial.model_dump(),
                            "task": "Independently audit whether selected spans, interpreted within pinned context, entail the full atomic claim. Classify claim and evidence roles independently. Veto unsupported relationships and certainty upgrades."}, ensure_ascii=False))]
                        audit, audit_usage = await self.model.structured(audit_messages, ModelSemanticDecision)
                        if not isinstance(audit, ModelSemanticDecision):
                            audit = ModelSemanticDecision.model_validate(audit)
                        for key in ("input_tokens", "output_tokens"):
                            if audit_usage.get(key) is not None:
                                usage_total[key] = usage_total.get(key, 0) + audit_usage[key]
                            else:
                                usage_complete = False
                        if any(id not in response.support_option_ids for id in audit.support_option_ids):
                            raise ValueError(f"{claim.id}: skeptical audit selected a new source span")
                        audit_record = VerificationPass(verdict=audit.verdict, support_option_ids=audit.support_option_ids,
                            reason=audit.reason, claim_relations=audit.claim_relations,
                            evidence_relation=audit.evidence_relation, relationship_verdict=audit.relationship_verdict,
                            contradiction_detected=audit.contradiction_detected,
                            uncertainty_detected=audit.uncertainty_detected,
                            selected_source_roles={id: source_span_relation_hints(options[id][1]) for id in audit.support_option_ids})
                        if audit.verdict == "SUPPORTED":
                            second_check = assess_positive(audit, claim, [entry["text"] for entry in selected])
                            effective_roles = list(dict.fromkeys([*effective_roles, *second_check.roles]))
                            if not second_check.passed:
                                relation_error = second_check.reason
                                audit_record.relation_error = relation_error
                                response = audit.model_copy(update={
                                    "verdict": "VERIFICATION_ERROR" if second_check.invalid else "INSUFFICIENT_EVIDENCE",
                                    "support_option_ids": [], "relationship_verdict": "NOT_ENTAILED",
                                    "evidence_relation": "CONTRADICTORY_RELATION" if "contradict" in relation_error else "INSUFFICIENT_RELATION",
                                    "reason": f"Skeptical relation gate: {relation_error}"})
                            else:
                                relation_passed = True
                        elif (initial.verdict == "SUPPORTED" and first_check.passed
                              and audit.verdict == "INSUFFICIENT_EVIDENCE"
                              and not audit.contradiction_detected and audit.relationship_verdict != "CONTRADICTED"
                              and not (EXPLICIT_OPPOSITION.search(audit.reason) and not re.search(r"\b(?:does not|do not|cannot)\s+contradict", audit.reason, re.I))
                              and not UNIVERSAL_QUANTIFIER.search(claim.proposition)
                              and not STRONG_CERTAINTY.search(claim.proposition)
                              and not ABSOLUTE_PREVENTION.search(claim.proposition)
                              and all(entry["text"] in by_id[options[entry["span_id"]][0]].source_quote for entry in selected)):
                            clarification_messages = [
                                system,
                                HumanMessage(content=json.dumps({
                                    "atomic_claims": [claim.model_dump()],
                                    "exact_span_options": selected,
                                    "context_windows": [w.model_dump() for w in context_windows],
                                    "initial_support": {
                                        "evidence_relation": initial.evidence_relation,
                                        "claim_relations": initial.claim_relations,
                                        "reason": initial.reason
                                    },
                                    "skeptical_audit": {
                                        "verdict": audit.verdict,
                                        "reason": audit.reason,
                                        "missing_relation_support": audit.missing_relation_support
                                    },
                                    "task": "Resolve the specific relation dispute between initial verification and skeptical audit. Evaluate whether selected spans entail the claim under faithful domain paraphrasing, modal narrowing, or source-attributed recommendation, while strictly vetoing unsupported causal inversions or guarantees. Return one ModelSemanticDecision."
                                }, ensure_ascii=False))
                            ]
                            reconciled, rec_usage = await self.model.structured(clarification_messages, ModelSemanticDecision)
                            if not isinstance(reconciled, ModelSemanticDecision):
                                reconciled = ModelSemanticDecision.model_validate(reconciled)
                            for key in ("input_tokens", "output_tokens"):
                                if rec_usage.get(key) is not None:
                                    usage_total[key] = usage_total.get(key, 0) + rec_usage[key]
                                else:
                                    usage_complete = False
                            if reconciled.verdict == "SUPPORTED" and not any(id not in response.support_option_ids for id in reconciled.support_option_ids):
                                rec_check = assess_positive(reconciled, claim, [entry["text"] for entry in selected])
                                if rec_check.passed:
                                    relation_passed = True
                                    response = reconciled
                                    effective_roles = list(dict.fromkeys([*effective_roles, *rec_check.roles]))
                                else:
                                    response = audit.model_copy(update={"support_option_ids": [],
                                        "reason": f"Reconciliation relation gate veto: {rec_check.reason}"})
                            else:
                                response = audit.model_copy(update={"support_option_ids": [],
                                    "reason": f"Skeptical audit sustained: {audit.reason}"})
                        else:
                            response = audit.model_copy(update={"support_option_ids": [],
                                "reason": f"Skeptical span audit: {audit.reason}"})
                spans = [SupportingSpan(evidence_id=options[id][0], quote=options[id][1]) for id in response.support_option_ids]
                for span in spans:
                    if span.quote not in by_id[span.evidence_id].source_quote:
                        raise ValueError(f"{claim.id}: source span no longer exists")
                verdict = SemanticVerdict(claim_id=claim.id, verdict=response.verdict,
                    evidence_ids=list(dict.fromkeys(span.evidence_id for span in spans)) if spans else claim.candidate_evidence_ids,
                    supporting_spans=spans, supporting_span_ids=response.support_option_ids,
                    reason=response.reason, missing_information=response.missing_information,
                    scope_mismatch=response.scope_mismatch, confidence=response.confidence,
                    verification_error=response.reason if response.verdict == "VERIFICATION_ERROR" else None,
                    context_windows=context_windows, proposed_supporting_spans=proposed,
                    initial_pass=initial, skeptical_pass=audit_record,
                    claim_relations=effective_roles, evidence_relation=response.evidence_relation,
                    relationship_verdict=response.relationship_verdict,
                    relation_integrity_passed=relation_passed, relation_error=relation_error)
                verdict.selected_source_roles = {id: source_span_relation_hints(options[id][1]) for id in response.support_option_ids}
                verdicts.append(verdict)
                self._cache[cache_key] = verdict
            except Exception as exc:
                usage_complete = False
                reason = f"Verifier failed: {type(exc).__name__}: {exc}"
                verdicts.extend(error_report([claim], reason).verdicts)
            finally:
                if "usage" in locals():
                    del usage

        # Verify whole sentence relationships
        effective_relations = relations
        if effective_relations is None:
            effective_relations = list({c.sentence_relation.id: c.sentence_relation for c in claims if c.sentence_relation}.values())

        rel_map: dict[str, SentenceRelationRecord] = {}
        sentence_to_rels: dict[str, list[SentenceRelationRecord]] = {}
        verified_relations_list: list[SentenceRelationRecord] = []
        for rel in effective_relations:
            if rel.semantic_verdict is None:
                updated_rel, rel_usage = await self.verify_relation_semantic(rel, evidence, system)
                for key in ("input_tokens", "output_tokens"):
                    if rel_usage.get(key) is not None:
                        usage_total[key] = usage_total.get(key, 0) + rel_usage[key]
                    else:
                        usage_complete = False
            else:
                updated_rel = rel
            verified_relations_list.append(updated_rel)
            rel_map[updated_rel.sentence] = updated_rel
            rel_map[updated_rel.id] = updated_rel
            sentence_to_rels.setdefault(updated_rel.sentence, []).append(updated_rel)

        claim_by_id = {c.id: c for c in claims}
        for c in claims:
            if c.sentence in rel_map:
                c.sentence_relation = rel_map[c.sentence]
        for v in verdicts:
            c = claim_by_id.get(v.claim_id)
            if c and c.sentence in sentence_to_rels:
                for r in sentence_to_rels[c.sentence]:
                    if r.semantic_verdict != "SUPPORTED":
                        v.relation_integrity_passed = False
                        v.relation_error = f"Sentence relation {r.id} ({r.connector}) not supported: {r.justification}"
                        break

        usage_total["usage_complete"] = usage_complete
        return SemanticReport(verdicts=verdicts, sentence_relations=verified_relations_list), usage_total, time.monotonic() - started

    async def verify_relation_semantic(
        self, rel: SentenceRelationRecord, evidence: list[Evidence], system: SystemMessage
    ) -> tuple[SentenceRelationRecord, dict]:
        records = [
            {"id": e.id, "source_title": e.source_title, "source_type": e.source_type,
             "source_url": e.url, "snapshot_sha256": e.snapshot_sha256,
             "source_quote": e.source_quote, "scope": e.scope}
            for e in evidence if e.id in rel.candidate_evidence_ids
        ]
        if not records:
            records = [
                {"id": e.id, "source_title": e.source_title, "source_type": e.source_type,
                 "source_url": e.url, "snapshot_sha256": e.snapshot_sha256,
                 "source_quote": e.source_quote, "scope": e.scope}
                for e in evidence
            ]
        options: dict[str, tuple[str, str]] = {}
        for record in records:
            pieces = source_span_options(record["source_quote"])
            for index, piece in enumerate(pieces):
                options[f"{record['id']}#{index}"] = (record["id"], piece)

        if rel.relation_type == "ACTION_RATIONALE":
            task_desc = (
                "Evaluate whether the source quotations entail this relationship. "
                "For ACTION_RATIONALE: A review action justified by a documented hazard is supported when: "
                "(1) The premise describes a genuine technical hazard documented in the source; "
                "(2) The conclusion is a relevant review action or remediation aligned with the source guidance; "
                "(3) The premise is not another bare recommendation. "
                "Do NOT demand that the source text literally assert that the act of reviewing is caused by the bug; "
                "it is sufficient that the hazard is documented and motivates the review action. "
                "Select the exact supporting span options and return one ModelSemanticDecision."
            )
        elif rel.relation_type == "CAUSAL":
            task_desc = (
                "Evaluate whether the source quotations entail this relationship. "
                "For CAUSAL: A factual causal assertion requires that the evidence establishes that the premise specifically causes, leads to, or produces the conclusion. "
                "Do NOT accept a causal claim merely because separate clauses are individually true in different contexts or sources. "
                "If the evidence does not establish that the premise causes the conclusion, return INSUFFICIENT_EVIDENCE or CONTRADICTED. "
                "Select the exact supporting span options and return one ModelSemanticDecision."
            )
        elif rel.relation_type == "INSTRUMENTAL":
            task_desc = (
                "Evaluate whether the source quotations entail this relationship. "
                "For INSTRUMENTAL: An instrumental assertion ('by ...-ing') requires that the evidence establishes that the action in the premise achieves or implements the outcome in the conclusion. "
                "Select the exact supporting span options and return one ModelSemanticDecision."
            )
        else:
            task_desc = (
                f"Evaluate whether the source quotations entail this {rel.relation_type} relationship. "
                "Verify that the condition/action and the consequence/purpose are grounded in the source context and scope. "
                "Select the exact supporting span options and return one ModelSemanticDecision."
            )

        prompt_payload = {
            "sentence": rel.sentence,
            "relation_type": rel.relation_type,
            "connector": rel.connector,
            "premise": rel.premise,
            "conclusion": rel.conclusion,
            "source_quotations": records,
            "exact_span_options": [{"span_id": k, "evidence_id": v[0], "text": v[1]} for k, v in options.items()],
            "task": task_desc,
        }

        try:
            decision, usage = await self.model.structured([system, HumanMessage(content=json.dumps(prompt_payload, ensure_ascii=False))], ModelSemanticDecision)
            if not isinstance(decision, ModelSemanticDecision):
                decision = ModelSemanticDecision.model_validate(decision)
            if decision.verdict == "SUPPORTED" and decision.relationship_verdict == "ENTAILED":
                selected_quotes = [options[id][1] for id in decision.support_option_ids if id in options]
                selected_evidence_ids = {options[id][0] for id in decision.support_option_ids if id in options}
                candidate_spans = [s for r in records if r["id"] in selected_evidence_ids for s in source_span_options(r["source_quote"])] if selected_evidence_ids else selected_quotes
                assessment = verify_sentence_relation(rel, candidate_spans)
                if assessment.passed:
                    rel = rel.model_copy(update={
                        "semantic_verdict": "SUPPORTED",
                        "justification": decision.reason,
                        "supporting_spans": selected_quotes,
                    })
                else:
                    rel = rel.model_copy(update={
                        "semantic_verdict": "INSUFFICIENT_EVIDENCE",
                        "justification": f"Deterministic relation gate veto: {assessment.reason}",
                        "supporting_spans": [],
                    })
            else:
                rel = rel.model_copy(update={
                    "semantic_verdict": decision.verdict,
                    "justification": decision.reason,
                    "supporting_spans": [],
                })
            return rel, usage
        except Exception as exc:
            rel = rel.model_copy(update={
                "semantic_verdict": "VERIFICATION_ERROR",
                "justification": f"Model relation verification failed: {type(exc).__name__}: {exc}",
                "supporting_spans": [],
            })
            return rel, {}
