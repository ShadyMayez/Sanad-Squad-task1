"""Explicit relation fields for deterministic model fixtures."""


def relation_fields(verdict="SUPPORTED", evidence_relation=None, claim_relations=None):
    supported = verdict == "SUPPORTED"
    return {
        "claim_relations": claim_relations or ["DESCRIPTIVE_FACT"],
        "evidence_relation": evidence_relation or ("DIRECT_DESCRIPTIVE_SUPPORT" if supported else "INSUFFICIENT_RELATION"),
        "relationship_verdict": "ENTAILED" if supported else "NOT_ENTAILED",
        "contradiction_detected": False,
        "uncertainty_detected": False,
    }
