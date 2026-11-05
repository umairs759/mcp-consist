# Supervisor Handover — MCP-CONSIST

## Overview
MCP-CONSIST is a deterministic five-layer research prototype for joint
context consistency in MCP tool calls. No ML, no real interception.

## Quick start
```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
.venv/bin/python demo/app.py
```
Open http://127.0.0.1:7860.

## Tests
```bash
.venv/bin/python -m pytest -q
```

## Evaluation
```bash
.venv/bin/python scripts/evaluate.py
.venv/bin/python scripts/evaluate_ablation.py
.venv/bin/python scripts/generate_adversarial_cases.py
.venv/bin/python scripts/verify_release.py
```

## Key artifacts
- results/eval_results.json
- results/ablation_results.json
- results/robustness_results.json
- dist/MCP-CONSIST-release.zip
- dist/SHA256SUMS.txt
- dist/screenshots/final_desktop.png

## Limitations
See docs/LIMITATIONS.md, docs/THREAT_MODEL.md. No external validation.