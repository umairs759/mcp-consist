# Supervisor Demo Guide — MCP-CONSIST

## Project overview
MCP-CONSIST is a deterministic, rule-based research prototype detecting
inconsistencies across five joint context inputs for MCP-style tool calls.

## Problem addressed
Tool poisoning can hide malicious intent in any single field; joint analysis
of description, schema, policy, task, call is needed.

## How five inputs work together
The engine runs 10 rules across 5 layers and emits ALLOW/WARN/BLOCK/ERROR.

## Launch
```bash
.venv/bin/python demo/app.py
```
Open http://127.0.0.1:7860.

## Benign demo scenario
Load "Benign: read workspace file" scenario -> Analyze -> ALLOW, score 1.0.

## Suspicious demo scenario
Load "Suspicious: path traversal" -> Analyze -> BLOCK with R-301.

## Interpreting verdicts
ALLOW (not proof of safety), WARN, BLOCK, ERROR. Show findings, rule IDs,
evidence, trace, raw JSON, download reports.

## Implemented vs not implemented
Implemented: 5-layer engine, 10 rules, UI both tabs, eval, ablation,
adversarial, docs, release. Not: ML, real MCP interception, external
validation, filesystem protection.

## Limitations
See docs/LIMITATIONS.md, docs/THREAT_MODEL.md.

## Suggested live demo sequence
1. Show Stage 1 tab (lexical baseline).
2. Switch to Joint Context; load benign scenario; analyze.
3. Load suspicious scenario; analyze; walk findings.
4. Show raw JSON and download report.
5. Show eval_results.json metrics.