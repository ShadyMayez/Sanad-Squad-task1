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


def located_source_options(quote: str) -> list[tuple[str, int, int]]:
    """Return exact option text with offsets within its pinned source quotation."""
    located = []
    cursor = 0
    for span in source_span_options(quote):
        start = quote.find(span, cursor)
        if start < 0:
            raise ValueError("source span cannot be located in its quotation")
        end = start + len(span)
        located.append((span, start, end))
        cursor = end
    return located


def bounded_context(quote: str, option_index: int, radius: int = 2, max_chars: int = 1400,
                    max_token_upper_bound: int = 1400) -> tuple[str, int, int, bool]:
    """Bound context by characters and UTF-8 bytes, a conservative token upper bound."""
    options = located_source_options(quote)
    if not 0 <= option_index < len(options):
        raise ValueError("unknown source span index")
    left = right = option_index
    budget_limited = False
    for distance in range(1, radius + 1):
        for direction in (-1, 1):
            candidate = option_index + direction * distance
            if 0 <= candidate < len(options):
                between = range(min(candidate, option_index) + 1, max(candidate, option_index) + 1)
                if any(options[i][0].lstrip().lower().startswith("remediation") for i in between):
                    continue
                new_left, new_right = min(left, candidate), max(right, candidate)
                candidate_text = quote[options[new_left][1]:options[new_right][2]]
                if len(candidate_text) <= max_chars and len(candidate_text.encode("utf-8")) <= max_token_upper_bound:
                    left, right = new_left, new_right
                else:
                    budget_limited = True
    start, end = options[left][1], options[right][2]
    if end - start > max_chars or len(quote[start:end].encode("utf-8")) > max_token_upper_bound:
        # A single source sentence may exceed the budget. Keep the selected
        # span intact and signal the exceptional over-budget context.
        return quote[start:end], start, end, True
    return quote[start:end], start, end, budget_limited
