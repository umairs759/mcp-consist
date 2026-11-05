# MCP-CONSIST Baseline Audit — Stage 1.1 (commit 271d9e5)

**Date:** 2026-11-05  
**Branch:** master  
**HEAD:** 271d9e5 `fix(ui): repair stage1 workbench rendering and interactions`  
**Tag:** stage1-verified-271d9e5  
**Test result:** 44 passed (`python -m pytest -q`)  
**Gradio:** 5.50.0  
**Python env:** `.venv/`

---

## Existing features

### Backend — `pipeline.py` (lexical consistency prototype)
- `analyze_pair(text1, text2, threshold=0.8) -> dict`: lowercase + whitespace tokenisation, set overlap `len(set1 & set2) / max(len(set1), len(set2))`.
- `run_consistency_check(...) -> str`: thin wrapper returning one of ALLOW / WARN / BLOCK / ERROR.
- Input validation: None / non-string / empty / whitespace-only / >20,000 chars → ERROR.
- Threshold validation: must be a number in [0, 1]; booleans/strings/None/out-of-range → ERROR.
- Prototype rule: identical token sets → BLOCK regardless of threshold (documented, retained).
- Threshold genuinely gates ALLOW (`overlap >= threshold` → ALLOW).
- Structured output: status, overlap, threshold, matched_terms, unmatched_a, unmatched_b, explanation, error.

### UI — `demo/app.py` (Gradio 5.50.0 dark workbench)
- Analysis Workspace tab: Context A / B textboxes, live char counts, validation messages, threshold slider, Run / Clear All / Load sample.
- Results panel: status badge, overlap %, threshold, matched / non-matching terms, explanation, error details.
- Methodology, Limitations, Project Info tabs.
- Real Gradio wiring: inputs → callback → outputs; all callbacks registered (`run_analysis`, `clear_all`, `load_sample`, `update_counts_a/b`, `clear_results`, `update_threshold_display`).
- XSS-escaped rendering via `demo.components` (`html.escape` on every user string).
- Localhost default (`127.0.0.1:7860`), `share=False`, analytics disabled, no external resources.
- `ENGINE_CHIP` = "Lexical consistency prototype (v1)".

### UI helpers — `demo/components.py`
- `badge()`, `chips()`, `meta_row()`, `explanation_box()`, `error_box()`, `esc()` — all escape user-derived strings.

### Theme — `demo/theme.css`
- Dark enterprise theme, design tokens: bg `#08090C`, panel `#11151B`, border `#252B34`, text `#E8EAED`, muted `#8B95A1`, amber `#E5A93C`, ice `#4E80EE`, allow `#34D399`, warn `#E5A93C`, block `#F87171`, error `#9CA3AF`.
- Responsive breakpoints at 768px and 375px.

### Data
- `data/samples.json`: 4 clearly-labelled safe demo pairs (benign high/low overlap, identical, case-insensitive).

### Tests (44 total)
- `tests/test_app.py`: backend behaviour (ALLOW/WARN/BLOCK/ERROR, threshold gating, validation, structured output).
- `tests/test_contract.py`: HTML badge contract for `demo.app.run_check`.
- `tests/test_ui.py`: UI wiring tests, XSS rendering, callback registration, component existence.

### Docs
- `docs/LIMITATIONS.md`: honest limitations (no semantics, no schema, no policy, no MCP monitoring, no ML, not a security boundary).
- `docs/SECURITY_REVIEW.md`: honest security review (no pentesting claim).
- `README.md`, `REPORT.md`, `SECURITY.md`, `data/DATASHEET.md`.

---

## Existing architecture

```
pipeline.py                      # Stage 1 lexical backend (analyze_pair / run_consistency_check)
demo/app.py                      # Stage 1 Gradio UI (Analysis Workspace)
demo/components.py               # HTML helpers (escaping)
demo/theme.css                   # Dark theme + tokens
data/samples.json                # Safe demo pairs
tests/                           # 44 Stage 1 tests
requirements.txt                 # gradio==5.50.0, pytest==9.2.0
```

The Stage 1 backend and UI are separate concerns with no shared state. `pipeline.py` is importable standalone; `demo/app.py` adds the project root to `sys.path` and imports from `pipeline` and `demo.components`.

---

## Actual test count

44 tests, all passing:
- `tests/test_app.py`: 22 tests
- `tests/test_contract.py`: 4 tests
- `tests/test_ui.py`: 18 tests

Verified with `.venv/bin/python -m pytest -q` → `44 passed in ~3s`.

---

## Verified behaviours (from tests)

- Threshold behaviour: ALLOW when `overlap >= threshold`; WARN otherwise; threshold boundaries 0.0 and 1.0 valid; invalid thresholds → ERROR.
- Identical token-set BLOCK behaviour (prototype rule).
- All four result states: ALLOW, WARN, BLOCK, ERROR.
- XSS protection: `<img ...>`, `<script>...</script>`, `<svg ...>` escaped; no raw tags render; `&lt;` / `&gt;` present.
- Clear All: resets inputs, results, threshold (0.8), sample dropdown.
- Sample loading: safe demo pairs from `data/samples.json`; placeholder returns empty.
- Character counters: per-input live counts with validation messages.
- Responsive interface: CSS breakpoints at 768px and 375px.
- Existing Gradio callbacks: all registered and wired.

---

## Known limitations (Stage 1)

Documented in `docs/LIMITATIONS.md` and `docs/SECURITY_REVIEW.md`:
- No semantics, negation handling, or intent understanding.
- No schema validation, parameter typing, or constraint checking.
- No policy enforcement, allow-lists, deny-lists, rate limits, or credential scopes.
- No MCP server connection, interception, or traffic monitoring.
- No sandbox, no canary credential, no outbound network request.
- No ML — no MiniLM, no XGBoost, no embeddings, no classifier.
- Not a security boundary; ALLOW is not proof of safety; BLOCK does not intercept.
- Identical token-set → BLOCK is a known questionable prototype rule.
- No reproducible evaluation, dataset, or claimed performance in Stage 1 (`results/_unverified/` contents are hand-written, unverified placeholders).

---

## Technical debt

- `results/_unverified/` contains `ablation_results.json` and `adaptive_holdout.json` — hand-written constants from earlier experiments, not reproducible from any code. Clearly labelled as unverified and not cited as achieved performance.
- `pipeline_output.txt`, `pipeline_result.txt` (empty) — root-level artifacts from earlier runs; not part of the project (covered by `.gitignore` `*_output.txt`, `*_result.txt`).
- `__pycache__/` and `.pytest_cache/` directories present; covered by `.gitignore`.
- `tests/__pycache__/` contains `.pyc` files; covered by `.gitignore`.

---

## Files that must remain backward compatible

| File | Why |
|------|-----|
| `pipeline.py` | Stage 1 backend API (`analyze_pair`, `run_consistency_check`, `MAX_INPUT_LENGTH`) used by `demo/app.py` and tests. |
| `demo/app.py` | Stage 1 Analysis Workspace UI; must keep functioning unchanged. |
| `demo/components.py` | HTML escaping helpers used by the UI and contract tests. |
| `demo/theme.css` | Stage 1 visual identity and design tokens. |
| `data/samples.json` | Stage 1 sample loader source. |
| `tests/test_app.py`, `tests/test_contract.py`, `tests/test_ui.py` | 44 Stage 1 tests must continue to pass. |
| `requirements.txt` | Pinned dependency file (`gradio==5.50.0`, `pytest==9.2.0`). |

---

## Phase gate

Phase 0 complete: existing system audited, baseline recorded, 44 tests pass, git tag created, backup made. Ready to proceed to Phase 1.
