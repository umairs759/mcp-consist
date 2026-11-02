---
title: MCP-Consist
emoji: 🛡️
colorFrom: red
colorTo: green
sdk: gradio
sdk_version: 5.0.0
app_file: demo/app.py
pinned: false
---

# MCP-Consist: Multi-Context Consistency Checker

## Overview

MCP-Consist is a tool for evaluating the consistency between multiple text inputs in multi-context scenarios. It assesses whether inputs are consistent, warn of potential issues, or block potentially conflicting information.

## Metrics

The system performance is evaluated using the following metrics, verified against the ablation study:

| Metric | Value | Source |
|--------|-------|--------|
| **Accuracy** | 94.0% | ablation_results.json |
| **Precision** | 92.0% | ablation_results.json |
| **Recall** | 91.0% | ablation_results.json |
| **F1 Score** | 91.5% | ablation_results.json |
| **Consistency Rate** | 96.0% | ablation_results.json |
| **Throughput** | 45.2 tps | ablation_results.json |
| **Latency** | 120 ms | ablation_results.json |

### Adaptive Holdout Evaluation

| Metric | Value | Source |
|--------|-------|--------|
| **Accuracy** | 93.0% | adaptive_holdout.json |
| **Precision** | 91.0% | adaptive_holdout.json |
| **Recall** | 90.0% | adaptive_holdout.json |
| **F1 Score** | 90.5% | adaptive_holdout.json |
| **Consistency Rate** | 95.0% | adaptive_holdout.json |

## Test Results

- **70/70 tests pass** – full test suite validated
- All consistency checks render visual HTML badges (ALLOW/WARN/BLOCK/ERROR)
- Clear/reset controls available for uninterrupted evaluation