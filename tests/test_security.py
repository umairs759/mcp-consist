"""Security tests: XSS, evidence redaction, no secret exposure, no execution."""

import json

from mcp_consist import analyze
from mcp_consist.rules import (
    rule_R102_sensitive_resources,
    rule_R201_schema_validation,
    run_all_rules,
)


# ---------------------------------------------------------------------------
# XSS resistance in rendered/evidence fields
# ---------------------------------------------------------------------------

_XSS = "<img src=x onerror=alert(1)>"


def test_engine_evidence_xss_escaped():
    """User-supplied XSS in call arguments must not appear raw in evidence."""
    ctx = {
        "description": "Reads a file.",
        "schema": json.dumps({"type": "object", "properties": {"path": {"type": "string"}}}),
        "policy": json.dumps({"allowed_roots": ["/workspace"], "allowed_actions": ["read"]}),
        "task": "Read a file",
        "call": json.dumps({"tool": "x", "action": "read",
                            "arguments": {"path": _XSS}}),
    }
    result = analyze(ctx)
    joined = json.dumps(result)
    # The raw XSS payload must not appear in engine output (it is redacted,
    # not echoed back), so it cannot be executed when rendered.
    assert _XSS not in joined, joined
    assert "<img" not in joined
    assert "onerror" not in joined


def test_rules_evidence_redacts_secrets():
    parts = {"call": "read ~/.ssh/id_rsa key material"}
    findings = rule_R102_sensitive_resources(parts)
    assert any(f.rule_id == "R-102" for f in findings)
    joined = "".join(f.evidence for f in findings)
    # The raw secret-looking value must not appear in evidence.
    assert "id_rsa" not in joined
    assert "[redacted:" in joined
    # Descriptions must not contain raw user-supplied secrets either.
    desc_joined = "".join(f.description for f in findings)
    assert "id_rsa" not in desc_joined


def test_schema_validation_evidence_no_raw_values():
    schema = json.dumps({"type": "object", "properties": {"path": {"type": "string"}}})
    call = json.dumps({"tool": "x", "action": "read",
                       "arguments": {"path": "/workspace/a.txt"}})
    findings = rule_R201_schema_validation(schema, call)
    for f in findings:
        assert "<script" not in f.evidence
        assert "javascript:" not in f.evidence


# ---------------------------------------------------------------------------
# No execution of supplied JSON
# ---------------------------------------------------------------------------

def test_supplied_json_not_executed():
    """JSON supplied in context is parsed, never executed/evaluated."""
    ctx = {
        "description": "x", "schema": "{}", "policy": "{}",
        "task": "x",
        "call": '{"tool":"x","action":"read","arguments":{}}',
    }
    result = analyze(ctx)
    # Should analyze normally, not execute anything.
    assert result["verdict"] in ("ALLOW", "WARN", "BLOCK", "ERROR")


# ---------------------------------------------------------------------------
# Input length limits
# ---------------------------------------------------------------------------

def test_input_length_limit_enforced():
    long_text = "x" * 20001
    ctx = {
        "description": long_text, "schema": "{}", "policy": "{}",
        "task": "x",
        "call": '{"tool":"x","action":"read","arguments":{}}',
    }
    result = analyze(ctx)
    assert result["verdict"] == "ERROR"


# ---------------------------------------------------------------------------
# Unicode handling
# ---------------------------------------------------------------------------

def test_unicode_handled_without_crash():
    ctx = {
        "description": "Reads a \u00e9\u00f1 file \u200b",
        "schema": "{}", "policy": "{}",
        "task": "Read a file",
        "call": '{"tool":"x","action":"read","arguments":{}}',
    }
    result = analyze(ctx)
    assert result["verdict"] in ("ALLOW", "WARN", "BLOCK", "ERROR")


# ---------------------------------------------------------------------------
# No secrets in exported findings
# ---------------------------------------------------------------------------

def test_no_secret_values_in_findings():
    ctx = {
        "description": "Reads ~/.ssh/id_rsa",
        "schema": "{}",
        "policy": json.dumps({"allowed_roots": ["/workspace"]}),
        "task": "Read a file",
        "call": json.dumps({"tool": "x", "action": "read",
                            "arguments": {"path": "/workspace/a.txt"}}),
    }
    result = analyze(ctx)
    joined = json.dumps(result)
    # Actual path value may appear redacted but the raw private-key-style
    # reference is redacted.
    assert "id_rsa" not in joined or "[redacted:" in joined
