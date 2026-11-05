"""Backend tests for the lexical consistency prototype (pipeline.py).

Covers the contract preserved from the original project plus the Stage 1
fixes: real threshold gating, threshold validation, empty/whitespace/None
handling, max-length, and the structured analyze_pair output.
"""

import pytest

from pipeline import (
    analyze_pair,
    MAX_INPUT_LENGTH,
    run_consistency_check,
)


# ---------------------------------------------------------------------------
# run_consistency_check — preserved behaviour + threshold now matters
# ---------------------------------------------------------------------------

def test_allow_high_similarity_at_default_threshold():
    """High overlap should return ALLOW at the default 0.80 threshold."""
    assert run_consistency_check(
        "The cat sat on the mat", "The cat is on the mat", 0.8
    ) == "ALLOW"


def test_allow_requires_threshold_to_be_met():
    """0.80 overlap must NOT be ALLOW when the threshold is 0.99."""
    # "a b c d e" vs "a b c d f" -> 4 shared / 5 = 0.80 overlap
    assert run_consistency_check("a b c d e", "a b c d f", 0.8) == "ALLOW"
    assert run_consistency_check("a b c d e", "a b c d f", 0.99) != "ALLOW"


def test_warn_below_threshold():
    """Below-threshold overlap returns WARN (not ALLOW, not BLOCK)."""
    assert run_consistency_check("a b c d e", "a b c d f", 0.9) == "WARN"


def test_block_identical_token_sets():
    """Identical inputs (same token set) return BLOCK (prototype rule)."""
    assert run_consistency_check("hello", "hello", 0.5) == "BLOCK"
    assert run_consistency_check("Hello world", "world hello", 0.5) == "BLOCK"


def test_word_order_independence():
    """Token-set overlap is independent of word order."""
    assert run_consistency_check(
        "the cat sat on the mat", "mat the on sat cat the", 0.5
    ) == "BLOCK"


def test_error_empty_input():
    """Empty inputs return ERROR."""
    assert run_consistency_check("", "some text", 0.5) == "ERROR"
    assert run_consistency_check("some text", "", 0.5) == "ERROR"


def test_error_whitespace_only_input():
    """Whitespace-only inputs return ERROR."""
    assert run_consistency_check("   ", "some text", 0.5) == "ERROR"
    assert run_consistency_check("some text", "\t\n ", 0.5) == "ERROR"


def test_error_none_input():
    """None inputs return ERROR (no exception)."""
    assert run_consistency_check(None, "some text", 0.5) == "ERROR"
    assert run_consistency_check("some text", None, 0.5) == "ERROR"


def test_error_non_string_input():
    """Non-string inputs return ERROR (no exception)."""
    assert run_consistency_check(123, "some text", 0.5) == "ERROR"
    assert run_consistency_check("some text", ["a", "b"], 0.5) == "ERROR"


def test_error_invalid_threshold():
    """Invalid thresholds return ERROR (no exception)."""
    assert run_consistency_check("a b", "a b", -0.1) == "ERROR"
    assert run_consistency_check("a b", "a b", 1.1) == "ERROR"
    assert run_consistency_check("a b", "a b", "0.5") == "ERROR"
    assert run_consistency_check("a b", "a b", None) == "ERROR"
    assert run_consistency_check("a b", "a b", True) == "ERROR"


def test_error_max_length():
    """Inputs over MAX_INPUT_LENGTH chars return ERROR."""
    long_text = "x" * (MAX_INPUT_LENGTH + 1)
    assert run_consistency_check(long_text, "x", 0.5) == "ERROR"
    assert run_consistency_check("x", long_text, 0.5) == "ERROR"


def test_boundary_max_length_ok():
    """Inputs exactly at MAX_INPUT_LENGTH are accepted."""
    text = "x" * MAX_INPUT_LENGTH
    assert run_consistency_check(text, text, 0.5) in ("ALLOW", "BLOCK")


def test_return_values_are_only_valid_states():
    """Every valid input returns one of the four states."""
    for result in (
        run_consistency_check("a b", "a b", 0.5),
        run_consistency_check("a b", "c d", 0.5),
        run_consistency_check("", "x", 0.5),
        run_consistency_check("a b", "a b", 1.5),
    ):
        assert result in ("ALLOW", "WARN", "BLOCK", "ERROR")


# ---------------------------------------------------------------------------
# analyze_pair — structured output
# ---------------------------------------------------------------------------

def test_analyze_pair_return_shape():
    out = analyze_pair("a b c", "b c d", 0.9)
    assert set(out.keys()) == {
        "status", "overlap", "threshold", "matched_terms",
        "unmatched_a", "unmatched_b", "explanation", "error",
    }
    assert out["status"] == "WARN"
    assert out["overlap"] == pytest.approx(2 / 3)
    assert out["threshold"] == 0.9
    assert out["matched_terms"] == ["b", "c"]
    assert out["unmatched_a"] == ["a"]
    assert out["unmatched_b"] == ["d"]
    assert out["error"] == ""


def test_analyze_pair_allow():
    out = analyze_pair("a b c d e", "a b c d f", 0.8)
    assert out["status"] == "ALLOW"
    assert out["overlap"] == pytest.approx(0.8)
    assert "meets the threshold" in out["explanation"]


def test_analyze_pair_block_identical():
    out = analyze_pair("hello world", "world hello", 0.5)
    assert out["status"] == "BLOCK"
    assert out["overlap"] == pytest.approx(1.0)


def test_analyze_pair_error_empty():
    out = analyze_pair("", "text", 0.5)
    assert out["status"] == "ERROR"
    assert out["overlap"] is None
    assert out["error"]


def test_analyze_pair_error_invalid_threshold():
    out = analyze_pair("a b", "a b", 2.0)
    assert out["status"] == "ERROR"
    assert out["threshold"] is None
    assert out["error"]


def test_run_consistency_check_wraps_analyze_pair():
    """run_consistency_check is a thin wrapper: same decision as analyze_pair."""
    for t1, t2, thr in [
        ("cat sat mat", "cat mat sat", 0.5),
        ("alpha beta", "gamma delta", 0.5),
        ("same", "same", 0.8),
        ("", "x", 0.8),
        ("a b", "a b", 1.5),
    ]:
        assert run_consistency_check(t1, t2, thr) == analyze_pair(t1, t2, thr)["status"]
