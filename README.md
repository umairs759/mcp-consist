# MCP-CONSIST · Context Integrity & Security Research Workbench

A research prototype for lexical consistency analysis of paired contexts, with
a professional dark workbench UI (Gradio 5.x). Stage 1 is an honest lexical
baseline — no ML, no sandboxing, no MCP traffic monitoring, no claimed
detection performance.

## What this is (Stage 1)

Two inputs are normalised to lowercase, tokenised on whitespace, and compared
by set overlap:

```
overlap = len(set1 & set2) / max(len(set1), len(set2))
```

The overlap is compared to a user-selected threshold (default 0.80) to emit one
of four states: ALLOW / WARN / BLOCK / ERROR.

- **ALLOW** — overlap meets the threshold. NOT proof the content is safe.
- **WARN** — overlap below threshold (and not identical token sets).
- **BLOCK** — identical token sets (prototype rule; see Limitations).
- **ERROR** — empty/whitespace/None/non-string input, input over 20,000 chars,
  or invalid threshold.

## What this is NOT

- No semantics, negation handling, or intent understanding.
- No schema validation, policy enforcement, or rate limiting.
- No MCP server connection, interception, or traffic monitoring.
- No sandbox, no canary credential, no outbound network request.
- No ML — no MiniLM, no XGBoost, no embeddings, no classifier, no trained model.
- Not a security boundary.

See `docs/LIMITATIONS.md` for the full list.

## Files

| File | Purpose |
|------|---------|
| `pipeline.py` | Backend: `run_consistency_check(...)` + `analyze_pair(...)` |
| `demo/app.py` | Gradio workbench UI + real callback wiring |
| `demo/theme.css` | Dark enterprise theme (CSS variables) |
| `demo/components.py` | HTML helpers; every user string `html.escape`d |
| `data/samples.json` | Clearly-labelled safe demo pairs |
| `tests/` | Backend, HTML-contract, and UI-wiring tests |
| `requirements.txt` | Pinned Gradio 5.x + pytest |
| `docs/LIMITATIONS.md` | Honest limitations |
| `docs/SECURITY_REVIEW.md` | Honest security review (no pentesting claim) |

## Implemented

- Lexical overlap detector with real, working `threshold` gating.
- `analyze_pair` returning status, overlap, threshold, matched / unmatched
  terms, explanation, error.
- `run_consistency_check` thin wrapper (backwards-compatible string API).
- Gradio workbench: Context A / B textboxes, live char count, threshold
  slider, Run / Clear All / Load sample, results panel (badge, overlap,
  threshold, terms, explanation), Methodology / Limitations / Project Info
  tabs, XSS-escaped rendering, dark theme.
- 44 passing tests (`pytest -q`): backend, badge HTML contract, UI wiring.

## Reported metrics (provenance stated)

The repo previously carried `results/ablation_results.json` and
`results/adaptive_holdout.json` containing hand-written constants
(accuracy 0.94/0.93, F1 0.915/0.905, etc.). These could **not** be reproduced
from any code in the repository (no training pipeline, no dataset, no
evaluation script existed in Stage 1). They are treated as **unverified,
from earlier experiments / placeholder** and are **not** cited as achieved
performance.

## Independently reproduced

```
# Fresh venv
python3 -m venv .venv
. .venv/bin/activate
pip install -r requirements.txt

# Tests
python -m pytest tests/ -q        # 44 passed (Stage 1.1)
python -m pytest tests/ -v        # verbose

# Launch (local only, no public tunnel)
MCP_CONSIST_HOST=127.0.0.1 PORT=7860 python demo/app.py
```

The app binds to `127.0.0.1:7860` by default. `share=False` by default; a
public tunnel only with `MCP_CONSIST_SHARE=1` (a warning is printed).

## Planned (Stage 2 — not yet implemented)

A deterministic, rule-based `policy-rules-v1` five-layer detector over a joint
context (description, schema, policy, task, call), plus a joint-context UI tab
and a reproducible synthetic benchmark (`data/eval_cases.jsonl`,
`scripts/evaluate.py`). Engine chip updates to `policy-rules-v1`. See
`docs/LIMITATIONS.md`.

## Citation / contact

Research prototype. No arXiv, no DOI, no publication is associated with this
repo. Maintainer: Muhammad Umair (@umairs759).
