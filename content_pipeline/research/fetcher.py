"""Safe, hardened HTTPS fetcher with SSRF prevention and allowlist gating.

Enforces:
- HTTPS-only retrieval.
- Strict domain allowlist validation before request and after each redirect.
- SSRF protection: DNS resolution checking blocking private, loopback, and metadata IPs.
- Resource limits: max response size (1MB), timeout (8s), max 3 redirects.
- Safe HTML sanitization and SHA-256 checksumming.
- Prompt injection isolation: treats page text strictly as untrusted evidence data.
"""
from __future__ import annotations

import hashlib
import ipaddress
import re
import socket
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from typing import Any
from .config import SourcesConfig
from .models import FetchedPage

MAX_RESPONSE_BYTES = 1024 * 1024  # 1 MB
DEFAULT_TIMEOUT_SECONDS = 8
MAX_REDIRECTS = 3

# RFC 1918, RFC 3927 (link-local/metadata), loopback, broadcast, and reserved networks
DISALLOWED_IPV4_NETWORKS = [
    ipaddress.ip_network("0.0.0.0/8"),
    ipaddress.ip_network("10.0.0.0/8"),
    ipaddress.ip_network("100.64.0.0/10"),
    ipaddress.ip_network("127.0.0.0/8"),
    ipaddress.ip_network("169.254.0.0/16"),
    ipaddress.ip_network("172.16.0.0/12"),
    ipaddress.ip_network("192.0.0.0/24"),
    ipaddress.ip_network("192.0.2.0/24"),
    ipaddress.ip_network("192.168.0.0/16"),
    ipaddress.ip_network("198.18.0.0/15"),
    ipaddress.ip_network("198.51.100.0/24"),
    ipaddress.ip_network("203.0.113.0/24"),
    ipaddress.ip_network("224.0.0.0/4"),
    ipaddress.ip_network("240.0.0.0/4"),
    ipaddress.ip_network("255.255.255.255/32"),
]

DISALLOWED_IPV6_NETWORKS = [
    ipaddress.ip_network("::/128"),
    ipaddress.ip_network("::1/128"),
    ipaddress.ip_network("fc00::/7"),  # Unique local
    ipaddress.ip_network("fe80::/10"),  # Link-local
    ipaddress.ip_network("ff00::/8"),  # Multicast
]


class SSRFViolationError(PermissionError):
    """Raised when an external request attempts to target an internal or reserved IP."""
    pass


class FetchSecurityError(PermissionError):
    """Raised when an external fetch violates allowlist, protocol, or redirect policy."""
    pass


class SafeFetcher:
    def __init__(
        self,
        sources_config: SourcesConfig | None = None,
        timeout: int = DEFAULT_TIMEOUT_SECONDS,
        max_bytes: int = MAX_RESPONSE_BYTES,
    ):
        from .config import load_sources_config
        self.config = sources_config or load_sources_config()
        self.timeout = timeout
        self.max_bytes = max_bytes

    def is_ip_disallowed(self, ip_str: str) -> bool:
        """Verify whether an IP address belongs to private or reserved ranges."""
        try:
            ip = ipaddress.ip_address(ip_str)
            if ip.version == 4:
                return any(ip in net for net in DISALLOWED_IPV4_NETWORKS)
            else:
                return any(ip in net for net in DISALLOWED_IPV6_NETWORKS)
        except ValueError:
            return True

    def verify_host_safety(self, hostname: str) -> None:
        """Resolve DNS and assert that target IP is not private or loopback."""
        clean_host = hostname.strip().lower()
        if clean_host in {"localhost", "metadata.google.internal", "instance-data"}:
            raise SSRFViolationError(f"Host '{hostname}' is a forbidden local/metadata endpoint.")

        # Check if host is direct IP
        try:
            ipaddress.ip_address(clean_host)
            if self.is_ip_disallowed(clean_host):
                raise SSRFViolationError(f"IP address '{clean_host}' is private or reserved.")
            return
        except ValueError:
            pass

        # Resolve DNS
        try:
            addr_info = socket.getaddrinfo(clean_host, None)
            for item in addr_info:
                ip_str = item[4][0]
                if self.is_ip_disallowed(ip_str):
                    raise SSRFViolationError(
                        f"Host '{hostname}' resolved to private/reserved IP: {ip_str}"
                    )
        except socket.gaierror as exc:
            raise FetchSecurityError(f"DNS resolution failed for '{hostname}': {exc}") from exc

    def sanitize_html_to_text(self, html_content: str) -> str:
        """Extract clean text content from HTML without executing scripts or tags."""
        # 1. Remove script and style blocks
        no_scripts = re.sub(r"<(script|style|noscript|svg)[^>]*>.*?</\1>", " ", html_content, flags=re.DOTALL | re.IGNORECASE)
        # 2. Remove comments
        no_comments = re.sub(r"<!--.*?-->", " ", no_scripts, flags=re.DOTALL)
        # 3. Strip HTML tags
        clean_text = re.sub(r"<[^>]+>", " ", no_comments)
        # 4. Normalize whitespace
        clean_text = " ".join(clean_text.split())
        return clean_text

    def extract_title(self, html_content: str) -> str:
        """Extract page <title> text."""
        match = re.search(r"<title[^>]*>(.*?)</title>", html_content, flags=re.DOTALL | re.IGNORECASE)
        if match:
            return " ".join(match.group(1).split())
        return ""

    def fetch_url(
        self,
        url: str,
        service_line: str,
        source_group: str = "",
    ) -> FetchedPage:
        """Fetch URL with full security gating, redirect checking, and logging."""
        timestamp = datetime.now(timezone.utc).isoformat()

        # 1. Enforce HTTPS only
        parsed = urllib.parse.urlparse(url)
        if parsed.scheme.lower() != "https":
            return FetchedPage(
                requested_url=url,
                final_url=url,
                http_status=400,
                retrieval_timestamp=timestamp,
                eligible_for_public_posting=False,
                failure_reason=f"Insecure protocol '{parsed.scheme}'. Only HTTPS is permitted.",
                service_line=service_line,
                source_group=source_group,
            )

        # 2. Check initial domain allowlist
        if not self.config.is_domain_allowed(url, service_line):
            return FetchedPage(
                requested_url=url,
                final_url=url,
                http_status=403,
                retrieval_timestamp=timestamp,
                eligible_for_public_posting=False,
                failure_reason=f"Domain '{parsed.netloc}' is not in allowlist for service '{service_line}' or is denied.",
                service_line=service_line,
                source_group=source_group,
            )

        # 3. Check DNS / SSRF safety
        try:
            self.verify_host_safety(parsed.hostname or "")
        except (SSRFViolationError, FetchSecurityError) as sec_err:
            return FetchedPage(
                requested_url=url,
                final_url=url,
                http_status=403,
                retrieval_timestamp=timestamp,
                eligible_for_public_posting=False,
                failure_reason=f"Security gate rejected host: {sec_err}",
                service_line=service_line,
                source_group=source_group,
            )

        # 4. Fetch with redirect tracking and hop verification
        current_url = url
        redirects: list[str] = []

        class SecureRedirectHandler(urllib.request.HTTPRedirectHandler):
            def __init__(self, fetcher: SafeFetcher, s_line: str):
                super().__init__()
                self.fetcher = fetcher
                self.service_line = s_line
                self.redirect_count = 0

            def redirect_request(self, req, fp, code, msg, headers, newurl):
                self.redirect_count += 1
                if self.redirect_count > MAX_REDIRECTS:
                    raise urllib.error.HTTPError(
                        req.full_url, 310, "Too many redirects", headers, fp
                    )
                new_parsed = urllib.parse.urlparse(newurl)
                if new_parsed.scheme.lower() != "https":
                    raise FetchSecurityError(f"Redirect to non-HTTPS URL: {newurl}")
                if not self.fetcher.config.is_domain_allowed(newurl, self.service_line):
                    raise FetchSecurityError(f"Redirect outside allowlist to domain: {new_parsed.netloc}")
                self.fetcher.verify_host_safety(new_parsed.hostname or "")
                redirects.append(newurl)
                return super().redirect_request(req, fp, code, msg, headers, newurl)

        opener = urllib.request.build_opener(SecureRedirectHandler(self, service_line))
        req = urllib.request.Request(
            url,
            headers={
                "User-Agent": "SanadSquad-Research-Agent/3.0 (+https://sanadsquad.com/bot; security-research)",
                "Accept": "text/html,application/xhtml+xml;q=0.9,*/*;q=0.8",
            },
        )

        try:
            with opener.open(req, timeout=self.timeout) as response:
                status_code = response.getcode()
                final_url = response.geturl()

                # Read capped response bytes
                content_bytes = response.read(self.max_bytes + 1)
                if len(content_bytes) > self.max_bytes:
                    return FetchedPage(
                        requested_url=url,
                        final_url=final_url,
                        http_status=413,
                        redirects=redirects,
                        retrieval_timestamp=timestamp,
                        eligible_for_public_posting=False,
                        failure_reason=f"Response exceeded size limit ({self.max_bytes} bytes).",
                        service_line=service_line,
                        source_group=source_group,
                    )

                # Decode HTML
                charset = response.headers.get_content_charset() or "utf-8"
                try:
                    html_text = content_bytes.decode(charset, errors="replace")
                except Exception:
                    html_text = content_bytes.decode("utf-8", errors="replace")

                sha256 = hashlib.sha256(content_bytes).hexdigest()
                cleaned = self.sanitize_html_to_text(html_text)
                title = self.extract_title(html_text)

                return FetchedPage(
                    requested_url=url,
                    final_url=final_url,
                    http_status=status_code,
                    redirects=redirects,
                    retrieval_timestamp=timestamp,
                    title=title,
                    publisher=urllib.parse.urlparse(final_url).netloc,
                    cleaned_text=cleaned,
                    sha256_checksum=sha256,
                    content_length=len(content_bytes),
                    eligible_for_public_posting=True,
                    service_line=service_line,
                    source_group=source_group,
                )

        except urllib.error.HTTPError as http_err:
            return FetchedPage(
                requested_url=url,
                final_url=current_url,
                http_status=http_err.code,
                redirects=redirects,
                retrieval_timestamp=timestamp,
                eligible_for_public_posting=False,
                failure_reason=f"HTTP {http_err.code}: {http_err.reason}",
                service_line=service_line,
                source_group=source_group,
            )
        except Exception as exc:
            return FetchedPage(
                requested_url=url,
                final_url=current_url,
                http_status=500,
                redirects=redirects,
                retrieval_timestamp=timestamp,
                eligible_for_public_posting=False,
                failure_reason=f"Fetch failed: {type(exc).__name__}: {exc}",
                service_line=service_line,
                source_group=source_group,
            )
