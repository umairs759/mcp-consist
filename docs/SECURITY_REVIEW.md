# Security Review — MCP-CONSIST Stage 1

Honest, evidence-based review. Nothing here claims penetration testing or a
formal security audit. No pentesting was performed.

## Scope

The lexical consistency prototype backend (`pipeline.py`) and the Gradio
workbench UI (`demo/app.py`, `demo/theme.css`, `demo/components.py`).

## 1. Input validation

- `analyze_pair` rejects None / non-string / empty / whitespace-only inputs
  with status ERROR (no exception raised).
- Each field is capped at `MAX_INPUT_LENGTH` (20,000 characters); longer
  inputs return ERROR.
- `threshold` must be a number in [0, 1]; booleans, strings, None, and
  out-of-range numbers return ERROR.
- Validation happens before any tokenisation, so malformed input cannot reach
  the overlap computation.

## 2. XSS

- Every user-derived string rendered into HTML is passed through
  `html.escape` via `demo.components` (`badge`, `chips`, `explanation_box`,
  `error_box`, `meta_row`, `esc`).
- No inline event handlers (`onclick`, `onerror`, etc.) are emitted by the
  helpers.
- Covered by test `test_run_analysis_xss_rendered_inert`.

## 3. Exception handling

- `analyze_pair` never raises for invalid input; it returns an ERROR dict.
- `run_consistency_check` is a thin wrapper and likewise never raises on
  invalid input.
- Callbacks in `demo/app.py` are thin wrappers over `analyze_pair`; tracebacks
  are not surfaced to users (results are HTML-only). Gradio still shows its
  own server-side traceback in console logs for unexpected bugs, which is
  standard Gradio behaviour and not user-facing.

## 4. Dependency pinning

- `requirements.txt` pins `gradio==5.50.0` and `pytest==9.2.0`, verified
  installable from a fresh venv. No unpinned deps are declared.

## 5. Secrets

- No API keys, tokens, or secrets are required or used. None are checked into
  the repo.

## 6. Outbound requests

- None expected. The only network-related behaviour is Gradio's optional
  public tunnel (`share=True`), which is disabled by default (`share=False`)
  and only enabled via `MCP_CONSIST_SHARE=1` with a printed warning. Google
  Fonts is linked via `<link rel=preconnect ...>` in the page head for font
  loading; the page works with system fallbacks if fonts fail to load.

## 7. Persistence

- None. Inputs are processed in memory only and not stored. No database,
  no file writes, no session state beyond Gradio's transient UI state.
- `test.db` was removed from the active tree (unrelated schema) and archived
  under `_archive_unrelated/`; nothing in the code references it.

## 8. Public-deployment config

- Host defaults to `127.0.0.1` (env `MCP_CONSIST_HOST`).
- Port defaults to 7860 (env `PORT` / `GRADIO_SERVER_PORT`).
- `share=False` by default; public tunnel requires explicit opt-in with a
  warning printed at launch.

## Remaining risks (not mitigated in Stage 1)

- The UI sends inputs to the local backend over HTTP (loopback by default).
  For public deployment, use HTTPS + authentication in front of Gradio (not
  provided by this repo).
- No rate limiting on the analysis endpoint.
- The identical-token-set → BLOCK rule can cause unexpected blocks; see
  docs/LIMITATIONS.md.
- Gradio's server-side console tracebacks may leak internal paths in unexpected
  error cases (standard Gradio behaviour).

No claim is made that the tool is free of vulnerabilities.
