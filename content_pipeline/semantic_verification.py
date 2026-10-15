"""Independent model judgment, with deterministic provenance and output gates."""
from __future__ import annotations

import json
import time
from langchain_core.messages import HumanMessage, SystemMessage
from .agents import instruction
from .provenance import evidence_errors
from .schemas import AtomicClaim, Evidence, ModelSemanticDecision, SemanticReport, SemanticVerdict, SupportingSpan
from .text_spans import source_span_options


def error_report(claims: list[AtomicClaim], reason: str) -> SemanticReport:
    return SemanticReport(verdicts=[SemanticVerdict(claim_id=c.id, verdict="VERIFICATION_ERROR", reason=reason,
        verification_error=reason) for c in claims])


class SemanticVerifier:
    def __init__(self, model):
        self.model = model

    async def run(self, claims: list[AtomicClaim], evidence: list[Evidence]) -> tuple[SemanticReport, dict, float]:
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
                if response.verdict == "SUPPORTED":
                    selected = [{"span_id": id, "evidence_id": options[id][0], "text": options[id][1]} for id in response.support_option_ids]
                    audit_messages = [skeptic, HumanMessage(content=json.dumps({
                        "atomic_claims": [claim.model_dump()], "exact_span_options": selected,
                        "task": "Independently audit whether only these selected spans entail the full atomic claim. Veto unsupported scope or changed relationships."}, ensure_ascii=False))]
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
                    if audit.verdict != "SUPPORTED":
                        response = ModelSemanticDecision(verdict=audit.verdict, support_option_ids=[],
                            reason=f"Skeptical span audit: {audit.reason}",
                            missing_information=audit.missing_information,
                            scope_mismatch=audit.scope_mismatch, confidence=audit.confidence)
                spans = [SupportingSpan(evidence_id=options[id][0], quote=options[id][1]) for id in response.support_option_ids]
                for span in spans:
                    if span.quote not in by_id[span.evidence_id].source_quote:
                        raise ValueError(f"{claim.id}: source span no longer exists")
                verdict = SemanticVerdict(claim_id=claim.id, verdict=response.verdict,
                    evidence_ids=list(dict.fromkeys(span.evidence_id for span in spans)) if spans else claim.candidate_evidence_ids,
                    supporting_spans=spans, supporting_span_ids=response.support_option_ids,
                    reason=response.reason, missing_information=response.missing_information,
                    scope_mismatch=response.scope_mismatch, confidence=response.confidence,
                    verification_error=response.reason if response.verdict == "VERIFICATION_ERROR" else None)
                verdicts.append(verdict)
            except Exception as exc:
                usage_complete = False
                reason = f"Verifier failed: {type(exc).__name__}: {exc}"
                verdicts.extend(error_report([claim], reason).verdicts)
            finally:
                if "usage" in locals():
                    del usage
        usage_total["usage_complete"] = usage_complete
        return SemanticReport(verdicts=verdicts), usage_total, time.monotonic() - started
