"""Engine-level tests for the policy-rules-v1 engine (mcp_consist.engine)."""

import json

import pytest

from mcp_consist import analyze, ENGINE_NAME, ENGINE_VERSION, DEFAULT_THRESHOLD
from mcp_consist.models import Verdict


def _ctx(**overrides):
    base = {
        "description": "Reads a file from the workspace.",
        "schema": json.dumps({
            "type": "object",
            "properties": {"path": {"type": "string"}},
            "required": ["path"],
            "additionalProperties": False,
        }),
        "policy": json.dumps({
            "allowed_roots": ["/workspace"],
            "allowed_hosts": ["example.test"],
            "allowed_actions": ["read", "list"],
            "allowed_tools": ["read_file"],
        }),
        "task": "Read the example file",
        "call": json.dumps({
            "tool": "read_file",
            "action": "read",
            "arguments": {"path": "/workspace/example.txt"},
        }),
    }
    base.update(overrides)
    return base


# ---------------------------------------------------------------------------
# Output contract
# ---------------------------------------------------------------------------

def test_analyze_returns_contract_keys():
    result = analyze(_ctx())
    expected = {
        "verdict", "score", "engine", "engine_version", "latency_ms",
        "layers", "findings", "trace", "override",
    }
    assert set(result.keys()) == expected, result.keys()


def test_analyze_five_layers_stable_order():
    result = analyze(_ctx())
    layer_ids = [l["layer_id"] for l in result["layers"]]
    assert layer_ids == ["layer1", "layer2", "layer3", "layer4", "layer5"]


def test_analyze_engine_identity():
    result = analyze(_ctx())
    assert result["engine"] == ENGINE_NAME
    assert result["engine_version"] == ENGINE_VERSION


def test_analyze_latency_is_measured():
    result = analyze(_ctx())
    assert isinstance(result["latency_ms"], (int, float))
    assert result["latency_ms"] >= 0.0


def test_analyze_verdict_is_allowed_state():
    result = analyze(_ctx())
    assert result["verdict"] in ("ALLOW", "WARN", "BLOCK", "ERROR")


def test_analyze_score_in_range():
    result = analyze(_ctx())
    assert 0.0 <= result["score"] <= 1.0


# ---------------------------------------------------------------------------
# Benign / ALLOW
# ---------------------------------------------------------------------------

def test_benign_allows():
    result = analyze(_ctx())
    assert result["verdict"] == Verdict.ALLOW.value
    assert result["score"] == pytest.approx(1.0)


# ---------------------------------------------------------------------------
# Invalid inputs -> ERROR
# ---------------------------------------------------------------------------

def test_analyze_none_context():
    result = analyze(None)
    assert result["verdict"] == Verdict.ERROR.value


def test_analyze_context_not_dict():
    result = analyze("not a dict")
    assert result["verdict"] == Verdict.ERROR.value


def test_analyze_empty_call():
    result = analyze(_ctx(call=""))
    assert result["verdict"] == Verdict.ERROR.value


def test_analyze_invalid_json_call():
    result = analyze(_ctx(call="{bad json"))
    assert result["verdict"] == Verdict.ERROR.value


def test_analyze_invalid_json_schema():
    result = analyze(_ctx(schema="{bad"))
    assert result["verdict"] == Verdict.ERROR.value


def test_analyze_invalid_json_policy():
    result = analyze(_ctx(policy="{bad"))
    assert result["verdict"] == Verdict.ERROR.value


def test_analyze_invalid_threshold():
    result = analyze(_ctx(), threshold=1.5)
    assert result["verdict"] == Verdict.ERROR.value


def test_analyze_boolean_threshold():
    result = analyze(_ctx(), threshold=True)
    assert result["verdict"] == Verdict.ERROR.value


# ---------------------------------------------------------------------------
# Threshold boundaries
# ---------------------------------------------------------------------------

def test_threshold_zero_allows_unless_blocked():
    result = analyze(_ctx(), threshold=0.0)
    assert result["verdict"] == Verdict.ALLOW.value


def test_threshold_one_allows_full_overlap():
    result = analyze(_ctx(), threshold=1.0)
    assert result["verdict"] == Verdict.ALLOW.value


# ---------------------------------------------------------------------------
# N/A layers
# ---------------------------------------------------------------------------

def test_layer3_na_when_no_schema():
    result = analyze(_ctx(schema=""))
    layer3 = result["layers"][2]
    assert layer3["applicable"] is False
    assert layer3["score"] is None
    assert layer3["status"] == "N/A"


def test_layer4_na_when_no_call():
    # call empty -> ERROR actually; use missing task to make layer5 N/A
    result = analyze(_ctx(task=""))
    layer5 = result["layers"][4]
    assert layer5["applicable"] is False
    assert layer5["score"] is None


def test_layer1_na_when_no_description():
    result = analyze(_ctx(description=""))
    layer1 = result["layers"][0]
    assert layer1["applicable"] is False
    assert layer1["score"] is None


# ---------------------------------------------------------------------------
# Missing policy coverage -> WARN
# ---------------------------------------------------------------------------

def test_missing_policy_warns():
    result = analyze(_ctx(policy=""))
    assert result["verdict"] == Verdict.WARN.value
    assert any(f["rule_id"] == "R-304" for f in result["findings"])


# ---------------------------------------------------------------------------
# Determinism
# ---------------------------------------------------------------------------

def test_deterministic_repeated_analysis():
    ctx = _ctx()
    r1 = analyze(ctx)
    r2 = analyze(ctx)
    assert r1["verdict"] == r2["verdict"]
    assert r1["score"] == r2["score"]
    assert r1["layers"] == r2["layers"]
    assert r1["findings"] == r2["findings"]
    # Latency may differ; not asserted.
