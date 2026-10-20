"""Thread-safe research logger with zero-credential masking and traceable records."""
from __future__ import annotations

import re
import threading
from datetime import datetime, timezone
from typing import Any
from .models import FetchedPage, ResearchQueryRecord, SlotResearchAudit
from ..schemas import Evidence, ResearchRecord

AUTH_BEARER_PATTERN = re.compile(r"(?i)(?:authorization\s*:\s*)?bearer\s+[a-z0-9_\-\.]+", re.IGNORECASE)
SENSITIVE_KEY_PATTERN = re.compile(
    r"(?i)(api[_-]?key|token|secret|password|authorization)\s*[:=]\s*([^\s,;\"']+)"
)


def mask_sensitive_strings(text: str) -> str:
    """Mask any accidental API keys, tokens, or credentials from logs."""
    if not text:
        return text
    masked = AUTH_BEARER_PATTERN.sub("Bearer [REDACTED]", text)
    masked = SENSITIVE_KEY_PATTERN.sub(r"\1: [REDACTED]", masked)
    return masked


class ResearchLogger:
    def __init__(self, run_id: str = "run_default"):
        self.run_id = run_id
        self._lock = threading.Lock()
        self.queries: list[ResearchQueryRecord] = []
        self.fetches: list[FetchedPage] = []
        self.slot_audits: dict[str, SlotResearchAudit] = {}

    def log_query(
        self,
        slot_id: str,
        query_text: str,
        service_line: str,
        provider_name: str,
        mode: str,
        results_count: int,
        returned_urls: list[str] | None = None,
        source_group: str | None = None,
        error: str | None = None,
    ) -> ResearchQueryRecord:
        """Record every search query, including zero-result queries."""
        record = ResearchQueryRecord(
            query_id=f"q_{len(self.queries) + 1}",
            slot_id=slot_id,
            query_text=mask_sensitive_strings(query_text),
            service_line=service_line,
            source_group=source_group,
            provider_name=provider_name,
            mode=mode,
            timestamp=datetime.now(timezone.utc).isoformat(),
            results_count=results_count,
            returned_urls=[mask_sensitive_strings(u) for u in (returned_urls or [])],
            error=mask_sensitive_strings(error) if error else None,
        )
        with self._lock:
            self.queries.append(record)
            if slot_id in self.slot_audits:
                self.slot_audits[slot_id].queries.append(record)
        return record

    def log_fetch(self, slot_id: str, fetch_record: FetchedPage) -> None:
        """Record every page fetch attempt."""
        with self._lock:
            self.fetches.append(fetch_record)
            if slot_id in self.slot_audits:
                self.slot_audits[slot_id].fetches.append(fetch_record)

    def init_slot_audit(self, slot_id: str, service_line: str, provider: str, mode: str) -> None:
        """Initialize slot audit tracking."""
        with self._lock:
            self.slot_audits[slot_id] = SlotResearchAudit(
                slot_id=slot_id,
                service_line=service_line,
                provider_name=provider,
                mode=mode,
            )

    def get_slot_audit(self, slot_id: str) -> SlotResearchAudit | None:
        """Retrieve audit record for a slot."""
        with self._lock:
            return self.slot_audits.get(slot_id)

    def build_research_records(
        self,
        slot_results: list[Any],
    ) -> list[dict[str, Any]]:
        """Generate schema-compliant research_log.json entries."""
        records: list[dict[str, Any]] = []
        for r in slot_results:
            slot_id = getattr(r.slot, "id", str(r.slot)) if hasattr(r, "slot") else str(r)
            status = getattr(r, "status", "failed")
            reason = getattr(r, "reason", None)
            topic = getattr(r, "topic", None)
            source_ids = getattr(r, "source_ids", [])
            evidence = [
                e.model_dump() if hasattr(e, "model_dump") else dict(e)
                for e in getattr(r, "evidence", [])
            ]
            records.append({
                "slot_id": slot_id,
                "topic": topic,
                "source_ids": source_ids,
                "evidence": evidence,
                "status": status,
                "reason": reason,
            })
        return records
