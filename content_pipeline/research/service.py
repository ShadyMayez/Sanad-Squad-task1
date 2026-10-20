"""High-level marketing research service orchestrating discovery, fetching, and sufficiency gating."""
from __future__ import annotations

import re
from typing import Any
from .config import SourcesConfig, load_sources_config
from .logging import ResearchLogger
from .models import FetchedPage, SearchResult
from .provider import FixtureResearchProvider, LiveResearchProvider, ResearchProvider
from ..schemas import Evidence, Vulnerability
from ..source_authority import SourceAuthorityViolationError, TechnicalResourceBrief


class ResearchService:
    def __init__(
        self,
        config: SourcesConfig | None = None,
        provider: ResearchProvider | None = None,
        logger: ResearchLogger | None = None,
    ):
        self.config = config or load_sources_config()
        self.logger = logger or ResearchLogger()
        if provider is not None:
            self.provider = provider
        else:
            live = LiveResearchProvider(self.config)
            self.provider = live if live.is_available() else FixtureResearchProvider(self.config)

    def conduct_marketing_research(
        self,
        slot_id: str,
        service_line: str,
        topic_focus: str | None = None,
        source_group: str | None = None,
        is_vulnerability_class_exception: bool = False,
        supplemental_kb_vulnerabilities: list[Vulnerability] | None = None,
    ) -> tuple[list[Evidence], list[str], str | None]:
        """Conduct external research for a marketing post slot.
        
        Enforces:
        - Only searches within the allowlist for the service line.
        - Records every query and fetch attempt in the research log.
        - Fails closed if no current verified source is retrieved.
        - KB entries can only be supplemental under an explicit vulnerability class exception.
        """
        self.logger.init_slot_audit(
            slot_id=slot_id,
            service_line=service_line,
            provider=self.provider.provider_name,
            mode=self.provider.mode,
        )

        # 1. Construct search query
        query_text = topic_focus if topic_focus else f"{service_line} security"

        # 2. Execute allowlist-scoped search
        try:
            results = self.provider.search(
                query=query_text,
                service_line=service_line,
                group=source_group,
                max_results=5,
            )
            self.logger.log_query(
                slot_id=slot_id,
                query_text=query_text,
                service_line=service_line,
                provider_name=self.provider.provider_name,
                mode=self.provider.mode,
                results_count=len(results),
                returned_urls=[r.url for r in results],
                source_group=source_group,
            )
        except Exception as exc:
            self.logger.log_query(
                slot_id=slot_id,
                query_text=query_text,
                service_line=service_line,
                provider_name=self.provider.provider_name,
                mode=self.provider.mode,
                results_count=0,
                error=f"{type(exc).__name__}: {exc}",
            )
            return [], [], f"Search query failed: {exc}"

        if not results:
            return [], [], f"No allowlisted search results found for query '{query_text}' under service '{service_line}'."

        # 3. Fetch top candidates and verify content
        fetched_evidence: list[Evidence] = []
        source_ids: list[str] = []

        for idx, res in enumerate(results[:2]):
            fetch_res = self.provider.fetch(res.url, service_line, res.source_group or "")
            self.logger.log_fetch(slot_id, fetch_res)

            if fetch_res.http_status == 200 and fetch_res.eligible_for_public_posting:
                ev_id = f"ev_web_{service_line.replace('-', '_')}_{idx+1}"
                # Extract quote from cleaned text
                quote_text = res.snippet or fetch_res.cleaned_text[:200]
                ev_item = Evidence(
                    id=ev_id,
                    url=fetch_res.final_url,
                    excerpt=quote_text,
                    source_title=fetch_res.title or res.title,
                    source_type=f"web_research:{fetch_res.source_group or 'general'}",
                    retrieved_at=fetch_res.retrieval_timestamp,
                    source_quote=quote_text,
                    snapshot_sha256=fetch_res.sha256_checksum,
                    scope=f"service_line:{service_line}",
                )
                fetched_evidence.append(ev_item)
                source_ids.append(ev_id)

        # 4. Handle supplemental KB exception
        if is_vulnerability_class_exception and supplemental_kb_vulnerabilities:
            for v in supplemental_kb_vulnerabilities:
                for kb_ev in v.evidence:
                    # Append strictly as supplemental
                    supp_id = f"supp_{kb_ev.id}"
                    supp_item = kb_ev.model_copy(update={
                        "id": supp_id,
                        "source_type": "knowledge_base:supplemental",
                    })
                    fetched_evidence.append(supp_item)
                    source_ids.append(supp_id)

        # 5. Fail-closed sufficiency check
        primary_web_evidence = [e for e in fetched_evidence if not e.id.startswith("supp_")]
        if not primary_web_evidence:
            return (
                [],
                [],
                f"Source sufficiency failure: No verified web research pages could be retrieved for slot {slot_id}.",
            )

        return fetched_evidence, source_ids, None

    def conduct_technical_external_research(
        self,
        slot_id: str,
        url: str,
    ) -> tuple[list[Evidence], TechnicalResourceBrief | None, str | None]:
        """Fetch and verify an external technical resource for a technical thread."""
        fetch_res = self.provider.fetch(url, "web3-security")
        self.logger.log_fetch(slot_id, fetch_res)

        if fetch_res.http_status != 200 or not fetch_res.eligible_for_public_posting:
            return [], None, f"Failed to retrieve technical resource at {url}: {fetch_res.failure_reason}"

        ev_id = f"ev_tech_ext_{slot_id}"
        excerpt = fetch_res.cleaned_text[:300]
        ev_item = Evidence(
            id=ev_id,
            url=fetch_res.final_url,
            excerpt=excerpt,
            source_title=fetch_res.title,
            source_type="external_technical_resource",
            retrieved_at=fetch_res.retrieval_timestamp,
            source_quote=excerpt,
            snapshot_sha256=fetch_res.sha256_checksum,
            scope="external_technical_postmortem",
        )

        brief = TechnicalResourceBrief(
            title=fetch_res.title or "External Technical Incident Report",
            url=fetch_res.final_url,
            publisher=fetch_res.publisher,
            retrieval_timestamp=fetch_res.retrieval_timestamp,
            summary_brief=excerpt,
            key_findings=[s.strip() for s in excerpt.split(".") if len(s.strip()) > 20][:3],
            sha256_checksum=fetch_res.sha256_checksum,
        )

        return [ev_item], brief, None
