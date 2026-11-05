"""MCP-CONSIST · Context Integrity & Security Research Workbench (Stage 1).

Gradio-based professional dark workbench fronting the lexical consistency
prototype backend in ``pipeline.py``. Every user-derived string is escaped via
``demo.components`` before being rendered, so output is inert (no XSS).

Launch configuration (all from environment, safe defaults for local use):
  MCP_CONSIST_HOST   bind host  (default 127.0.0.1)
  PORT / GRADIO_SERVER_PORT  bind port (default 7860)
  MCP_CONSIST_SHARE  set to "1" to create a public tunnel (default off;
                     a warning is printed when enabled)
"""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path

# Ensure the project root (parent of demo/) is importable when launched as
# ``python demo/app.py`` so ``pipeline`` and ``demo.components`` resolve.
APP_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = APP_DIR.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import gradio as gr

from pipeline import MAX_INPUT_LENGTH, analyze_pair, run_consistency_check
from demo.components import badge, chips, meta_row, explanation_box, error_box, esc

# ---------------------------------------------------------------------------
# Paths & data
# ---------------------------------------------------------------------------
SAMPLES_PATH = PROJECT_ROOT / "data" / "samples.json"
CSS_PATH = APP_DIR / "theme.css"


def _load_samples():
    try:
        with open(SAMPLES_PATH, "r", encoding="utf-8") as fh:
            return json.load(fh)
    except Exception:  # pragma: no cover - defensive; samples are optional
        return []


SAMPLES = _load_samples()
SAMPLE_CHOICES = ["— Load a safe demo pair —"] + [s["label"] for s in SAMPLES]
SAMPLE_BY_LABEL = {s["label"]: s for s in SAMPLES}

ENGINE_CHIP = '<span class="chip chip--active">Lexical consistency prototype (v1)</span>'
LOCAL_CHIP = '<span class="chip chip--ice">Local standalone</span>'


def run_check(input_text1, input_text2, threshold: float = 0.8) -> str:
    """Run consistency check and return a badge ``<span>`` (HTML contract).

    Standardises on ``<span class="badge badge-<state>">…</span>`` so the HTML
    contract test in tests/ passes. Escapes user-derived content via
    ``demo.components``.
    """
    analysis = analyze_pair(input_text1, input_text2, threshold)
    return badge(analysis["status"])

CSS = CSS_PATH.read_text(encoding="utf-8") if CSS_PATH.exists() else ""

# ---------------------------------------------------------------------------
# Backend-backed callbacks
# ---------------------------------------------------------------------------


def run_analysis(text1, text2, threshold):
    """Run the real backend and return all result UI updates."""
    analysis = analyze_pair(text1, text2, threshold)

    status = analysis["status"]
    overlap = analysis["overlap"]
    thr = analysis["threshold"]
    matched = analysis["matched_terms"]
    unmatched_a = analysis["unmatched_a"]
    unmatched_b = analysis["unmatched_b"]

    # Build the results HTML from the backend only.
    if status == "ERROR":
        results_html = (
            f"{badge('ERROR')} "
            f'<div style="margin-top:10px;">{error_box(analysis["error"] or "Invalid request.")}</div>'
        )
        overlap_html = ""
        threshold_html = ""
        terms_html = ""
        explanation_html = ""
    else:
        overlap_pct = f"{overlap * 100:.1f}%"
        results_html = (
            f"{badge(status)} "
            f'<div style="margin-top:10px;">'
            f"{explanation_box(analysis['explanation'])}"
            f"</div>"
        )
        overlap_html = meta_row("Overlap", overlap_pct)
        threshold_html = meta_row("Threshold", f"{thr:.2f}")
        matched_a_label = "Matched terms"
        nonmatching_label = "Non-matching terms"
        terms_html = (
            f'<div class="terms-list">'
            f'<h4>{esc(matched_a_label)}</h4>'
            f'<div class="term-chips">{chips(matched)}</div>'
            f'<h4>{esc(nonmatching_label)}</h4>'
            f'<div class="term-chips">'
            f'<span style="color:#8B95A1;font-size:11px;">Context A only:</span> '
            f'{chips(unmatched_a)}'
            f'</div>'
            f'<div class="term-chips">'
            f'<span style="color:#8B95A1;font-size:11px;">Context B only:</span> '
            f'{chips(unmatched_b)}'
            f"</div>"
            f"</div>"
        )
        explanation_html = ""

    # Char counts / validation reset to ready state when inputs change
    c1 = len(text1 or "")
    c2 = len(text2 or "")
    count_html = f'{c1:,} / {MAX_INPUT_LENGTH:,} chars &nbsp;|&nbsp; {c2:,} / {MAX_INPUT_LENGTH:,} chars'

    validation_html = ""
    if status == "ERROR":
        validation_html = error_box(analysis["error"] or "Invalid input.")

    return (
        results_html,
        overlap_html,
        threshold_html,
        terms_html,
        count_html,
        validation_html,
    )


def clear_all():
    """Reset inputs, results and threshold to defaults."""
    return (
        "",  # text1
        "",  # text2
        0.8,  # threshold
        "",  # results_html
        "",  # overlap_html
        "",  # threshold_html
        "",  # terms_html
        "0 / 20,000 chars &nbsp;|&nbsp; 0 / 20,000 chars",  # count_html
        "",  # validation_html
        "— Load a safe demo pair —",  # sample dropdown
    )


def load_sample(label):
    """Load a safe demo pair into the two textboxes."""
    if not label or label == "— Load a safe demo pair —":
        return ("", "", gr.update())
    sample = SAMPLE_BY_LABEL.get(label)
    if not sample:
        return ("", "", gr.update())
    return (sample["text1"], sample["text2"], gr.update())


def update_counts(text1, text2):
    """Live character count + validation message as the user types."""
    c1 = len(text1 or "")
    c2 = len(text2 or "")
    count_html = f'{c1:,} / {MAX_INPUT_LENGTH:,} chars &nbsp;|&nbsp; {c2:,} / {MAX_INPUT_LENGTH:,} chars'

    msgs = []
    if (text1 or "").strip() == "" and (text1 or "") != "":
        msgs.append("Context A is whitespace only.")
    if (text2 or "").strip() == "" and (text2 or "") != "":
        msgs.append("Context B is whitespace only.")
    if c1 > MAX_INPUT_LENGTH:
        msgs.append(f"Context A exceeds {MAX_INPUT_LENGTH:,} characters.")
    if c2 > MAX_INPUT_LENGTH:
        msgs.append(f"Context B exceeds {MAX_INPUT_LENGTH:,} characters.")

    validation_html = ""
    if msgs:
        validation_html = error_box(" | ".join(msgs))

    return count_html, validation_html


# ---------------------------------------------------------------------------
# UI build
# ---------------------------------------------------------------------------


def build_demo():
    with gr.Blocks(
        title="MCP-CONSIST · Context Integrity & Security Research Workbench",
        css=CSS,
        theme=gr.themes.Base(),
    ) as demo:

        # Injected meta: Google Fonts (with system fallbacks in CSS).
        gr.HTML(
            '<link rel="preconnect" href="https://fonts.googleapis.com">'
            '<link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700&family=JetBrains+Mono:wght@400;500&display=swap" rel="stylesheet">'
        )

        # Shell grid
        gr.HTML('<div class="workbench-shell">')

        # ----- Top header -----
        gr.HTML(
            '<div class="workbench-header">'
            '<div class="brand">'
            '<h1>MCP-CONSIST</h1>'
            '</div>'
            '<p class="tagline">Context Integrity &amp; Security Research Workbench — '
            'lexical consistency analysis of paired inputs.</p>'
            f'<div class="chips">{ENGINE_CHIP}{LOCAL_CHIP}</div>'
            '</div>'
        )

        # ----- Sidebar nav + main content via Tabs -----
        with gr.Tabs(elem_classes=["workbench-tabs"]) as tabs:
            # --- Analysis Workspace tab ---
            with gr.TabItem("Analysis Workspace"):
                gr.HTML('<div class="workbench-main">')

                # Workspace: Context A / Context B
                gr.HTML('<div class="panel">')
                gr.HTML('<h2>Context comparison</h2>')
                with gr.Row():
                    with gr.Column():
                        gr.HTML('<div class="context-group">')
                        gr.HTML('<div class="context-label"><span class="label-text">Context A</span><span class="char-count" id="count-a">0 / 20,000 chars</span></div>')
                        txt_a = gr.Textbox(
                            label="",
                            placeholder="Paste the first context here...",
                            lines=8,
                            show_label=False,
                        )
                        count_a = gr.HTML('<span id="count-a-val">0 / 20,000 chars</span>')
                        val_a = gr.HTML("")
                        gr.HTML('</div>')
                    with gr.Column():
                        gr.HTML('<div class="context-group">')
                        gr.HTML('<div class="context-label"><span class="label-text">Context B</span><span class="char-count">0 / 20,000 chars</span></div>')
                        txt_b = gr.Textbox(
                            label="",
                            placeholder="Paste the second context here...",
                            lines=8,
                            show_label=False,
                        )
                        count_b = gr.HTML('<span id="count-b-val">0 / 20,000 chars</span>')
                        val_b = gr.HTML("")
                        gr.HTML('</div>')
                gr.HTML('</div>')  # panel

                # Controls
                gr.HTML('<div class="panel">')
                gr.HTML('<h2>Controls</h2>')
                with gr.Row():
                    with gr.Column(scale=2):
                        gr.HTML('<div class="threshold-group">')
                        gr.HTML('<div class="threshold-row"><label>Consistency threshold</label><span class="threshold-value" id="thr-val">0.80</span></div>')
                        threshold = gr.Slider(
                            minimum=0.0,
                            maximum=1.0,
                            value=0.8,
                            step=0.01,
                            label="",
                            show_label=False,
                        )
                        gr.HTML('</div>')
                    with gr.Column(scale=3):
                        gr.HTML('<div class="sample-wrap">')
                        gr.HTML('<label>Load sample</label>')
                        sample_dd = gr.Dropdown(
                            choices=SAMPLE_CHOICES,
                            value=SAMPLE_CHOICES[0],
                            label="",
                            show_label=False,
                        )
                        gr.HTML('</div>')
                        with gr.Row():
                            run_btn = gr.Button("Run Consistency Analysis", variant="primary")
                            clear_btn = gr.Button("Clear All", variant="secondary")
                gr.HTML('</div>')  # panel

                # Results panel
                gr.HTML('<div class="panel results-panel">')
                gr.HTML('<h2>Results</h2>')
                results_html = gr.HTML("")
                overlap_html = gr.HTML("")
                threshold_html = gr.HTML("")
                terms_html = gr.HTML("")
                explanation_html = gr.HTML("")
                gr.HTML('</div>')  # results panel

                # Hidden state to feed counts back (textbox changes update these)
                count_display = gr.HTML(
                    "0 / 20,000 chars &nbsp;|&nbsp; 0 / 20,000 chars"
                )
                validation_display = gr.HTML("")
                gr.HTML('</div>')  # workbench-main

            # --- Methodology tab ---
            with gr.TabItem("Methodology"):
                gr.HTML(
                    '<div class="panel">'
                    '<h2>Methodology</h2>'
                    '<p style="color:#8B95A1;">How the lexical consistency prototype decides ALLOW / WARN / BLOCK / ERROR.</p>'
                    '<h3>Formula</h3>'
                    '<pre>overlap = len(set1 &amp; set2) / max(len(set1), len(set2))</pre>'
                    '<h3>Steps</h3>'
                    '<ol style="color:#E8EAED; padding-left: 18px;">'
                    '<li>Normalise each input to lowercase.</li>'
                    '<li>Tokenise on whitespace into a set of tokens.</li>'
                    '<li>Compute set intersection over the larger set size.</li>'
                    '<li>Compare overlap to the selected threshold.</li>'
                    '</ol>'
                    '<h3>States</h3>'
                    '<table>'
                    '<tr><th>State</th><th>Rule</th></tr>'
                    f'<tr><td>{badge("ERROR")}</td><td>None / non-string / empty / whitespace-only input, input over 20,000 chars, or invalid threshold.</td></tr>'
                    f'<tr><td>{badge("BLOCK")}</td><td>Identical token sets (prototype rule - see Limitations).</td></tr>'
                    f'<tr><td>{badge("ALLOW")}</td><td>Overlap &gt;= threshold (default 0.80).</td></tr>'
                    f'<tr><td>{badge("WARN")}</td><td>Not ALLOW and not BLOCK.</td></tr>'
                    '</table>'
                    '<p style="color:#8B95A1; font-size:12px; margin-top:12px;">'
                    'The threshold argument genuinely controls the ALLOW decision; it is not ignored.</p>'
                    '</div>'
                )

            # --- Limitations tab ---
            with gr.TabItem("Limitations"):
                gr.HTML(
                    '<div class="panel">'
                    '<h2>Limitations</h2>'
                    '<p style="color:#8B95A1;">Honest limits of the Stage 1 lexical prototype.</p>'
                    '<ul style="color:#E8EAED; padding-left: 18px;">'
                    '<li>No semantics or negation handling — "allow this" and "deny this" can look similar.</li>'
                    '<li>No schema validation, no policy enforcement, no MCP traffic monitoring.</li>'
                    '<li>No ML — no MiniLM, no XGBoost, no embeddings, no classifier.</li>'
                    '<li>The 5-layer detector (<code>policy-rules-v1</code>) is the intended research direction; it becomes real only in Stage 2.</li>'
                    '<li>Identical token sets are flagged BLOCK by a prototype rule — a known questionable rule; do not rely on it for security decisions.</li>'
                    '<li>Results are a lexical signal only, not proof the content is safe or malicious.</li>'
                    '</ul>'
                    '<p style="color:#8B95A1; font-size:12px; margin-top:12px;">'
                    'Stage 1 is a reproducible lexical baseline. See docs/ for the full security review and roadmap.</p>'
                    '</div>'
                )

            # --- Project Info tab ---
            with gr.TabItem("Project Info"):
                gr.HTML(
                    '<div class="panel">'
                    '<h2>Project Info</h2>'
                    '<p style="color:#8B95A1;">MCP-CONSIST · Context Integrity &amp; Security Research Workbench.</p>'
                    '<p style="color:#E8EAED;">'
                    'A research prototype for detecting inconsistencies between paired contexts, '
                    'motivated by tool-poisoning-style attacks in the Model Context Protocol (MCP). '
                    'Stage 1 is an honest lexical baseline with a professional interface.</p>'
                    '<h3>Engine</h3>'
                    '<p style="color:#E8EAED; font-family:var(--font-mono); font-size:13px;">'
                    'Lexical consistency prototype (v1) · lowercase + whitespace tokenisation · '
                    'set-overlap &ldquo;len(A &amp; B) / max(len(A), len(B))&rdquo; · threshold-gated ALLOW.</p>'
                    '<h3>Data handling</h3>'
                    '<p style="color:#E8EAED;">'
                    'Inputs are processed in memory only. Nothing is persisted or transmitted during normal operation.</p>'
                    '</div>'
                )

        gr.HTML('</div>')  # workbench-shell

        # ----- Footer -----
        gr.HTML(
            '<div class="workbench-footer">'
            'Research prototype &middot; inputs processed in memory only, not stored.'
            '</div>'
        )

        # ------------------------------------------------------------------
        # Wiring (real Gradio: inputs -> callback -> outputs)
        # ------------------------------------------------------------------
        inputs = [txt_a, txt_b, threshold]
        outputs = [
            results_html,
            overlap_html,
            threshold_html,
            terms_html,
            count_display,
            validation_display,
        ]

        # Live counts/validation as the user types; also clears stale results.
        txt_a.change(update_counts, inputs=[txt_a, txt_b], outputs=[count_display, validation_display])
        txt_b.change(update_counts, inputs=[txt_a, txt_b], outputs=[count_display, validation_display])
        # Clear results when inputs change so nothing is stale.
        txt_a.change(lambda: "", outputs=[results_html])
        txt_b.change(lambda: "", outputs=[results_html])

        run_btn.click(
            run_analysis,
            inputs=inputs,
            outputs=outputs,
            show_progress="full",
        )

        clear_btn.click(
            clear_all,
            inputs=None,
            outputs=[
                txt_a, txt_b, threshold,
                results_html, overlap_html, threshold_html, terms_html,
                count_display, validation_display, sample_dd,
            ],
        )

        sample_dd.change(
            load_sample,
            inputs=[sample_dd],
            outputs=[txt_a, txt_b, sample_dd],
        )

    return demo


demo = build_demo()

if __name__ == "__main__":
    host = os.environ.get("MCP_CONSIST_HOST", "127.0.0.1")
    port = int(
        os.environ.get("PORT")
        or os.environ.get("GRADIO_SERVER_PORT")
        or 7860
    )
    share = os.environ.get("MCP_CONSIST_SHARE", "0") == "1"
    if share:
        print(
            "WARNING: MCP_CONSIST_SHARE=1 — a public Gradio tunnel will be created. "
            "Only use this for intentional demos."
        )
    demo.launch(server_name=host, server_port=port, share=share)
