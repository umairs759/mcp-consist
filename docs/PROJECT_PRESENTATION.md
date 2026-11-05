# Project Presentation — MCP-CONSIST

## Problem
Tool-poisoning in MCP: malicious intent hidden in descriptions/schemas/calls.

## Motivation
Single-field checks insufficient; need joint, explainable analysis.

## Proposed solution
Five-layer deterministic rule engine (policy-rules-v1) over 5 context inputs.

## Architecture
mcp_consist package + Gradio UI + eval scripts. See docs/ENGINE_ARCHITECTURE.md.

## Five detection layers
Description integrity; sensitive resources; schema/params; policy compliance;
joint intent/pivot.

## Evaluation
101 synthetic cases; acc 0.9109; binary P/R/F1 1.0; macro F1 0.5892;
benign FPR 0.0. Ablation + adversarial suites.

## Results
See results/eval_results.json, ablation_results.json, robustness_results.json.

## Limitations
No ML, no real interception, synthetic data, lexical checks only.

## Future research
Semantic models with real data; MCP proxy; licensed benchmarks.