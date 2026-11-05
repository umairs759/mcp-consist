# MCP-CONSIST — Context-Consistency Enforcement for MCP Tool-Poisoning Detection

A research prototype (deterministic, rule-based, no ML) for detecting
inconsistencies between five joint context inputs of an MCP-style tool call:

1. Tool description
2. Tool input schema
3. Capability policy
4. User task
5. Proposed tool call

The system emits one of four verdicts — ALLOW / WARN / BLOCK / ERROR — with a
score, five-layer matrix, findings, rule IDs, evidence, and a decision trace.

## Research motivation

Tool-poisoning-style attacks in the Model Context Protocol (MCP) can hide
malicious intent inside tool descriptions, schemas, or proposed calls that
disagree with the user's task. MCP-CONSIST explores a deterministic,
explainable, multi-layer consistency check across all five context inputs
instead of relying on any single field.

## Problem statement

A single input field (description or call) is insufficient: a malicious tool
can have a benign description while its proposed call targets a sensitive
resource. Joint analysis of description, schema, policy, task and call is
required to surface inconsistencies.

## Proposed approach

A five-layer deterministic rule engine (`policy-rules-v1`) with centralized
severity penalties and a documented verdict policy. No ML, no network access,
no filesystem access, no code execution.

## System architecture

```
analyze(ctx, threshold=0.8) ->
  validation -> JSON parsing -> layer applicability ->
  run_all_rules (10 rules) -> layer scoring -> overall score -> verdict policy
```

Source tree:

```
mcp_consist/
  __init__.py engine.py rules.py config.py normalization.py
  models.py validation.py reporting.py
pipeline.py            # Stage 1 lexical prototype (preserved)
demo/app.py            # Gradio UI (Stage 1 + Joint Context tab)
demo/components.py     # XSS-safe HTML helpers
data/eval_cases.jsonl  # 101 synthetic cases
data/scenarios.json    # UI scenarios
scripts/evaluate.py    # evaluation
scripts/evaluate_ablation.py
scripts/generate_adversarial_cases.py
scripts/verify_release.py
```

## Five detection layers

1. **Description Integrity** (R-101): hidden instruction phrases, zero-width
   Unicode, bidi control chars, long encoded payload indicators.
2. **Sensitive Resource Protection** (R-102): references to SSH keys, .env,
   AWS creds, tokens, cookies, passwords, etc. (redacted evidence).
3. **Schema and Parameter Integrity** (R-201, R-202): required/unknown/type/
   enum validation; undeclared side-channel parameters.
4. **Capability Policy Compliance** (R-301..R-304): path outside roots,
   disallowed hosts, disallowed actions, missing policy coverage.
5. **Joint Intent and Tool-Call Integrity** (R-401, R-402, R-501): task vs
   call mismatch, description vs call mismatch, cross-tool pivot.

## Rule catalog summary

See `docs/RULE_CATALOG.md`. All 10 rules have positive and negative tests.

## Installation

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

Python 3.11+ recommended. Gradio 5.50.0.

## Launch

```bash
.venv/bin/python demo/app.py
# open http://127.0.0.1:7860
```

Environment: `MCP_CONSIST_HOST`, `PORT`/`GRADIO_SERVER_PORT`, `MCP_CONSIST_SHARE`.

## Example workflow

Stage 1 (Analysis Workspace): paste two texts, run consistency check.

Stage 2 (Joint Context tab): fill five fields (or load a scenario), click
"Analyze Joint Context". Review verdict, five-layer matrix, findings, trace,
raw JSON, download reports.

## Example result format

```json
{
  "verdict": "BLOCK",
  "score": 0.25,
  "engine": "policy-rules-v1",
  "engine_version": "1.0.0",
  "latency_ms": 0.3,
  "layers": [...],
  "findings": [...],
  "trace": [...],
  "override": "HIGH finding present"
}
```

## Evaluation methodology

Synthetic, author-authored dataset (101 cases, dev/holdout split). Real engine
execution. Metrics in `results/eval_results.json`.

- Dataset size: 101 (dev 54, holdout 47)
- Multiclass accuracy: 1.0000
- Macro F1 (all 4 classes): 0.7500; (observed classes): 1.0000
- Weighted F1: 1.0000
- Binary precision/recall/F1: 1.0000 / 1.0000 / 1.0000
- Benign false-positive rate: 0.0000
- Latency p50/p95 (ms): 0.18 / 0.59

Confusion matrix (rows=true): ALLOW 53/53 correct; WARN 4 correct, 9 predicted
BLOCK; BLOCK 35/35 correct.

## Security and privacy

Inputs processed in memory only; no persistence, no outbound requests, no
secrets. See `docs/SECURITY_REVIEW.md`, `docs/THREAT_MODEL.md`.

## Limitations

- Deterministic rule-based; no ML, no semantics.
- No real MCP interception; not a security boundary.
- Synthetic dataset, author-authored; no external validation.
- Lexical path/host checks only; no symlink protection.
- See `docs/LIMITATIONS.md`.

## Future research

- Semantic intent classification (carefully, with real data).
- Real MCP proxy integration.
- External benchmark evaluation with licensed datasets.
- Improved false-positive reduction via context-aware rules.