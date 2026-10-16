from __future__ import annotations

import re
from .schemas import Evidence, KnowledgeBase, Vulnerability


class EvidenceLookup:
    """Shared, deterministic KB skill used by Research and Reviewer."""

    def __init__(self, kb: KnowledgeBase):
        self.kb = kb
        self.calls: list[str] = []

    def select(self, focus: str | None, index: int) -> Vulnerability:
        self.calls.append("research")
        if not focus:
            return self.kb.vulnerabilities[index % len(self.kb.vulnerabilities)]
        norm_focus = focus.strip().upper()
        for item in self.kb.vulnerabilities:
            if item.id.upper() == norm_focus:
                return item
        words = set(re.findall(r"[a-z0-9]+", focus.lower())) - {"smart", "contract", "security", "vulnerability", "risk"}
        if not words:
            raise ValueError(f"No specific KB topic found for focus {focus!r}")
        matches = []
        for item in self.kb.vulnerabilities:
            # Topic routing uses vetted labels, not prose summaries that may drift
            # from pinned source quotations or carry unreviewed wording.
            haystack = f"{item.name} {item.category}".lower()
            score = len(words & set(re.findall(r"[a-z0-9]+", haystack))) / len(words)
            if score >= 0.75:
                matches.append((score, item))
        if not matches:
            raise ValueError(f"No grounded KB topic found for focus {focus!r}")
        return max(matches, key=lambda pair: pair[0])[1]

    def verify_ids(self, evidence: list[Evidence], ids: list[str]) -> list[str]:
        self.calls.append("reviewer")
        known = {item.id for item in evidence}
        return [item for item in ids if item not in known]

