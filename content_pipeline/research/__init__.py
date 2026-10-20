"""SanadSquad Marketing Research Subsystem.

Provides source configuration, safe web fetching, live & fixture providers,
and full query/retrieval audit logging.
"""
from .config import load_sources_config, SourcesConfig
from .provider import ResearchProvider, LiveResearchProvider, FixtureResearchProvider
from .service import ResearchService
from .fetcher import SafeFetcher
from .logging import ResearchLogger

__all__ = [
    "load_sources_config",
    "SourcesConfig",
    "ResearchProvider",
    "LiveResearchProvider",
    "FixtureResearchProvider",
    "ResearchService",
    "SafeFetcher",
    "ResearchLogger",
]
