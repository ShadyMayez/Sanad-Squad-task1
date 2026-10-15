"""Span-preserving sentence boundaries for public copy and pinned sources."""
from __future__ import annotations

import re

ABBREVIATION = re.compile(r"(?<!\w)(?:a\.k\.a\.|i\.e\.|e\.g\.|ie\.)(?=\s|\))", re.IGNORECASE)
SENTENCE = re.compile(r"[^.!?]+(?:[.!?](?!\S)|$)")
SOURCE_BOUNDARY = re.compile(r"(?<=[.!?])\s+|\n(?=\s*[-*]\s)|\n(?=##\s)")


def masked_abbreviations(text: str) -> str:
    """Hide abbreviation periods without changing string offsets."""
    chars = list(text)
    for match in ABBREVIATION.finditer(text):
        for index in range(match.start(), match.end()):
            if chars[index] == ".":
                chars[index] = "∶"
    return "".join(chars)


def sentence_matches(text: str):
    masked = masked_abbreviations(text)
    return SENTENCE.finditer(masked)


def source_span_options(quote: str) -> list[str]:
    """Split prose and Markdown bullets; return only exact contiguous substrings."""
    masked = masked_abbreviations(quote)
    boundaries = list(SOURCE_BOUNDARY.finditer(masked))
    spans = []
    for start, end in zip([0] + [m.end() for m in boundaries],
                          [m.start() for m in boundaries] + [len(quote)]):
        span = quote[start:end].strip()
        if span.startswith(("- ", "* ")):
            span = span[2:].strip()
        if span and not span.startswith("## "):
            spans.append(span)
    return spans
