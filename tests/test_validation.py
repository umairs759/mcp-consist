"""Validation tests for the policy-rules-v1 engine (mcp_consist.validation)."""

import pytest

from mcp_consist.validation import (
    validate_context,
    validate_threshold,
    parse_json_field,
    MAX_INPUT_LENGTH,
)
from mcp_consist.models import AnalysisContext


# ---------------------------------------------------------------------------
# validate_threshold
# ---------------------------------------------------------------------------

def test_threshold_valid_in_range():
    assert validate_threshold(0.8) == 0.8
    assert validate_threshold(0.0) == 0.0
    assert validate_threshold(1.0) == 1.0
    assert validate_threshold(0.5) == 0.5


def test_threshold_invalid_rejected():
    assert validate_threshold(None) is None
    assert validate_threshold("0.5") is None
    assert validate_threshold(True) is None
    assert validate_threshold(False) is None
    assert validate_threshold(-0.1) is None
    assert validate_threshold(1.1) is None
    assert validate_threshold([0.5]) is None
    assert validate_threshold({}) is None


# ---------------------------------------------------------------------------
# validate_context
# ---------------------------------------------------------------------------

def test_context_valid():
    ctx, err = validate_context({
        "description": "d", "schema": "{}", "policy": "{}",
        "task": "t", "call": '{"tool":"x","action":"read","arguments":{}}',
    })
    assert err is None
    assert isinstance(ctx, AnalysisContext)
    assert ctx.description == "d"


def test_context_none():
    ctx, err = validate_context(None)
    assert ctx is None
    assert err is not None


def test_context_not_dict():
    ctx, err = validate_context("not a dict")
    assert ctx is None
    assert err is not None


def test_context_missing_call():
    ctx, err = validate_context({
        "description": "d", "schema": "{}", "policy": "{}",
        "task": "t", "call": "",
    })
    assert ctx is None
    assert "call" in err.lower()


def test_context_call_whitespace_only():
    ctx, err = validate_context({
        "description": "d", "schema": "{}", "policy": "{}",
        "task": "t", "call": "   ",
    })
    assert ctx is None
    assert err is not None


def test_context_field_non_string():
    ctx, err = validate_context({
        "description": 123, "schema": "{}", "policy": "{}",
        "task": "t", "call": "{}",
    })
    assert ctx is None
    assert err is not None


def test_context_field_too_long():
    long_text = "x" * (MAX_INPUT_LENGTH + 1)
    ctx, err = validate_context({
        "description": long_text, "schema": "{}", "policy": "{}",
        "task": "t", "call": "{}",
    })
    assert ctx is None
    assert err is not None


def test_context_exact_max_length_ok():
    text = "x" * MAX_INPUT_LENGTH
    ctx, err = validate_context({
        "description": text, "schema": "{}", "policy": "{}",
        "task": text, "call": '{"tool":"x","action":"read","arguments":{}}',
    })
    assert err is None


def test_context_none_fields_treated_as_empty():
    ctx, err = validate_context({
        "description": None, "schema": None, "policy": None,
        "task": None, "call": '{"tool":"x","action":"read","arguments":{}}',
    })
    assert err is None
    assert ctx.description == ""


# ---------------------------------------------------------------------------
# parse_json_field
# ---------------------------------------------------------------------------

def test_parse_json_field_valid():
    parsed, err = parse_json_field('{"a": 1}', "schema")
    assert err is None
    assert parsed == {"a": 1}


def test_parse_json_field_invalid():
    parsed, err = parse_json_field("{bad json", "schema")
    assert parsed is None
    assert err is not None
    assert "schema" in err


def test_parse_json_field_empty():
    parsed, err = parse_json_field("", "schema")
    assert parsed is None
    assert err is not None


def test_parse_json_field_whitespace_only():
    parsed, err = parse_json_field("   \n ", "schema")
    assert parsed is None
    assert err is not None
