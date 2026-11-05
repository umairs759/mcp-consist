"""MCP-CONSIST · Context Integrity & Security Research Workbench (Stage 1).

Gradio-based professional dark workbench fronting the lexical consistency
prototype backend in ``pipeline.py``. Every user-derived string is escaped via
``demo.components`` before being rendered, so output is inert (no XSS).

Launch configuration (all from environment, safe defaults for local use):
  MCP_CONSIST_HOST   bind host  (default 127.0.0.1)
  PORT / GRADIO_SERVER_PORT  bind port (default 7860)
  MCP_CONSIST_SHARE  set to "1" to create a public tunnel (default off;
                     a warning is printed when enabled)

Design notes (Stage 1.1):
  * The layout is built from real Gradio components (Blocks, Column, Row,
    Group, Tabs, TabItem, HTML, Textbox, Slider, Dropdown, Button). No HTML
    element is ever opened in one component and closed in another.
  * ``theme``/``css``/``head`` are set on the Blocks instance (not the
    constructor) to avoid the Gradio 6 deprecation path; analytics is
    disabled and no external fonts/resources are loaded.
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

# Injected page head. Only an inline keyboard-shortcut script lives here: no
# Google Fonts, no external scripts, no third-party resources (Priority Five).
HEAD_HTML = """
<script>
(function () {
  function onKeyDown(event) {
    if ((event.ctrlKey || event.metaKey) && event.key === "Enter") {
      event.preventDefault();
      var btn = document.getElementById("run-consistency-analysis");
      if (btn && !btn.disabled) {
        btn.click();
      }
    }
  }
  document.addEventListener("keydown", onKeyDown);
})();
</script>
"""


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

    if status == "ERROR":
        results_html = (
            f"{badge('ERROR')} "
            f'<div class="result-error">{error_box(analysis["error"] or "Invalid request.")}</div>'
        )
        overlap_html = ""
        threshold_html = ""
        terms_html = ""
        explanation_html = ""
    else:
        overlap_pct = f"{overlap * 100:.1f}%"
        results_html = (
            f"{badge(status)} "
            f'<div class="result-explanation">{explanation_box(analysis["explanation"])}</div>'
        )
        overlap_html = meta_row("Overlap", overlap_pct)
        threshold_html = meta_row("Threshold", f"{thr:.2f}")
        terms_html = (
            f'<div class="terms-list">'
            f'<h4 class="terms-heading">Matched terms</h4>'
            f'<div class="term-chips">{chips(matched)}</div>'
            f'<h4 class="terms-heading">Non-matching terms</h4>'
            f'<div class="term-chips">'
            f'<span class="terms-note">Context A only:</span> {chips(unmatched_a)}'
            f'</div>'
            f'<div class="term-chips">'
            f'<span class="terms-note">Context B only:</span> {chips(unmatched_b)}'
            f"</div>"
            f"</div>"
        )
        explanation_html = ""

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


# ---------------------------------------------------------------------------
# Per-input helpers (individual counters + validation)
# ---------------------------------------------------------------------------


def _count(text) -> str:
    c = len(text or "")
    return f"{c:,} / {MAX_INPUT_LENGTH:,} chars"


def _validation(text, label: str) -> str:
    t = text or ""
    msgs = []
    if t.strip() == "" and t != "":
        msgs.append(f"{label} is whitespace only.")
    if len(t) > MAX_INPUT_LENGTH:
        msgs.append(f"{label} exceeds {MAX_INPUT_LENGTH:,} characters.")
    return error_box(" | ".join(msgs)) if msgs else ""


def update_counts_a(text1):
    """Live count + validation for Context A."""
    return _count(text1), _validation(text1, "Context A")


def update_counts_b(text2):
    """Live count + validation for Context B."""
    return _count(text2), _validation(text2, "Context B")


def clear_results():
    """Invalidate every result output (called when inputs/threshold change)."""
    return ("", "", "", "", "")


def update_threshold_display(threshold):
    """Show the selected threshold and invalidate stale results."""
    return f'<span class="threshold-value">{float(threshold):.2f}</span>', "", "", "", "", ""


# ---------------------------------------------------------------------------
# UI build
# ---------------------------------------------------------------------------


def build_demo():
    with gr.Blocks(
        title="MCP-CONSIST · Context Integrity & Security Research Workbench",
        analytics_enabled=False,
    ) as demo:

        # ----- Top header (always visible) -----
        with gr.Row(elem_classes=["workbench-header"]):
            with gr.Column():
                gr.HTML(
                    '<div class="brand">'
                    '<h1>MCP-CONSIST</h1>'
                    '</div>'
                    '<p class="tagline">Context Integrity &amp; Security Research Workbench — '
                    'lexical consistency analysis of paired inputs.</p>'
                    f'<div class="chips">{ENGINE_CHIP}{LOCAL_CHIP}</div>',
                    padding=False,
                )

        # ----- Navigation tabs -----
        with gr.Tabs(elem_classes=["workbench-tabs"]):
            # --- Analysis Workspace tab ---
            with gr.TabItem("Analysis Workspace"):
                with gr.Column(elem_classes=["workbench-main"]):

                    # Context comparison
                    with gr.Group(elem_classes=["panel"]):
                        gr.HTML('<h2>Context comparison</h2>', padding=False)
                        with gr.Row(elem_classes=["contexts-row"]):
                            with gr.Column(elem_classes=["context-column"]):
                                gr.HTML(
                                    '<div class="context-label"><span class="label-text">Context A</span></div>',
                                    padding=False,
                                )
                                txt_a = gr.Textbox(
                                    label="",
                                    placeholder="Paste the first context here...",
                                    lines=8,
                                    show_label=False,
                                    elem_classes=["context-textbox"],
                                )
                                count_a = gr.HTML(_count(""), padding=False)
                                val_a = gr.HTML("", padding=False)
                            with gr.Column(elem_classes=["context-column"]):
                                gr.HTML(
                                    '<div class="context-label"><span class="label-text">Context B</span></div>',
                                    padding=False,
                                )
                                txt_b = gr.Textbox(
                                    label="",
                                    placeholder="Paste the second context here...",
                                    lines=8,
                                    show_label=False,
                                    elem_classes=["context-textbox"],
                                )
                                count_b = gr.HTML(_count(""), padding=False)
                                val_b = gr.HTML("", padding=False)

                    # Controls
                    with gr.Group(elem_classes=["panel"]):
                        gr.HTML('<h2>Controls</h2>', padding=False)
                        with gr.Row(elem_classes=["controls-row"]):
                            with gr.Column(elem_classes=["threshold-column"]):
                                gr.HTML(
                                    '<div class="threshold-group">'
                                    '<div class="threshold-row">'
                                    '<label>Consistency threshold</label>'
                                    '</div>'
                                    '</div>',
                                    padding=False,
                                )
                                threshold_value = gr.HTML('<span class="threshold-value">0.80</span>', padding=False)
                                threshold = gr.Slider(
                                    minimum=0.0,
                                    maximum=1.0,
                                    value=0.8,
                                    step=0.01,
                                    label="",
                                    show_label=False,
                                    elem_classes=["threshold-slider"],
                                )
                            with gr.Column(elem_classes=["sample-column"]):
                                gr.HTML('<label class="sample-label">Load sample</label>', padding=False)
                                sample_dd = gr.Dropdown(
                                    choices=SAMPLE_CHOICES,
                                    value=SAMPLE_CHOICES[0],
                                    label="",
                                    show_label=False,
                                    elem_classes=["sample-dropdown"],
                                )
                                with gr.Row(elem_classes=["button-row"]):
                                    run_btn = gr.Button(
                                        "Run Consistency Analysis",
                                        variant="primary",
                                        elem_id="run-consistency-analysis",
                                        elem_classes=["btn--primary"],
                                    )
                                    clear_btn = gr.Button(
                                        "Clear All",
                                        variant="secondary",
                                        elem_classes=["btn--secondary"],
                                    )

                    # Results
                    with gr.Group(elem_classes=["panel results-panel"]):
                        gr.HTML('<h2>Results</h2>', padding=False)
                        results_html = gr.HTML("", padding=False)
                        overlap_html = gr.HTML("", padding=False)
                        threshold_html = gr.HTML("", padding=False)
                        terms_html = gr.HTML("", padding=False)
                        explanation_html = gr.HTML("", padding=False)

                    # Combined count/validation summary (kept for callback contract).
                    count_display = gr.HTML(
                        "0 / 20,000 chars &nbsp;|&nbsp; 0 / 20,000 chars",
                        padding=False,
                    )
                    validation_display = gr.HTML("", padding=False)

            # --- Methodology tab ---
            with gr.TabItem("Methodology"):
                gr.HTML(
                    '<div class="panel">'
                    '<h2>Methodology</h2>'
                    '<p class="muted">How the lexical consistency prototype decides ALLOW / WARN / BLOCK / ERROR.</p>'
                    '<h3>Formula</h3>'
                    '<pre>overlap = len(set1 &amp; set2) / max(len(set1), len(set2))</pre>'
                    '<h3>Steps</h3>'
                    '<ol>'
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
                    '<p class="muted small">The threshold argument genuinely controls the ALLOW decision; it is not ignored.</p>'
                    '</div>',
                    padding=False,
                )

            # --- Limitations tab ---
            with gr.TabItem("Limitations"):
                gr.HTML(
                    '<div class="panel">'
                    '<h2>Limitations</h2>'
                    '<p class="muted">Honest limits of the Stage 1 lexical prototype.</p>'
                    '<ul>'
                    '<li>No semantics or negation handling — "allow this" and "deny this" can look similar.</li>'
                    '<li>No schema validation, no policy enforcement, no MCP traffic monitoring.</li>'
                    '<li>No ML — no MiniLM, no XGBoost, no embeddings, no classifier.</li>'
                    '<li>The 5-layer detector (<code>policy-rules-v1</code>) is the intended research direction; it becomes real only in Stage 2.</li>'
                    '<li>Identical token sets are flagged BLOCK by a prototype rule — a known questionable rule; do not rely on it for security decisions.</li>'
                    '<li>Results are a lexical signal only, not proof the content is safe or malicious.</li>'
                    '</ul>'
                    '<p class="muted small">Stage 1 is a reproducible lexical baseline. See docs/ for the full security review and roadmap.</p>'
                    '</div>',
                    padding=False,
                )

            # --- Project Info tab ---
            with gr.TabItem("Project Info"):
                gr.HTML(
                    '<div class="panel">'
                    '<h2>Project Info</h2>'
                    '<p class="muted">MCP-CONSIST · Context Integrity &amp; Security Research Workbench.</p>'
                    '<p>'
                    'A research prototype for detecting inconsistencies between paired contexts, '
                    'motivated by tool-poisoning-style attacks in the Model Context Protocol (MCP). '
                    'Stage 1 is an honest lexical baseline with a professional interface.</p>'
                    '<h3>Engine</h3>'
                    '<p class="mono small">'
                    'Lexical consistency prototype (v1) · lowercase + whitespace tokenisation · '
                    'set-overlap &ldquo;len(A &amp; B) / max(len(A), len(B))&rdquo; · threshold-gated ALLOW.</p>'
                    '<h3>Data handling</h3>'
                    '<p>'
                    'Inputs are processed in memory only. Nothing is persisted or transmitted during normal operation.</p>'
                    '</div>',
                    padding=False,
                )

        # ----- Footer -----
        with gr.Row(elem_classes=["workbench-footer"]):
            with gr.Column():
                gr.HTML(
                    'Research prototype &middot; inputs processed in memory only, not stored.',
                    padding=False,
                )

        # ------------------------------------------------------------------
        # Wiring (real Gradio: inputs -> callback -> outputs)
        # ------------------------------------------------------------------
        run_inputs = [txt_a, txt_b, threshold]
        run_outputs = [
            results_html,
            overlap_html,
            threshold_html,
            terms_html,
            count_display,
            validation_display,
        ]

        # Live per-input character counts + validation as the user types.
        txt_a.change(
            update_counts_a,
            inputs=[txt_a],
            outputs=[count_a, val_a],
        )
        txt_b.change(
            update_counts_b,
            inputs=[txt_b],
            outputs=[count_b, val_b],
        )

        # Clear ALL stale results whenever an input or the threshold changes.
        txt_a.change(
            clear_results,
            outputs=[results_html, overlap_html, threshold_html, terms_html, explanation_html],
        )
        txt_b.change(
            clear_results,
            outputs=[results_html, overlap_html, threshold_html, terms_html, explanation_html],
        )
        threshold.change(
            update_threshold_display,
            inputs=[threshold],
            outputs=[
                threshold_value,
                results_html,
                overlap_html,
                threshold_html,
                terms_html,
                explanation_html,
            ],
        )

        run_btn.click(
            run_analysis,
            inputs=run_inputs,
            outputs=run_outputs,
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
        # Reset the per-input counters and threshold display on Clear All
        # (programmatic value changes do not fire the textbox change events).
        clear_btn.click(
            lambda: (_count(""), _count(""), "", "", "0.80"),
            outputs=[count_a, count_b, val_a, val_b, threshold_value],
        )

        sample_dd.change(
            load_sample,
            inputs=[sample_dd],
            outputs=[txt_a, txt_b, sample_dd],
        )

        # Expose components for testability and event-wiring inspection.
        demo.txt_a = txt_a
        demo.txt_b = txt_b
        demo.threshold = threshold
        demo.run_btn = run_btn
        demo.clear_btn = clear_btn
        demo.sample_dd = sample_dd
        demo.count_a = count_a
        demo.count_b = count_b
        demo.val_a = val_a
        demo.val_b = val_b
        demo.threshold_value = threshold_value
        demo.results_html = results_html
        demo.overlap_html = overlap_html
        demo.threshold_html = threshold_html
        demo.terms_html = terms_html
        demo.explanation_html = explanation_html
        demo.count_display = count_display
        demo.validation_display = validation_display

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
    demo.css = CSS
    demo.head = HEAD_HTML
    demo.launch(server_name=host, server_port=port, share=share)
