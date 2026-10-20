"""Deterministic checks for human writing quality and anti-AI markers.

Enforces rules defined in writing-quality-rules.json:
- Banned characters (em dash, en dash separator, curly quotes, emoji, obfuscation)
- Banned vocabulary (14+ terms loaded from config with word-boundary normalization)
- Banned constructions (negative parallelism, copula avoidance, filler openers)
- Rule of three repeated parallelism heuristic
- Hedging density metric
- Sentence-length distribution and variance logging
"""
from __future__ import annotations

import json
import math
import re
import unicodedata
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any
from .config import ROOT

DEFAULT_RULES_PATH = ROOT / "writing-quality-rules.json"

# Common emoji unicode ranges
EMOJI_PATTERN = re.compile(
    "["
    "\U0001F600-\U0001F64F"  # emoticons
    "\U0001F300-\U0001F5FF"  # symbols & pictographs
    "\U0001F680-\U0001F6FF"  # transport & map symbols
    "\U0001F700-\U0001F77F"  # alchemical symbols
    "\U0001F780-\U0001F7FF"  # geometric shapes extended
    "\U0001F800-\U0001F8FF"  # supplemental arrows-c
    "\U0001F900-\U0001F9FF"  # supplemental symbols and pictographs
    "\U0001FA00-\U0001FA6F"  # chess symbols
    "\U0001FA70-\U0001FAFF"  # symbols and pictographs extended-a
    "\U00002600-\U000026FF"  # miscellaneous symbols
    "\U00002700-\U000027BF"  # dingbats
    "\U0001F1E6-\U0001F1FF"  # flags (iOS)
    "]+",
    flags=re.UNICODE,
)

ZERO_WIDTH_CHARS = {"\u200b", "\u200c", "\u200d", "\ufeff", "\u00ad"}


@dataclass
class SentenceVarianceReport:
    sentence_count: int
    sentence_lengths: list[int]
    mean_length: float
    variance: float
    std_dev: float
    is_evaluable: bool
    note: str = ""

    def model_dump(self) -> dict[str, Any]:
        return {
            "sentence_count": self.sentence_count,
            "sentence_lengths": self.sentence_lengths,
            "mean_length": self.mean_length,
            "variance": self.variance,
            "std_dev": self.std_dev,
            "is_evaluable": self.is_evaluable,
            "note": self.note,
        }

    def to_dict(self) -> dict[str, Any]:
        return self.model_dump()


@dataclass
class WritingQualityReport:
    passed: bool
    errors: list[str] = field(default_factory=list)
    hedging_density_per_100: float = 0.0
    hedge_word_count: int = 0
    total_words: int = 0
    sentence_variance: SentenceVarianceReport | None = None
    rule_of_three_occurrences: int = 0

    def model_dump(self) -> dict[str, Any]:
        return {
            "passed": self.passed,
            "errors": self.errors,
            "hedging_density_per_100": self.hedging_density_per_100,
            "hedge_word_count": self.hedge_word_count,
            "total_words": self.total_words,
            "sentence_variance": self.sentence_variance.model_dump() if self.sentence_variance else None,
            "rule_of_three_occurrences": self.rule_of_three_occurrences,
        }

    def to_dict(self) -> dict[str, Any]:
        return self.model_dump()



def load_writing_quality_rules(path: Path | None = None) -> dict[str, Any]:
    rules_file = path or DEFAULT_RULES_PATH
    if not rules_file.exists():
        raise FileNotFoundError(f"Writing quality rules file not found: {rules_file}")
    with rules_file.open("r", encoding="utf-8") as f:
        return json.load(f)


def strip_zero_width_chars(text: str) -> str:
    """Remove hidden zero-width obfuscation characters."""
    return "".join(c for c in text if c not in ZERO_WIDTH_CHARS)


def split_sentences(text: str) -> list[str]:
    """Split text into sentences while respecting common abbreviations."""
    clean = text.strip()
    if not clean:
        return []
    # Avoid splitting on common abbreviations like e.g., i.e., vs.
    sentences = re.split(r"(?<=[.!?])\s+(?=[A-Z0-9])", clean)
    return [s.strip() for s in sentences if s.strip()]


def calculate_sentence_variance(text: str, min_required: int = 2) -> SentenceVarianceReport:
    """Calculate sentence-length variance in words.
    
    If fewer than min_required sentences exist, logs the metric honestly
    without calculating artificial statistical variance.
    """
    sentences = split_sentences(text)
    if len(sentences) < min_required:
        lengths = [len(re.findall(r"\b\w+\b", s)) for s in sentences]
        mean = float(lengths[0]) if lengths else 0.0
        return SentenceVarianceReport(
            sentence_count=len(sentences),
            sentence_lengths=lengths,
            mean_length=mean,
            variance=0.0,
            std_dev=0.0,
            is_evaluable=False,
            note=f"Post has {len(sentences)} sentence(s); variance requires >= {min_required} sentences.",
        )

    lengths = [len(re.findall(r"\b\w+\b", s)) for s in sentences]
    n = len(lengths)
    mean = sum(lengths) / n
    var = sum((x - mean) ** 2 for x in lengths) / n
    std = math.sqrt(var)

    return SentenceVarianceReport(
        sentence_count=n,
        sentence_lengths=lengths,
        mean_length=round(mean, 2),
        variance=round(var, 2),
        std_dev=round(std, 2),
        is_evaluable=True,
        note="Evaluated over complete sentence distribution.",
    )


def count_hedging(text: str, hedge_words: list[str]) -> tuple[int, int, float]:
    """Count hedge words and compute density per 100 words."""
    words = re.findall(r"\b\w+\b", text.lower())
    total_words = len(words)
    if total_words == 0:
        return 0, 0, 0.0

    hedge_set = {w.lower() for w in hedge_words}
    count = sum(1 for w in words if w in hedge_set)
    density = (count / total_words) * 100.0
    return count, total_words, round(density, 2)


def detect_rule_of_three(text: str) -> list[str]:
    """Heuristic for detecting coordinate three-part parallel constructions.
    
    Identifies patterns like:
    'X, Y, and Z' or 'X, Y, or Z'
    where X, Y, Z are distinct coordinated noun phrases or predicates.
    """
    matches = []
    sentences = split_sentences(text)
    pattern = re.compile(
        r"\b([\w\s'-]+),\s+([\w\s'-]+),\s+(?:and|or)\s+([\w\s'-]+)\b",
        re.IGNORECASE,
    )
    for s in sentences:
        for m in pattern.finditer(s):
            part1, part2, part3 = m.group(1).strip(), m.group(2).strip(), m.group(3).strip()
            # Validate that parts are non-trivial phrases and not numbers or dates
            if (
                len(part1) >= 2
                and len(part2) >= 2
                and len(part3) >= 2
                and not (part1.isdigit() and part2.isdigit() and part3.isdigit())
            ):
                matches.append(m.group(0))
    return matches


def detect_banned_characters(text: str, rules: dict[str, Any] | None = None) -> list[str]:
    """Detect banned em dash, separator en dash, curly quotes, and emoji."""
    if rules is None:
        rules = load_writing_quality_rules()
    errors: list[str] = []
    clean_text = strip_zero_width_chars(text)

    banned_chars = rules.get("banned_characters", [])
    for char in banned_chars:
        if char in text:
            char_name = unicodedata.name(char, f"U+{ord(char):04X}")
            if char == "—":
                errors.append(f"Contains banned em dash '{char}'")
            elif char in ("“", "”"):
                errors.append(f"Contains banned curly double quotes '{char}'")
            elif char in ("‘", "’"):
                errors.append(f"Contains banned curly apostrophe/single quote '{char}'")
            else:
                errors.append(f"Contains banned character '{char}' ({char_name})")

    # Separator en-dash check (e.g. "word – word" or with surrounding spaces)
    if re.search(r"\s+–\s+|\b–\b", text):
        if not any("en dash" in err for err in errors):
            errors.append("Contains banned separator en dash '–'")

    # Simulated em-dash obfuscation (e.g. three hyphens or two hyphens used as separator)
    if re.search(r"(?:---|--)\s+", clean_text) or re.search(r"\s+(?:---|--)", clean_text):
        errors.append("Contains simulated em dash ('--' or '---' used as separator)")

    # Emoji check
    if rules.get("forbid_emoji", True):
        emoji_matches = EMOJI_PATTERN.findall(text)
        if emoji_matches:
            errors.append(f"Contains banned emoji: {emoji_matches[0]}")

    return errors


def detect_banned_vocabulary(text: str, rules: dict[str, Any] | None = None) -> list[str]:
    """Detect 14+ banned buzzwords using word-boundary matching."""
    if rules is None:
        rules = load_writing_quality_rules()
    errors: list[str] = []
    clean_text = strip_zero_width_chars(text)
    banned_vocab = rules.get("banned_vocabulary", [])

    for term in banned_vocab:
        term_clean = term.strip().lower()
        stem = re.sub(r"e$", "", term_clean)
        pattern = rf"\b(?:{re.escape(term_clean)}|{re.escape(stem)}(?:ing|ed|s|es|ly)?)\b"
        if re.search(pattern, clean_text, re.IGNORECASE):
            errors.append(f"Contains banned vocabulary '{term}'")

    return errors


def detect_banned_constructions(text: str, rules: dict[str, Any] | None = None) -> list[str]:
    """Detect negative parallelism, copula avoidance, and canned filler openers."""
    if rules is None:
        rules = load_writing_quality_rules()
    errors: list[str] = []
    clean_text = strip_zero_width_chars(text)
    banned_constructions = rules.get("banned_constructions", [])

    for construction in banned_constructions:
        name = construction.get("name", "construction")
        reason = construction.get("reason", "")
        for pat in construction.get("patterns", []):
            if re.search(pat, clean_text, re.IGNORECASE | re.MULTILINE):
                errors.append(f"Banned construction ({name}): {reason}")
                break

    return errors


def detect_repeated_rule_of_three(text: str, max_allowed: int = 1) -> tuple[bool, int]:
    """Check if three-part coordinate parallel construction repeats within a piece."""
    clean_text = strip_zero_width_chars(text)
    triples = detect_rule_of_three(clean_text)
    count = len(triples)
    return count > max_allowed, count


def calculate_hedging_density(text: str, hedge_words: list[str] | None = None) -> tuple[float, int, int]:
    """Compute hedging density per 100 words. Returns (density, count, total_words)."""
    if hedge_words is None:
        rules = load_writing_quality_rules()
        hedge_words = rules.get("hedging", {}).get("hedge_words", [])
    count, total_words, density = count_hedging(text, hedge_words)
    return density, count, total_words


def validate_writing_quality(
    tweets: list[str],
    rules: dict[str, Any] | None = None,
) -> WritingQualityReport:
    """Run deterministic human writing quality checks on a piece (list of tweets).
    
    Returns WritingQualityReport with passed status, specific error messages,
    hedging density, and sentence variance metrics.
    """
    if rules is None:
        rules = load_writing_quality_rules()

    full_text = " ".join(tweets)
    clean_full_text = strip_zero_width_chars(full_text)

    # 1. Banned characters and emoji
    char_errors = detect_banned_characters(full_text, rules=rules)

    # 2. Banned vocabulary
    vocab_errors = detect_banned_vocabulary(full_text, rules=rules)

    # 3. Banned constructions
    construction_errors = detect_banned_constructions(full_text, rules=rules)

    errors: list[str] = char_errors + vocab_errors + construction_errors

    # 4. Repeated rhetorical pattern (Rule of three)
    r3_config = rules.get("rule_of_three", {})
    r3_occurrences = 0
    if r3_config.get("enabled", True):
        max_allowed = r3_config.get("max_allowed_per_piece", 1)
        triples = detect_rule_of_three(clean_full_text)
        r3_occurrences = len(triples)
        if r3_occurrences > max_allowed:
            errors.append(
                f"Repeated three-part parallel construction detected ({r3_occurrences} times): "
                f"flagged '{triples[-1]}'. Avoid repetitive rhetorical patterns."
            )

    # 5. Hedging density metric
    hedging_config = rules.get("hedging", {})
    hedge_words = hedging_config.get("hedge_words", [])
    max_density = hedging_config.get("max_hedge_words_per_100_words", 10.0)
    max_short = hedging_config.get("max_hedge_words_short_text", 3)

    hedge_count, total_words, density = count_hedging(clean_full_text, hedge_words)
    if total_words < 35:
        # In a short tweet (< 35 words), 2 legitimate modals like "can" or "may" is normal,
        # but 3 or more becomes excessively evasive hedging
        if hedge_count > max_short:
            errors.append(
                f"Excessive hedging in short text: found {hedge_count} hedge words "
                f"(max allowed: {max_short}). State factual findings and policies directly."
            )
    else:
        if density > max_density:
            errors.append(
                f"Hedging density too high: {density}% (max allowed: {max_density}%). "
                f"Found {hedge_count} hedge words across {total_words} words."
            )

    # 6. Sentence-length distribution and variance logging
    variance_report = calculate_sentence_variance(clean_full_text)

    return WritingQualityReport(
        passed=len(errors) == 0,
        errors=errors,
        hedging_density_per_100=density,
        hedge_word_count=hedge_count,
        total_words=total_words,
        sentence_variance=variance_report,
        rule_of_three_occurrences=r3_occurrences,
    )
