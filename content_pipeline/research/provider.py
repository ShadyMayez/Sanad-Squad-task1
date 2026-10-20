"""Research provider interface and implementations for live and offline fixture modes."""
from __future__ import annotations

import abc
import hashlib
import os
from datetime import datetime, timezone
from typing import Any
from .config import SourcesConfig
from .fetcher import SafeFetcher
from .fixtures import get_all_fixtures, get_fixtures_for_service
from .models import FetchedPage, SearchResult


class ResearchProvider(abc.ABC):
    """Abstract interface for marketing research search and retrieval."""

    @property
    @abc.abstractmethod
    def provider_name(self) -> str:
        """Name of the research provider (e.g. 'live_https_search', 'offline_fixture')."""
        pass

    @property
    @abc.abstractmethod
    def mode(self) -> str:
        """Mode of the provider: 'live' or 'fixture'."""
        pass

    @abc.abstractmethod
    def is_available(self) -> bool:
        """Check if provider is available and ready for execution."""
        pass

    @abc.abstractmethod
    def search(
        self,
        query: str,
        service_line: str,
        group: str | None = None,
        max_results: int = 5,
    ) -> list[SearchResult]:
        """Perform search query scoped strictly to the service line allowlist."""
        pass

    @abc.abstractmethod
    def fetch(
        self,
        url: str,
        service_line: str,
        source_group: str = "",
    ) -> FetchedPage:
        """Fetch and verify page content from allowlisted source URL."""
        pass


class LiveResearchProvider(ResearchProvider):
    """Live external research provider executing real HTTPS queries against allowlisted domains."""

    def __init__(
        self,
        sources_config: SourcesConfig,
        api_key: str | None = None,
        search_endpoint: str | None = None,
    ):
        self.config = sources_config
        self.api_key = api_key or os.getenv("SANADSQUAD_SEARCH_API_KEY")
        self.search_endpoint = search_endpoint or os.getenv("SANADSQUAD_SEARCH_ENDPOINT")
        self.fetcher = SafeFetcher(sources_config)

    @property
    def provider_name(self) -> str:
        return "live_https_search"

    @property
    def mode(self) -> str:
        return "live"

    def is_available(self) -> bool:
        """Available only when a live search API key or endpoint is configured."""
        return bool(self.api_key or self.search_endpoint)

    def search(
        self,
        query: str,
        service_line: str,
        group: str | None = None,
        max_results: int = 5,
    ) -> list[SearchResult]:
        if not self.is_available():
            raise RuntimeError(
                "LiveResearchProvider is unavailable: no search API key or endpoint configured. "
                "Set SANADSQUAD_SEARCH_API_KEY or use FixtureResearchProvider."
            )

        # Scoped allowlist domains
        allowed_domains = self.config.get_service_allowlist(service_line, group)
        if not allowed_domains:
            return []

        # In live mode with configured API, query scoped search
        # Simulated live search query scoped to allowed domains:
        site_filter = " OR ".join(f"site:{d}" for d in allowed_domains[:5])
        scoped_query = f"{query} ({site_filter})"

        # If live HTTP search is configured, query endpoint; otherwise raise explicit error
        # rather than faking search results
        raise NotImplementedError(
            f"Live search API integration configured with key, but endpoint '{self.search_endpoint}' "
            "requires live network execution."
        )

    def fetch(
        self,
        url: str,
        service_line: str,
        source_group: str = "",
    ) -> FetchedPage:
        # Live fetch executes through safe, hardened HTTPS fetcher
        return self.fetcher.fetch_url(url, service_line, source_group)


class FixtureResearchProvider(ResearchProvider):
    """Deterministic offline fixture provider using verified public-domain evidence."""

    def __init__(self, sources_config: SourcesConfig):
        self.config = sources_config
        self.fixtures = get_all_fixtures()

    @property
    def provider_name(self) -> str:
        return "offline_fixture"

    @property
    def mode(self) -> str:
        return "fixture"

    def is_available(self) -> bool:
        return True

    def search(
        self,
        query: str,
        service_line: str,
        group: str | None = None,
        max_results: int = 5,
    ) -> list[SearchResult]:
        allowed_domains = set(self.config.get_service_allowlist(service_line, group))
        candidates = get_fixtures_for_service(service_line)

        import re
        q_terms = [t.lower() for t in re.findall(r"\w+", query) if len(t) > 2]

        scored: list[tuple[int, SearchResult]] = []
        for item in candidates:
            target_check = item.get("url") or item["domain"]
            if not self.config.is_domain_allowed(target_check, service_line):
                continue

            combined_text = (item["title"] + " " + item["cleaned_text"]).lower()
            score = sum(1 for term in q_terms if term in combined_text)
            res = SearchResult(
                title=item["title"],
                url=item["url"],
                domain=item["domain"],
                snippet=item["quote"],
                published_date=item.get("published_date"),
                service_line=item["service_line"],
                source_group=item.get("source_group"),
            )
            scored.append((score, res))

        scored.sort(key=lambda x: x[0], reverse=True)
        if q_terms:
            results = [res for s, res in scored if s > 0]
        else:
            results = [res for s, res in scored]
        return results[:max_results]

    def fetch(
        self,
        url: str,
        service_line: str,
        source_group: str = "",
    ) -> FetchedPage:
        # Match against fixtures
        timestamp = datetime.now(timezone.utc).isoformat()
        clean_url = url.strip()

        # Check domain allowlist
        if not self.config.is_domain_allowed(clean_url, service_line):
            return FetchedPage(
                requested_url=clean_url,
                final_url=clean_url,
                http_status=403,
                retrieval_timestamp=timestamp,
                eligible_for_public_posting=False,
                failure_reason=f"Domain not authorized for service line '{service_line}'.",
                service_line=service_line,
                source_group=source_group,
                is_fixture=True,
            )

        for item in self.fixtures:
            if item["url"] == clean_url:
                cleaned = item["cleaned_text"]
                sha256 = hashlib.sha256(cleaned.encode("utf-8")).hexdigest()
                return FetchedPage(
                    requested_url=clean_url,
                    final_url=clean_url,
                    http_status=200,
                    retrieval_timestamp=timestamp,
                    title=item["title"],
                    publisher=item["publisher"],
                    publication_date=item.get("published_date"),
                    cleaned_text=cleaned,
                    sha256_checksum=sha256,
                    content_length=len(cleaned.encode("utf-8")),
                    eligible_for_public_posting=True,
                    service_line=service_line,
                    source_group=source_group or item.get("source_group", ""),
                    is_fixture=True,
                )

        return FetchedPage(
            requested_url=clean_url,
            final_url=clean_url,
            http_status=404,
            retrieval_timestamp=timestamp,
            eligible_for_public_posting=False,
            failure_reason=f"Fixture not found for URL: {clean_url}",
            service_line=service_line,
            source_group=source_group,
            is_fixture=True,
        )
