"""UI wiring tests: real Gradio callbacks (inputs -> callback -> outputs).

Verifies the callbacks that back the buttons/dropdowns behave correctly and
that the demo Blocks is built. No JS-only mocks.
"""

import gradio as gr

from demo.app import clear_all, load_sample, run_analysis, SAMPLE_CHOICES, demo


def test_demo_is_blocks():
    assert isinstance(demo, gr.Blocks)


def test_clear_all_resets_inputs_results_threshold():
    """Clear All resets inputs, results and threshold to defaults."""
    (
        t1, t2, thr,
        results_html, overlap_html, threshold_html, terms_html,
        count_html, validation_html, sample_dd,
    ) = clear_all()
    assert t1 == ""
    assert t2 == ""
    assert thr == 0.8
    assert results_html == ""
    assert overlap_html == ""
    assert threshold_html == ""
    assert terms_html == ""
    assert count_html == "0 / 20,000 chars &nbsp;|&nbsp; 0 / 20,000 chars"
    assert validation_html == ""
    assert sample_dd == "— Load a safe demo pair —"


def test_load_sample_returns_safe_pair():
    """Load sample puts a labelled safe demo pair into the textboxes."""
    label = SAMPLE_CHOICES[1]  # first real sample
    t1, t2, _ = load_sample(label)
    assert t1 and t2
    assert isinstance(t1, str) and isinstance(t2, str)
    # Non-sample choice returns empty unchanged.
    t1, t2, _ = load_sample("— Load a safe demo pair —")
    assert t1 == "" and t2 == ""


def test_run_analysis_returns_all_outputs():
    """run_analysis returns a value for every wired output (6 values)."""
    results = run_analysis("Fetch weather for Lahore", "Fetch weather for Lahore", 0.8)
    assert len(results) == 6
    results_html, overlap_html, threshold_html, terms_html, count_html, validation_html = results
    assert "badge" in results_html
    assert "20,000" in count_html


def test_run_analysis_warn_below_threshold():
    results = run_analysis("a b c d e", "a b c d f", 0.99)
    results_html = results[0]
    assert "badge-warn" in results_html, results_html
    assert "badge-allow" not in results_html


def test_run_analysis_error_invalid_threshold():
    results = run_analysis("a b", "a b", 1.5)
    results_html = results[0]
    assert "badge-error" in results_html, results_html


def test_run_analysis_xss_rendered_inert():
    """User-derived HTML/JS in terms must be escaped, never executed."""
    xss = "<img src=x onerror=alert(1)>"
    results = run_analysis(f"{xss} hello", f"{xss} world", 0.5)
    results_html, overlap_html, threshold_html, terms_html, count_html, validation_html = results
    all_outputs = "".join(results)
    # No raw unescaped tag may appear anywhere (that would be executable).
    assert "<img" not in all_outputs
    # The matched XSS token is rendered via chips(), so it is escaped, not stripped.
    assert "&lt;img" in terms_html
    # The tag close is also escaped, so no complete tag is formed.
    assert "&gt;" in terms_html
