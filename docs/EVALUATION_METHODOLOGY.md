# Evaluation Methodology — MCP-CONSIST

## Dataset
`data/eval_cases.jsonl`: 101 synthetic cases authored by project author.
Provenance: "synthetic, authored by project author". Dev split 54, holdout 47.
12 attack families. Not MCPTox or any external dataset.

## Method
Each case executed through `mcp_consist.analyze()`. Predicted verdict compared to
expected_verdict. Metrics computed by `scripts/evaluate.py`. No hardcoded results.

## Metrics
Accuracy, precision/recall/F1 (binary malicious), macro F1, weighted F1,
per-class, per-family recall, benign FPR, confusion matrix, latency p50/p95.

## Ablation
`scripts/evaluate_ablation.py` genuinely disables layers via enabled_layers.
Configurations: none, each individual, progressive combinations, full.

## Adversarial
`scripts/generate_adversarial_cases.py` applies deterministic bounded
transformations (case, whitespace, zero-width, bidi, unicode normalization)
plus targeted path/host/pivot variants. Results in robustness_results.json.

## Reproducibility
Dataset SHA-256, engine version, source revision, config hash recorded.
Re-running evaluate.py reproduces non-latency metrics.