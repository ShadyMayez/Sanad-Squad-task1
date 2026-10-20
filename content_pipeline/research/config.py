"""Source configuration parser and domain authority validator.

Directive: SANADSQUAD_V3_OFFICIAL_BRAND_INTEGRATION_01

Loads sources.json (with source.json alias support) and enforces
strict domain allowlisting and denylisting across the 4 SanadSquad research categories,
while supporting all 5 official commercial services:
1. Blockchain security audits (blockchain-security-audits) -> web3-security
2. Penetration testing (penetration-testing) -> pentesting
3. Agentic security tooling (agentic-security-tooling) -> agentic-security
4. Agentic payments (agentic-payments) -> agentic-payments
5. Security consulting (security-consulting) -> web3-security / cross-cutting
"""
from __future__ import annotations

import json
from pathlib import Path
from urllib.parse import urlparse
from typing import Any
from pydantic import BaseModel, Field, model_validator
from ..config import ROOT

DEFAULT_SOURCES_PATH = ROOT / "sources.json"
ALIAS_SOURCES_PATH = ROOT / "source.json"

REQUIRED_SERVICE_LINES = {
    "web3-security",
    "pentesting",
    "agentic-security",
    "agentic-payments",
}

REQUIRED_SOURCE_GROUPS = {
    "blogs",
    "docs",
    "production",
    "analysis",
    "figures",
}

COMMERCIAL_TO_RESEARCH_MAP = {
    "blockchain-security-audits": "web3-security",
    "penetration-testing": "pentesting",
    "agentic-security-tooling": "agentic-security",
    "agentic-payments": "agentic-payments",
    "security-consulting": "web3-security",
    "consulting": "web3-security",
    "web3-security": "web3-security",
    "pentesting": "pentesting",
    "agentic-security": "agentic-security",
}


class ServiceLineSources(BaseModel):
    description: str = ""
    blogs: list[str] = Field(default_factory=list)
    docs: list[str] = Field(default_factory=list)
    production: list[str] = Field(default_factory=list)
    analysis: list[str] = Field(default_factory=list)
    figures: list[str] = Field(default_factory=list)

    def all_domains(self) -> set[str]:
        return set(self.blogs + self.docs + self.production + self.analysis + self.figures)


class SourcesConfig(BaseModel):
    model_config = {"populate_by_name": True}

    version: str = "2.0.0"
    service_lines: dict[str, ServiceLineSources]
    deny: list[str] = Field(default_factory=list, alias="_deny")

    @model_validator(mode="before")
    @classmethod
    def _normalize_deny(cls, data: Any) -> Any:
        if isinstance(data, dict):
            if "_deny" not in data:
                if "global_deny" in data:
                    data["_deny"] = data["global_deny"]
                elif "deny" in data:
                    data["_deny"] = data["deny"]
        return data

    def get_service_allowlist(self, service_line: str, group: str | None = None) -> list[str]:
        """Return allowed domains for a service line and optional source group."""
        norm_line = COMMERCIAL_TO_RESEARCH_MAP.get(service_line.lower().strip(), service_line.lower().strip())
        if norm_line not in self.service_lines:
            raise KeyError(f"Unknown service line '{service_line}'. Expected one of: {list(self.service_lines)}")
        sl = self.service_lines[norm_line]
        if group:
            if not hasattr(sl, group):
                raise KeyError(f"Unknown source group '{group}'. Expected one of: {list(REQUIRED_SOURCE_GROUPS)}")
            domains = getattr(sl, group)
        else:
            domains = sorted(list(sl.all_domains()))

        # Filter out anything on the global deny list
        deny_set = {d.lower() for d in self.deny}
        return [d for d in domains if d.lower() not in deny_set]

    def get_cross_service_allowlist(self, service_lines: list[str]) -> list[str]:
        """Combine allowlists for cross-service topics with denylist filtering."""
        combined: set[str] = set()
        for sl in service_lines:
            combined.update(self.get_service_allowlist(sl))
        return sorted(list(combined))

    def is_domain_allowed(self, url_or_domain: str, service_lines: list[str] | str) -> bool:
        """Check if a domain or URL is authorized under the specified service line(s)."""
        domain = self.extract_domain(url_or_domain).lower()
        if not domain:
            return False

        # 1. Global denylist check (denylist always overrides allowlist)
        for denied in self.deny:
            denied_norm = denied.lower().strip()
            if domain == denied_norm or domain.endswith("." + denied_norm):
                return False

        # 2. Service allowlist check
        target_lines = [service_lines] if isinstance(service_lines, str) else service_lines
        allowed_domains = self.get_cross_service_allowlist(target_lines)

        url_lower = url_or_domain.lower().strip()
        if "://" in url_lower:
            url_path_part = url_lower.split("://", 1)[1].rstrip("/")
        else:
            url_path_part = url_lower.rstrip("/")

        for allowed in allowed_domains:
            allowed_norm = allowed.lower().strip().rstrip("/")
            if "/" in allowed_norm:
                # Path-scoped allowlist (e.g. github.com/coinbase/x402)
                if url_path_part == allowed_norm or url_path_part.startswith(allowed_norm + "/"):
                    return True
            else:
                # Hostname-scoped allowlist (e.g. solana.com, owasp.org)
                if domain == allowed_norm or domain.endswith("." + allowed_norm):
                    return True

        return False

    @staticmethod
    def extract_domain(url_or_domain: str) -> str:
        """Extract clean hostname from URL or raw domain string."""
        raw = url_or_domain.strip()
        if not raw:
            return ""
        if "://" in raw:
            parsed = urlparse(raw)
            return (parsed.hostname or "").lower()
        # Might be a raw domain or path
        domain_part = raw.split("/")[0].split(":")[0]
        return domain_part.lower()


def load_sources_config(path: Path | None = None) -> SourcesConfig:
    """Load canonical sources.json configuration with validation."""
    source_file = path or DEFAULT_SOURCES_PATH
    if not source_file.exists() and ALIAS_SOURCES_PATH.exists():
        source_file = ALIAS_SOURCES_PATH

    if not source_file.exists():
        raise FileNotFoundError(f"Marketing sources configuration not found at: {source_file}")

    with source_file.open("r", encoding="utf-8") as f:
        data = json.load(f)

    # Validate that all required service lines exist
    sl_data = data.get("service_lines", {})
    missing_sl = REQUIRED_SERVICE_LINES - set(sl_data.keys())
    if missing_sl:
        raise ValueError(f"sources.json is missing required service line(s): {missing_sl}")

    # Validate source groups within each service line
    for sl_name, sl_obj in sl_data.items():
        missing_groups = REQUIRED_SOURCE_GROUPS - set(sl_obj.keys())
        if missing_groups:
            raise ValueError(f"sources.json service line '{sl_name}' is missing source group(s): {missing_groups}")

    return SourcesConfig.model_validate(data)
