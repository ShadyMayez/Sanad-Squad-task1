"""Explicit maintenance command: fetch credited source pages and pin normalized text.

The runtime never fetches or rewrites sources. Review every generated quote before
committing an update; a reachable page and an exact substring are not truth proofs.
"""
from __future__ import annotations

import hashlib
import json
import re
from datetime import date
from html.parser import HTMLParser
from pathlib import Path
from urllib.request import Request, urlopen

ROOT = Path(__file__).resolve().parent.parent


class ArticleText(HTMLParser):
    def __init__(self):
        super().__init__()
        self.parts: list[str] = []
        self.skip: list[str] = []

    def handle_starttag(self, tag, attrs):
        if tag in {"script", "style", "nav", "footer"}:
            self.skip.append(tag)
        if tag in {"p", "h1", "h2", "h3", "li"}:
            self.parts.append(" ")

    def handle_endtag(self, tag):
        if self.skip and self.skip[-1] == tag:
            self.skip.pop()
        if tag in {"p", "h1", "h2", "h3", "li"}:
            self.parts.append(" ")

    def handle_data(self, data):
        if not self.skip:
            self.parts.append(data)


def main():
    kb_path = ROOT / "kb.json"
    kb = json.loads(kb_path.read_text())
    folder = ROOT / "source_snapshots"
    folder.mkdir(exist_ok=True)
    for topic in kb["vulnerabilities"]:
        for evidence in topic["evidence"]:
            if evidence["id"] == "SWC-107":
                raw_url = "https://raw.githubusercontent.com/SmartContractSecurity/SWC-registry/master/entries/docs/SWC-107.md"
                with urlopen(Request(raw_url, headers={"User-Agent": "SanadSquad-source-audit/1.0"}), timeout=30) as response:
                    markdown = response.read().decode("utf-8", errors="replace")
                (folder / "SWC-107-official.md").write_text(markdown)
                body = markdown.split("## Description\n\n", 1)[1].split("\n\n## References", 1)[0]
                body = re.sub(r"\[([^]]+)\]\([^)]*\)", r"\1", body)
                body = re.sub(r"  +", " ", body).rstrip() + "\n"
                source = "Source: SmartContractSecurity/SWC-registry entries/docs/SWC-107.md, normalized Markdown excerpt.\n" + body
                snapshot = folder / "SWC-107-canonical.txt"
                snapshot.write_text(source)
                evidence["snapshot_path"] = str(snapshot.relative_to(ROOT))
                evidence["snapshot_sha256"] = hashlib.sha256(snapshot.read_bytes()).hexdigest()
                evidence["retrieved_at"] = date.today().isoformat()
                evidence["source_type"] = "official registry Markdown, normalized excerpt"
                evidence["source_title"] = "SWC-107 Reentrancy, official SWC Registry"
                evidence["scope"] = "Legacy SWC guidance; check compiler and EVM applicability"
                evidence["source_quote"] = body.strip()
                evidence["quote_start"] = source.index(evidence["source_quote"])
                evidence["quote_end"] = evidence["quote_start"] + len(evidence["source_quote"])
                print(evidence["id"], len(source), len(evidence["source_quote"]))
                continue
            with urlopen(Request(evidence["url"], headers={"User-Agent": "SanadSquad-source-audit/1.0"}), timeout=30) as response:
                html = response.read().decode("utf-8", errors="replace")
            parser = ArticleText()
            parser.feed(html)
            source = re.sub(r"\s+", " ", " ".join(parser.parts)).strip()
            if len(source) < 300:
                raise ValueError(f"Source text too short: {evidence['url']}")
            snapshot = folder / f"{evidence['id']}.txt"
            snapshot.write_text(source + "\n")
            evidence["snapshot_path"] = str(snapshot.relative_to(ROOT))
            evidence["snapshot_sha256"] = hashlib.sha256(snapshot.read_bytes()).hexdigest()
            evidence["retrieved_at"] = date.today().isoformat()
            evidence["source_type"] = "SWC Registry" if "swcregistry.io" in evidence["url"] else "OWASP Smart Contract Security"
            evidence["source_title"] = topic["name"]
            evidence["scope"] = "Legacy SWC guidance; check compiler and EVM applicability" if evidence["source_type"] == "SWC Registry" else "Use the documented oracle conditions and threat model"
            if evidence["id"] == "OWASP-SC03":
                start = source.index("Aggregate multiple sources")
            else:
                start = source.find("Description ")
                if start < 0:
                    raise ValueError(f"No description section: {evidence['url']}")
            end = min(len(source), start + 1100)
            for boundary in (" References ", " Examples ", " Samples "):
                boundary_at = source.find(boundary, start + 120, end)
                if boundary_at >= 0:
                    end = min(end, boundary_at)
            # Keep a contiguous exact excerpt. A section boundary may already
            # follow a complete sentence; do not clip at an earlier "ie.".
            if source[end - 1] not in ".!?":
                stop = source.rfind(". ", start + 350, end)
                if stop > start:
                    end = stop + 1
            evidence["source_quote"] = source[start:end]
            evidence["quote_start"] = start
            evidence["quote_end"] = end
            if len(evidence["source_quote"]) < 100:
                raise ValueError(f"Source quote too short: {evidence['id']}")
            print(evidence["id"], len(source), len(evidence["source_quote"]))
    kb_path.write_text(json.dumps(kb, indent=2, ensure_ascii=False) + "\n")


if __name__ == "__main__":
    main()
