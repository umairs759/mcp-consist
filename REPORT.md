# REPORT — MCP-CONSIST

## Abstract
MCP-CONSIST is a deterministic, rule-based research prototype that detects
inconsistencies across five joint context inputs (tool description, schema,
capability policy, user task, proposed tool call) for MCP-style tool poisoning.
It implements 10 rules over 5 layers, emits ALLOW/WARN/BLOCK/ERROR, and is
evaluated on 101 synthetic cases. No ML, no real MCP interception.

## Introduction
Tool-poisoning attacks can hide malicious intent in any one field. Single-field
checks are insufficient; joint analysis is required.

## Problem statement
Detect inconsistencies between description, schema, policy, task, and call.

## Research objective
Build an explainable, reproducible, deterministic detector and evaluate it
honestly on synthetic data.

## Threat model
See docs/THREAT_MODEL.md.

## Methodology
Five-layer rule engine with centralized severity penalties and documented
verdict policy. See docs/ENGINE_ARCHITECTURE.md and docs/RULE_CATALOG.md.

## System architecture
See docs/ENGINE_ARCHITECTURE.md.

## Rule implementation
10 rules R-101..R-501 across 5 layers. See docs/RULE_CATALOG.md.

## Experimental setup
101 synthetic cases, dev 54 / holdout 47, 12 families.

## Dataset provenance
Synthetic, authored by project author. Not MCPTox or external data.

## Results
Accuracy 0.9109; binary P/R/F1 1.0/1.0/1.0; macro F1 0.5892; weighted F1
0.8924; benign FPR 0.0. Latency p50 0.18ms, p95 0.59ms. Confusion: ALLOW
53/53, BLOCK 35/35, WARN 4 correct / 9 predicted BLOCK.

## Ablation
Full five layers: acc 0.9109. Single layers range 0.56-0.81. Progressive
combination shows monotonic improvement. See results/ablation_results.json.

## Error analysis
WARN cases often classified BLOCK due to high-severity co-triggers; this is
conservative (favors blocking). False positives 0 on eval set. Adversarial
suite reports verdict flips (see results/robustness_results.json).

## Discussion
Deterministic rules provide explainability but limited generalization. WARN
vs BLOCK boundary is conservative.

## Limitations
See docs/LIMITATIONS.md and threat model. No ML, no real interception, no
external validation, synthetic data only.

## Ethical considerations
No real user data; inputs not executed; no outbound requests; research
prototype not a security boundary.

## Conclusion
A complete, tested, documented, reproducible research prototype suitable for
supervisor presentation.

## Future work
Semantic intent models with real data; MCP proxy integration; licensed
external benchmarks.