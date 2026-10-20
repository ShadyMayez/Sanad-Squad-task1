"""Data models for marketing research queries, page fetches, and audit records."""
from __future__ import annotations

from typing import Literal
from pydantic import BaseModel, Field
from ..schemas import Evidence


class SearchResult(BaseModel):
    title: str
    url: str
    domain: str
    snippet: str
    published_date: str | None = None
    service_line: str
    source_group: str | None = None


class FetchedPage(BaseModel):
    requested_url: str
    final_url: str
    http_status: int
    redirects: list[str] = Field(default_factory=list)
    retrieval_timestamp: str
    title: str = ""
    publisher: str = ""
    publication_date: str | None = None
    cleaned_text: str = ""
    sha256_checksum: str = ""
    content_length: int = 0
    eligible_for_public_posting: bool = True
    failure_reason: str | None = None
    service_line: str = ""
    source_group: str = ""
    is_fixture: bool = False
    is_fresh_for_current_news: bool = True

    @property
    def domain(self) -> str:
        import urllib.parse
        return urllib.parse.urlparse(self.final_url).netloc.lower()


class ResearchQueryRecord(BaseModel):
    query_id: str
    slot_id: str
    query_text: str
    service_line: str
    source_group: str | None = None
    provider_name: str
    mode: str
    timestamp: str
    results_count: int
    returned_urls: list[str] = Field(default_factory=list)
    error: str | None = None


class SlotResearchAudit(BaseModel):
    slot_id: str
    service_line: str
    provider_name: str
    mode: str
    queries: list[ResearchQueryRecord] = Field(default_factory=list)
    fetches: list[FetchedPage] = Field(default_factory=list)
    extracted_evidence: list[Evidence] = Field(default_factory=list)
    sufficiency_passed: bool = False
    failure_reason: str | None = None
