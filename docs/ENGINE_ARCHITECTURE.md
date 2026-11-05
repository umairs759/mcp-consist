# Engine Architecture — MCP-CONSIST

## Overview

Stage 1: lexical consistency prototype (`pipeline.py`) — preserved unchanged.
Stage 2: five-layer deterministic detector (`mcp_consist/`).

## Data flow

1. `analyze(ctx, threshold, enabled_layers)` receives a dict.
2. `validate_context` checks types, lengths, required call.
3. JSON fields parsed safely (`safe_parse_json`).
4. Layer applicability computed (description/schema/call/task presence + enabled).
5. `run_all_rules` executes 10 rules (disabled layers skipped).
6. `_build_layer_results` builds LayerResult with score = max(0, 1 - sum penalties).
7. Overall score = weighted average of applicable layer scores (equal weights).
8. Verdict policy applied (CRITICAL/HIGH -> BLOCK; zero-score override; MEDIUM -> WARN; coverage gap -> WARN; else threshold).
9. `AnalysisResult` serialized to dict with measured latency.

## Scoring

- Penalties: LOW 0.15, MEDIUM 0.40, HIGH 0.75, CRITICAL 1.00.
- Layer score: max(0.0, 1.0 - sum penalties).
- N/A layers: score null, excluded from average.
- Overall: weighted average over applicable layers.

## Verdict policy (order)

1. Invalid inputs -> ERROR.
2. CRITICAL finding -> BLOCK.
3. HIGH finding -> BLOCK.
4. Applicable layer genuine zero score -> BLOCK (override).
5. MEDIUM-only -> WARN.
6. Policy coverage gap -> WARN.
7. Score >= threshold -> ALLOW else WARN.

## Report generation

`mcp_consist.reporting` produces JSON/Markdown with UTC timestamp, engine
version, verdict, score, layers, findings, trace, input SHA-256 hashes.