# Security Review — MCP-CONSIST

Honest, evidence-based review. No penetration testing was performed. No formal
security audit was conducted. This document describes implemented safeguards
and remaining risks.

## Scope

Stage 1 lexical consistency prototype (`pipeline.py`) and Stage 2 five-layer
engine (`mcp_consist/`) plus the Gradio workbench (`demo/app.py`,
`demo/theme.css`, `demo/components.py`).

## 1. Input validation

- `analyze` (Stage 2) validates context via `mcp_consist.validation.validate_context`:
  None/non-dict/missing call/oversize fields -> ERROR, no exception.
- Each field capped at `MAX_INPUT_LENGTH` (20,000 chars).
- `threshold` validated to a number in [0, 1]; booleans rejected.
- JSON fields parsed with `json.loads` only; no execution.
- Stage 1 `analyze_pair` preserves the same validation contract.
- Covered by `tests/test_validation.py`, `tests/test_security.py`.

## 2. No code execution / no unsafe deserialization

- No `eval`, `exec`, `compile`, or dynamic import of user input.
- JSON parsed with standard `json.loads` (no pickle/YAML).
- No shell invocation using inputs.
- No user-controlled network requests.
- No filesystem access beyond reading project data files; path checks are lexical
  only and never touch the filesystem.

## 3. XSS

- All user-derived strings rendered via `demo.components` helpers which
  `html.escape` every value.
- Engine findings contain no raw user input (redacted evidence) by design.
- Covered by `test_run_analysis_xss_rendered_inert` and security tests.

## 4. Evidence redaction

- Sensitive resource references are redacted; actual secret values never
  displayed.
- Rule findings use `_redact()` labels instead of raw values.
- Reports contain SHA-256 hashes of inputs, not raw input contents.

## 5. Recursion / nesting limits

- Input length cap (20,000 chars) bounds JSON size.
- JSON Schema subset validation does not recurse beyond one level for type
  matching; no unbounded recursion.
- No regex catastrophic backtracking patterns identified (patterns are simple
  literals / bounded).

## 6. Unicode handling

- Zero-width and bidi control characters are detected, not executed.
- Normalization is deterministic and does not decode payloads.
- Suspicious encoded payloads are flagged but never decoded.

## 7. Report file handling

- Reports written to a temporary directory under the OS temp path; no
  user-controlled path components.
- No secrets embedded in findings.

## 8. Gradio launch configuration

- Host defaults to 127.0.0.1; port 7860; share=False by default.
- Public tunnel only via explicit MCP_CONSIST_SHARE=1 with warning.
- Analytics disabled.

## 9. Dependency audit

- requirements.txt pins gradio==5.50.0, pytest==9.2.0.
- No heavy ML frameworks introduced.
- Dependency compatibility verified against installed .venv.

## 10. Remaining risks

- Deterministic rule-based detector can be bypassed by novel phrasing
  (documented in threat model).
- No real MCP interception; this is a research prototype, not a security
  boundary.
- No symlink/filesystem protection (lexical only).
- Synthetic dataset is author-authored; no external validation.
- In-memory history is process-shared across sessions (minor).

## 11. No pentest claim

No penetration test or formal security audit has been performed. This review
is a source-level self-assessment.