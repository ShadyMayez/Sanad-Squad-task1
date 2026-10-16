"""Extract exact evidence pairs for manual source-to-claim inspection."""
from __future__ import annotations

import argparse
import json
from pathlib import Path

from audit.semantic.inspect_new_run import inspect
from content_pipeline.relation_integrity import claim_relation_hints


def summarize(folder: Path) -> dict:
    mechanical = inspect(folder)
    accepted = json.loads((folder / "accepted_content.json").read_text())
    rows = []
    for piece in accepted:
        evidence = {e["id"]: e for e in piece["evidence"]}
        claims = {c["id"]: c for c in piece["atomic_claims"][-1]}
        verdicts = piece["semantic_reports"][-1]["verdicts"]
        for v in verdicts:
            c = claims[v["claim_id"]]
            rows.append({"slot_id": piece["slot"]["id"], "claim_id": c["id"],
                "public_claim": c["proposition"], "claim_relation_hints": claim_relation_hints(c["proposition"]),
                "selected_source_roles": v.get("selected_source_roles", {}),
                "model_evidence_relation": v.get("evidence_relation"),
                "relation_integrity_passed": v.get("relation_integrity_passed"),
                "support": [{"evidence_id": s["evidence_id"],
                    "source_title": evidence[s["evidence_id"]].get("source_title"),
                    "source_url": evidence[s["evidence_id"]]["url"],
                    "selected_exact_quote": s["quote"],
                    "source_scope": evidence[s["evidence_id"]].get("scope")}
                    for s in v["supporting_spans"]]})
    failures = json.loads((folder / "failures.json").read_text())
    return {"run": str(folder.resolve()), "summary": mechanical["summary"],
        "mechanical_inspection_passed": True, "accepted_claims_for_manual_review": rows,
        "non_accepted_slots": failures,
        "manual_semantic_clearance": "NO_ACCEPTED_CONTENT" if not accepted else "PENDING_HUMAN_REVIEW"}


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("folder", type=Path)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    args.output.write_text(json.dumps(summarize(args.folder), indent=2) + "\n")
