"""Fail-closed integrity checks for pinned, offline source snapshots."""
from __future__ import annotations

import hashlib
from pathlib import Path
from .config import ROOT
from .schemas import Evidence, KnowledgeBase


def evidence_errors(item: Evidence, root: Path = ROOT) -> list[str]:
    errors: list[str] = []
    required = ("source_title", "source_type", "snapshot_path", "snapshot_sha256", "retrieved_at", "source_quote", "scope")
    for field in required:
        if not getattr(item, field):
            errors.append(f"{item.id}: missing {field}")
    if errors:
        return errors
    path = (root / item.snapshot_path).resolve()
    if not path.is_relative_to(root.resolve()):
        return [f"{item.id}: snapshot path escapes repository"]
    try:
        raw = path.read_bytes()
        text = raw.decode("utf-8")
    except (OSError, UnicodeError) as exc:
        return [f"{item.id}: source snapshot unavailable: {exc}"]
    actual = hashlib.sha256(raw).hexdigest()
    if actual != item.snapshot_sha256:
        errors.append(f"{item.id}: source snapshot hash mismatch")
    start, end = item.quote_start, item.quote_end
    # The snapshot is a UTF-8 text file; offsets refer to Unicode code points.
    if start is None or end is None or start < 0 or end <= start or text[start:end] != item.source_quote:
        errors.append(f"{item.id}: exact source quote or offsets mismatch")
    if item.source_quote not in text:
        errors.append(f"{item.id}: quote absent from source snapshot")
    return errors


def knowledge_base_errors(kb: KnowledgeBase, root: Path = ROOT) -> list[str]:
    return [error for topic in kb.vulnerabilities for item in topic.evidence for error in evidence_errors(item, root)]
