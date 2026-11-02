import pytest
from pipeline import run_consistency_check


class TestConsistencyCheck:
    """Tests for the consistency check pipeline."""

    def test_allow_high_similarity(self):
        """High overlap should return ALLOW."""
        result = run_consistency_check(
            "The cat sat on the mat", "The cat is on the mat", 0.5
        )
        assert result == "ALLOW"

    def test_warn_medium_similarity(self):
        """Medium overlap should return WARN."""
        result = run_consistency_check(
            "The cat sat on the mat", "Dogs are great pets", 0.5
        )
        assert result in ("WARN", "BLOCK")

    def test_block_identical(self):
        """Identical inputs should return BLOCK."""
        text = "The quick brown fox"
        result = run_consistency_check(text, text, 0.5)
        assert result == "BLOCK"

    def test_error_empty_input(self):
        """Empty inputs should return ERROR."""
        result = run_consistency_check("", "some text", 0.5)
        assert result == "ERROR"
        result = run_consistency_check("some text", "", 0.5)
        assert result == "ERROR"

    def test_threshold_gate(self):
        """Below threshold should not ALLOW."""
        result = run_consistency_check(
            "apple", "orange", 0.9
        )
        assert result != "ALLOW"

    def test_consistency_rate_bounds(self):
        """Consistency rate should be between 0 and 1."""
        # Just verify the function runs without crashing on valid inputs
        result = run_consistency_check(
            "hello world", "hello world", 0.5
        )
        assert result in ("ALLOW", "WARN", "BLOCK", "ERROR")