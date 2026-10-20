"""Fail-closed integrity checks for pinned, offline source snapshots."""
from __future__ import annotations

import hashlib
from pathlib import Path
from .config import ROOT
from .schemas import Evidence, EvidenceContext, KnowledgeBase


def evidence_errors(item: Evidence, root: Path = ROOT) -> list[str]:
    errors: list[str] = []
    source_type = item.source_type or ""
    is_runtime_research = source_type.startswith("web_research") or source_type == "external_technical_resource"

    if is_runtime_research:
        # Runtime web research provenance authority:
        # Requires valid HTTPS URL, source title, retrieval timestamp, 64-char content sha256, quote, and scope.
        required = ("source_title", "source_type", "snapshot_sha256", "retrieved_at", "source_quote", "scope")
        for field in required:
            if not getattr(item, field):
                errors.append(f"{item.id}: missing {field}")
        if not item.url or not item.url.startswith("https://"):
            errors.append(f"{item.id}: runtime research evidence must have secure HTTPS url")
        if item.snapshot_sha256 and len(item.snapshot_sha256) != 64:
            errors.append(f"{item.id}: invalid sha256 checksum format")
        if item.snapshot_path:
            path = (root / item.snapshot_path).resolve()
            if not path.is_relative_to(root.resolve()):
                errors.append(f"{item.id}: snapshot path escapes repository")
            elif path.exists():
                raw = path.read_bytes()
                if hashlib.sha256(raw).hexdigest() != item.snapshot_sha256:
                    errors.append(f"{item.id}: source snapshot hash mismatch")
        return errors

    # Static KB evidence provenance authority:
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


def context_errors(window: EvidenceContext, item: Evidence, root: Path = ROOT) -> list[str]:
    """A context window has authority only through its pinned source snapshot."""
    errors = evidence_errors(item, root)
    if errors:
        return errors
    if window.evidence_id != item.id or window.snapshot_sha256 != item.snapshot_sha256 or window.source_scope != (item.scope or ""):
        return [f"{item.id}: context source identity or hash mismatch"]
    text = (root / (item.snapshot_path or "")).read_text()
    if window.start < (item.quote_start or 0) or window.end > (item.quote_end or 0) or text[window.start:window.end] != window.text:
        return [f"{item.id}: context offsets or text mismatch"]
    expected_partial = window.start > (item.quote_start or 0) or window.end < (item.quote_end or 0)
    if window.window_partial is not None and window.window_partial != expected_partial:
        return [f"{item.id}: context partial-window flag mismatch"]
    if window.token_upper_bound is not None and window.token_upper_bound != len(window.text.encode("utf-8")):
        return [f"{item.id}: context token upper bound mismatch"]
    if window.token_upper_bound is not None and window.token_upper_bound > window.token_budget_upper_bound and not window.truncated:
        return [f"{item.id}: context exceeds token budget without truncation flag"]
    return []
