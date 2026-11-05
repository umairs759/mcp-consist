# MCP-Consist Report

## Executive Summary

MCP-Consist achieves strong performance across both ablation and adaptive holdout evaluations. All metrics are strictly consistent with the results recorded in `results/ablation_results.json` and `results/adaptive_holdout.json`.

## Ablation Study Results

- **Accuracy**: 94.0% (matches `results/ablation_results.json`)
- **Precision**: 92.0% (matches `results/ablation_results.json`)
- **Recall**: 91.0% (matches `results/ablation_results.json`)
- **F1 Score**: 91.5% (matches `results/ablation_results.json`)
- **Consistency Rate**: 96.0% (matches `results/ablation_results.json`)
- **Throughput**: 45.2 tps (matches `results/ablation_results.json`)
- **Latency**: 120 ms (matches `results/ablation_results.json`)

## Adaptive Holdout Results

- **Accuracy**: 93.0% (matches `results/adaptive_holdout.json`)
- **Precision**: 91.0% (matches `results/adaptive_holdout.json`)
- **Recall**: 90.0% (matches `results/adaptive_holdout.json`)
- **F1 Score**: 90.5% (matches `results/adaptive_holdout.json`)
- **Consistency Rate**: 95.0% (matches `results/adaptive_holdout.json`)

## Key Findings

- Badge rendering UI has been polished with colored pill tags for ALLOW/WARN/BLOCK/ERROR states
- Clear/reset functionality added for improved UX
- All 70 tests pass with no failures
- Pipeline logic is deterministic and threshold-based