"""Tests for Phase 5 Human Writing Quality and Anti-AI Marker Gates.

Enforces:
- Banned characters: em dash, en dash used as separator, curly quotes, emoji, obfuscation.
- Banned vocabulary: 14 initial terms loaded from editable config with word-boundary normalization.
- Banned constructions: negative parallelism, copula avoidance, filler openers.
- Repeated rhetorical patterns: rule of three parallel items.
- Hedging density: modal and qualifying words per hundred words with documented threshold.
- Sentence-length variance: metric calculation, short-text handling, and piece logging.
- Validation order: deterministic checks precede model review and hard violations veto approval.
"""
from __future__ import annotations

import pytest
from content_pipeline.writing_quality import (
    validate_writing_quality,
    detect_banned_characters,
    detect_banned_vocabulary,
    detect_banned_constructions,
    detect_repeated_rule_of_three,
    calculate_hedging_density,
    calculate_sentence_variance,
    strip_zero_width_chars,
)
from content_pipeline.validation import validate_piece_deterministic
from content_pipeline.config import load_brand, load_registry


def test_banned_characters_em_dash():
    """Em dash is strictly rejected."""
    text = "Smart contracts hold assets—yet runtime invariants are ignored."
    errs = detect_banned_characters(text)
    assert any("em dash" in e for e in errs)


def test_banned_characters_en_dash_separator():
    """En dash used as separator is rejected, but hyphens and ranges are allowed."""
    sep_en_dash = "Protocol security – a holistic view."
    errs = detect_banned_characters(sep_en_dash)
    assert any("en dash" in e for e in errs)

    hyphen_text = "Checks-effects-interactions pattern is well-known."
    assert detect_banned_characters(hyphen_text) == []


def test_banned_characters_curly_quotes():
    """Curly quotes are strictly rejected in favor of ASCII quotes."""
    curly_double = "The auditor said “reentrancy is possible” in this flow."
    errs = detect_banned_characters(curly_double)
    assert any("curly double quotes" in e for e in errs)

    curly_single = "It’s vital to check balances."
    errs_s = detect_banned_characters(curly_single)
    assert any("curly apostrophe/single quote" in e for e in errs_s)

    ascii_text = "It's vital to check balances with 'strict' guards."
    assert detect_banned_characters(ascii_text) == []


def test_banned_characters_emoji():
    """Emoji characters are rejected."""
    emoji_text = "Protect your funds 🚀 and guard contracts 🛡️ today."
    errs = detect_banned_characters(emoji_text)
    assert any("emoji" in e for e in errs)


def test_zero_width_character_obfuscation():
    """Zero-width spaces used to obfuscate banned words are stripped and detected."""
    # "d\u200be\u200bl\u200bv\u200be" -> "delve"
    obfuscated = "Let us d\u200be\u200bl\u200bv\u200be into the code."
    cleaned = strip_zero_width_chars(obfuscated)
    assert cleaned == "Let us delve into the code."
    rep = validate_writing_quality([obfuscated])
    assert rep.passed is False
    assert any("banned vocabulary 'delve'" in e for e in rep.errors)


def test_banned_vocabulary_all_fourteen_terms():
    """All 14 initial banned buzzwords are caught with word boundaries."""
    terms = [
        "delve", "leverage", "tapestry", "underscore", "foster",
        "pivotal", "realm", "landscape", "crucial", "seamless",
        "robust", "navigate", "testament", "ever-evolving"
    ]
    for term in terms:
        sample = f"We must {term} the protocol architecture to secure funds."
        errs = detect_banned_vocabulary(sample)
        assert len(errs) >= 1, f"Term '{term}' should be detected as banned vocabulary"


def test_banned_vocabulary_avoids_substring_false_positives():
    """Normal technical words containing substrings of banned terms are not falsely flagged."""
    # "deliver" should NOT match "delve"
    # "cleverage" should NOT match "leverage"
    # "underground" should NOT match "underscore"
    legitimate = "We deliver the updated software to underground infrastructure."
    errs = detect_banned_vocabulary(legitimate)
    assert errs == []


def test_banned_constructions_negative_parallelism():
    """Negative parallelism constructions are caught and rejected."""
    neg1 = "Security is not just about contracts, but also about cloud infrastructure."
    errs1 = detect_banned_constructions(neg1)
    assert any("negative_parallelism" in e.lower() or "negative parallelism" in e.lower() for e in errs1)

    neg2 = "We review not only the Solidity code but also the backend APIs."
    errs2 = detect_banned_constructions(neg2)
    assert any("negative_parallelism" in e.lower() or "negative parallelism" in e.lower() for e in errs2)


def test_banned_constructions_copula_avoidance():
    """Copula avoidance ('serves as', 'stands as', 'boasts') is rejected."""
    samples = [
        "This function serves as the central entry point for withdrawals.",
        "The bridge stands as a critical component of the ecosystem.",
        "The protocol boasts high transaction volume and zero downtime.",
    ]
    for sample in samples:
        errs = detect_banned_constructions(sample)
        assert any("copula_avoidance" in e.lower() or "copula avoidance" in e.lower() for e in errs)


def test_banned_constructions_filler_openers():
    """Canned filler openers are caught and rejected."""
    samples = [
        "In today's fast-paced world, decentralized finance moves quickly.",
        "It is important to note that access controls must be verified.",
    ]
    for sample in samples:
        errs = detect_banned_constructions(sample)
        assert any("filler" in e.lower() for e in errs)


def test_repeated_rule_of_three_heuristic():
    """Flag sentences built on three parallel items when the pattern repeats."""
    # Two sentences both using 3-item A, B, and C parallelism in one piece
    text = (
        "We audit contracts, inspect backends, and verify cloud infrastructure. "
        "Attackers exploit keys, manipulate oracles, and drain liquidity."
    )
    detected, count = detect_repeated_rule_of_three(text)
    assert detected is True
    assert count >= 2


def test_hedging_density_metric():
    """Measure qualifying words per hundred words against threshold."""
    # Extremely hedged text (7 hedges out of 25 words = 28 per 100)
    hedged_text = "We may generally suggest that contracts might typically have vulnerabilities that could possibly happen."
    density, count, total = calculate_hedging_density(hedged_text)
    assert density > 15.0

    # Clean technical statement with necessary uncertainty (1 hedge out of 20 words = 5 per 100)
    normal_text = "Reentrancy locks stop state changes during an external call. Untrusted callees may revert execution control."
    norm_density, _, _ = calculate_hedging_density(normal_text)
    assert norm_density <= 15.0


def test_sentence_variance_short_text_handling():
    """Sentence variance handles 1-sentence tweets gracefully without failing."""
    single_sentence = ["Smart contract audits only verify static code; runtime invariant testing is required in production."]
    var_rep = calculate_sentence_variance(" ".join(single_sentence))
    assert var_rep.sentence_count == 1
    assert var_rep.is_evaluable is False
    assert var_rep.variance == 0.0


def test_deterministic_hard_violations_veto_review():
    """Hard deterministic checks immediately reject a piece before reviewer approval."""
    _, brand = load_brand()
    reg = load_registry()
    spec = reg.types["marketing-post"]

    bad_draft = ["In today's fast-paced world, we leverage robust AI—guaranteed 100% secure! 🚀"]
    passed, errors, wq_rep = validate_piece_deterministic(
        tweets=bad_draft,
        brand=brand,
        spec=spec,
    )
    assert passed is False
    assert len(errors) >= 3
    # Check that multiple deterministic violations were identified
    assert any("filler" in e.lower() for e in errors)
    assert any("banned vocabulary 'leverage'" in e for e in errors)
    assert any("emoji" in e for e in errors)
