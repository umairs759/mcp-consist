# MCP-CONSIST Report

## Status

Stage 1: honest lexical baseline + professional Gradio workbench UI.
`tests/` — 31 tests, all passing (`python -m pytest tests/ -q`).

## Backend (`pipeline.py`)

- `run_consistency_check(input_text1, input_text2, threshold) -> "ALLOW"|"WARN"|"BLOCK"|"ERROR"`
- `analyze_pair(...) -> dict` with status, overlap, threshold, matched_terms,
  unmatched_a, unmatched_b, explanation, error.
- `threshold` genuinely gates ALLOW (`overlap >= threshold` → ALLOW).
- Empty / whitespace / None / non-string / >20,000 chars / invalid threshold → ERROR.
- Identical token sets → BLOCK (prototype rule; documented in docs/LIMITATIONS.md).

## UI (`demo/app.py`)

- Dark enterprise theme (`demo/theme.css`), Gradio 5.50.0.
- Context A / B textboxes with live character count and validation messages.
- Threshold slider (default 0.80), Run Consistency Analysis, Clear All,
  Load sample (safe demo pairs from `data/samples.json`).
- Results panel: status badge (`<span class="badge badge-...">`), overlap %,
  threshold, matched terms, non-matching terms, short explanation, error details.
- Real Gradio wiring: inputs → `run_analysis` callback → outputs (verified via
  live `gradio_client` against a running server).
- XSS-escaped rendering; no inline event handlers; no tracebacks shown to users.
- Local by default (`127.0.0.1:7860`, `share=False`).

## Metrics

No ML, no training pipeline, no dataset, and no reproducible evaluation existed
in Stage 1. `results/ablation_results.json` and `results/adaptive_holdout.json`
contain hand-written constants (e.g. recall 0.90 in adaptive_holdout vs the
1.000 claimed by the old README). These are **unverified, from earlier
experiments / placeholder** and are **not** cited as achieved performance.

Numbers in the README/REPORT/UI come only from reproducible code paths; no
accuracy / precision / recall / F1 is claimed.

## What is not implemented (Stage 2 planned)

- `mcp_consist/engine.py` (`policy-rules-v1`) five-layer rule-based detector.
- Joint-context UI tab (description, schema, policy, task, call).
- `data/eval_cases.jsonl` + `scripts/evaluate.py` reproducible benchmark.

## Security

No pentesting performed. See `docs/SECURITY_REVIEW.md` for an honest review
and remaining risks. No vulnerability claims are made.
