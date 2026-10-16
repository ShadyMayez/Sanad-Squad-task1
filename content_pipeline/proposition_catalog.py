"""Structured evidence-first proposition and relation catalog model.

Represents versioned factual propositions and approved typed relationships
grounded in cryptographic source evidence snapshots.
"""
from __future__ import annotations

import json
import hashlib
from pathlib import Path
from typing import Literal
from pydantic import BaseModel, Field

from .text_spans import source_span_options

PropositionKind = Literal[
    "DEFINITION",
    "FACT",
    "MECHANISM",
    "PRECONDITION",
    "CONSEQUENCE",
    "RECOMMENDATION",
    "LIMITATION"
]

CatalogStatus = Literal[
    "PROPOSED",
    "REVIEWED_FOR_PILOT",
    "APPROVED",
    "REJECTED"
]

RelationType = Literal[
    "CAUSES",
    "ENABLES",
    "REQUIRES_CONDITION",
    "CAN_LEAD_TO",
    "RECOMMENDS_FOR",
    "MITIGATES",
    "HAS_LIMITATION",
    "APPLIES_TO_VERSION",
    "ACTION_RATIONALE",
    "INSTRUMENTAL",
    "CONDITIONAL",
    "TELEOLOGICAL"
]


class VerifiedProposition(BaseModel):
    id: str
    topic_id: str
    kind: PropositionKind
    canonical_text: str
    modality: str = Field(default="factual", description="epistemic modality: factual, possibility, recommendation, obligation")
    applicability: dict[str, str] = Field(default_factory=dict, description="e.g. {'solidity_version': '<0.4.22'}")
    evidence_span_ids: list[str] = Field(..., min_length=1)
    status: CatalogStatus = Field(default="REVIEWED_FOR_PILOT")
    catalog_version: str = Field(default="2.0.0")


class TypedRelation(BaseModel):
    id: str
    relation_type: RelationType
    source_id: str
    target_id: str
    direction: str = Field(default="source_to_target")
    modality: str = Field(default="factual")
    scope: str = Field(default="vulnerability_domain")
    evidence_span_ids: list[str] = Field(..., min_length=1)
    catalog_version: str = Field(default="2.0.0")
    status: CatalogStatus = Field(default="REVIEWED_FOR_PILOT")


class EvidenceWitness(BaseModel):
    evidence_id: str
    snapshot_path: str
    snapshot_sha256: str
    source_quote: str
    spans: list[str]
    scope: str | None = None


class PropositionCatalog(BaseModel):
    catalog_version: str = "2.0.0"
    propositions: list[VerifiedProposition]
    relations: list[TypedRelation]
    evidence_witnesses: dict[str, EvidenceWitness]

    def validate_catalog_integrity(self, root_dir: Path | None = None) -> list[str]:
        """Validate all referential integrity, span existence, canonical segmentation, and snapshot hashes."""
        errors: list[str] = []
        prop_ids = {p.id: p for p in self.propositions}
        rel_ids = {r.id: r for r in self.relations}

        # 0. Witness span canonical segmentation and exact quote verification
        for ev_id, witness in self.evidence_witnesses.items():
            expected_spans = source_span_options(witness.source_quote)
            if witness.spans != expected_spans:
                errors.append(
                    f"Evidence witness {ev_id} spans do not match canonical segmentation of source quote: "
                    f"expected {len(expected_spans)} spans, got {len(witness.spans)}"
                )
            for idx, span in enumerate(witness.spans):
                if span not in witness.source_quote:
                    errors.append(f"Evidence witness {ev_id} span at index {idx} not found in source quote: {span!r}")

        # 1. Proposition duplicate IDs, non-empty canonical text, and span references
        if len(prop_ids) != len(self.propositions):
            errors.append("Duplicate proposition IDs found in catalog")
        for p in self.propositions:
            if not p.canonical_text or not p.canonical_text.strip():
                errors.append(f"Proposition {p.id} has empty canonical_text")
            for span_id in p.evidence_span_ids:
                if "#" not in span_id:
                    errors.append(f"Proposition {p.id} has invalid span_id format: {span_id}")
                    continue
                ev_id, span_idx_str = span_id.split("#", 1)
                if ev_id not in self.evidence_witnesses:
                    errors.append(f"Proposition {p.id} references unknown evidence ID: {ev_id}")
                    continue
                try:
                    span_idx = int(span_idx_str)
                    witness = self.evidence_witnesses[ev_id]
                    if span_idx < 0 or span_idx >= len(witness.spans):
                        errors.append(f"Proposition {p.id} references out-of-bounds span index {span_idx} for evidence {ev_id}")
                except ValueError:
                    errors.append(f"Proposition {p.id} has non-integer span index: {span_idx_str}")

        # 2. Relation duplicate IDs, source/target references, topic bridges, and span references
        if len(rel_ids) != len(self.relations):
            errors.append("Duplicate relation IDs found in catalog")

        approved_topic_bridges = {
            ("SWC-105", "OZ-OWNABLE"),
            ("OZ-OWNABLE", "SWC-105"),
            ("SCWE-028", "OWASP-SC03"),
            ("OWASP-SC03", "SCWE-028"),
        }

        for r in self.relations:
            if r.source_id == r.target_id:
                errors.append(f"Relation {r.id} cannot be self-referential ({r.source_id})")
            if r.source_id not in prop_ids:
                errors.append(f"Relation {r.id} references non-existent source proposition: {r.source_id}")
            if r.target_id not in prop_ids:
                errors.append(f"Relation {r.id} references non-existent target proposition: {r.target_id}")

            if r.source_id in prop_ids and r.target_id in prop_ids:
                src_p = prop_ids[r.source_id]
                tgt_p = prop_ids[r.target_id]
                if src_p.topic_id != tgt_p.topic_id and (src_p.topic_id, tgt_p.topic_id) not in approved_topic_bridges:
                    errors.append(
                        f"Relation {r.id} connects incompatible topics: source {src_p.id} ({src_p.topic_id}) "
                        f"and target {tgt_p.id} ({tgt_p.topic_id})"
                    )

                allowed_ev_ids = {sp.split("#")[0] for sp in src_p.evidence_span_ids + tgt_p.evidence_span_ids}
                for span_id in r.evidence_span_ids:
                    if "#" not in span_id:
                        errors.append(f"Relation {r.id} has invalid span_id format: {span_id}")
                        continue
                    ev_id, span_idx_str = span_id.split("#", 1)
                    if ev_id not in self.evidence_witnesses:
                        errors.append(f"Relation {r.id} references unknown evidence ID: {ev_id}")
                        continue
                    if ev_id not in allowed_ev_ids:
                        errors.append(
                            f"Relation {r.id} references evidence {ev_id} which does not support "
                            f"either source proposition {r.source_id} or target proposition {r.target_id}"
                        )
                    try:
                        span_idx = int(span_idx_str)
                        witness = self.evidence_witnesses[ev_id]
                        if span_idx < 0 or span_idx >= len(witness.spans):
                            errors.append(f"Relation {r.id} references out-of-bounds span index {span_idx} for evidence {ev_id}")
                    except ValueError:
                        errors.append(f"Relation {r.id} has non-integer span index: {span_idx_str}")

        # 3. Snapshot hash verification
        if root_dir is not None:
            for ev_id, witness in self.evidence_witnesses.items():
                snap_path = root_dir / witness.snapshot_path
                if not snap_path.exists():
                    errors.append(f"Evidence witness {ev_id} snapshot file does not exist: {snap_path}")
                else:
                    computed = hashlib.sha256(snap_path.read_bytes()).hexdigest()
                    if computed != witness.snapshot_sha256:
                        errors.append(f"Evidence witness {ev_id} SHA-256 mismatch: recorded {witness.snapshot_sha256} vs computed {computed}")
                    if witness.source_quote not in snap_path.read_text():
                        errors.append(f"Evidence witness {ev_id} source quote not found in snapshot file")

        return errors

    def get_propositions_for_topic(self, topic_id: str, allowed_statuses: set[str] | None = None) -> list[VerifiedProposition]:
        statuses = allowed_statuses or {"REVIEWED_FOR_PILOT", "APPROVED"}
        return [p for p in self.propositions if p.topic_id == topic_id and p.status in statuses]

    def get_relations_for_topic(self, topic_id: str, allowed_statuses: set[str] | None = None) -> list[TypedRelation]:
        statuses = allowed_statuses or {"REVIEWED_FOR_PILOT", "APPROVED"}
        topic_prop_ids = {p.id for p in self.get_propositions_for_topic(topic_id, statuses)}
        return [r for r in self.relations if r.source_id in topic_prop_ids and r.target_id in topic_prop_ids and r.status in statuses]


def _find_project_root(path: Path | None = None) -> Path:
    candidates = []
    if path is not None:
        p = path.resolve()
        candidates.extend([p] + list(p.parents))
    candidates.append(Path.cwd().resolve())
    candidates.append(Path(__file__).resolve().parent.parent)
    for c in candidates:
        if (c / "source_snapshots").is_dir() and (c / "knowledge").is_dir():
            return c
    return Path.cwd().resolve()


def load_catalog(path: Path | None = None, root_dir: Path | None = None) -> PropositionCatalog:
    if root_dir is None:
        root_dir = _find_project_root(path)
    if path is None:
        path = root_dir / "knowledge" / "evidence_first_v2" / "catalog.json"
    if not path.exists():
        raise FileNotFoundError(f"Proposition catalog not found at {path}")
    data = json.loads(path.read_text())
    catalog = PropositionCatalog.model_validate(data)
    errors = catalog.validate_catalog_integrity(root_dir=root_dir)
    if errors:
        raise ValueError(f"Proposition catalog integrity errors:\n" + "\n".join(errors))
    return catalog


def validate_catalog_integrity(catalog: PropositionCatalog, root_dir: Path | None = None) -> list[str]:
    return catalog.validate_catalog_integrity(root_dir)


