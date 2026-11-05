"""UI wiring tests: real Gradio callbacks (inputs -> callback -> outputs).

Verifies the callbacks that back the buttons/dropdowns behave correctly and
that the demo Blocks is built. No JS-only mocks.
"""

import gradio as gr

from pipeline import MAX_INPUT_LENGTH
from demo.app import (
    clear_all, load_sample, run_analysis, SAMPLE_CHOICES, demo,
    update_counts_a, update_counts_b, clear_results, update_threshold_display,
)


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


# ---------------------------------------------------------------------------
# UI callback wiring
# ---------------------------------------------------------------------------

def _registered_callback_names():
    return {v.fn.__name__ for v in demo.fns.values()}


def test_all_ui_callbacks_registered():
    """Every control is backed by a real, registered Gradio callback."""
    expected = {
        "run_analysis", "clear_all", "load_sample",
        "update_counts_a", "update_counts_b",
        "clear_results", "update_threshold_display",
    }
    assert expected <= _registered_callback_names(), _registered_callback_names()


def test_run_analysis_wiring_signature():
    """run_analysis accepts the three wired inputs and returns six outputs."""
    import inspect
    sig = inspect.signature(run_analysis)
    assert list(sig.parameters) == ["text1", "text2", "threshold"]
    results = run_analysis("a b c", "b c d", 0.5)
    assert len(results) == 6


def test_clear_all_wiring_resets_every_output():
    """Clear All returns a fresh value for every one of its ten wired outputs."""
    outs = clear_all()
    assert len(outs) == 10
    t1, t2, thr = outs[0], outs[1], outs[2]
    assert t1 == "" and t2 == "" and thr == 0.8
    # Result outputs are cleared (no stale state from a previous analysis).
    assert outs[3] == ""   # results_html
    assert outs[4] == ""   # overlap_html
    assert outs[5] == ""   # threshold_html
    assert outs[6] == ""   # terms_html
    # Counter is reset to zero (intentionally non-empty), validation cleared.
    assert outs[7] == "0 / 20,000 chars &nbsp;|&nbsp; 0 / 20,000 chars"
    assert outs[8] == ""
    # Sample dropdown reset to the placeholder.
    assert outs[9] == "— Load a safe demo pair —"


def test_update_counts_work_independently():
    """Each textbox has its own independently-updating counter + validation."""
    c_a, v_a = update_counts_a("hello world")
    c_b, v_b = update_counts_b("")
    assert "11 / 20,000 chars" in c_a   # "hello world" is 11 characters
    assert "0 / 20,000 chars" in c_b
    assert v_a == ""                      # normal text: no validation error
    assert v_b == ""                      # truly empty: no whitespace error
    # Whitespace-only input produces a visible validation message.
    _, v_ws = update_counts_a("   \t\n ")
    assert v_ws != "" and "whitespace" in v_ws
    # Over-length input produces a visible validation message.
    _, v_long = update_counts_a("x" * (MAX_INPUT_LENGTH + 1))
    assert v_long != "" and "exceeds" in v_long


def test_clear_results_invalidates_all_result_outputs():
    """Changing an input clears ALL result outputs together (no stale state)."""
    outs = clear_results()
    assert len(outs) == 5
    assert all(o == "" for o in outs)


def test_threshold_change_updates_display_and_clears_stale():
    """Threshold change shows the new value and invalidates prior results."""
    display, *cleared = update_threshold_display(0.5)
    assert "0.50" in display
    assert all(o == "" for o in cleared)


def test_all_four_states_render():
    """run_analysis renders all four statuses with the correct badge classes."""
    cases = [
        ("a b c d e", "a b c d f", 0.8, "badge-allow"),
        ("a b c d e", "a b c d f", 0.99, "badge-warn"),
        ("hello world", "world hello", 0.5, "badge-block"),
        ("", "text", 0.5, "badge-error"),
    ]
    for t1, t2, thr, expected_badge in cases:
        results = run_analysis(t1, t2, thr)
        assert expected_badge in results[0], results[0]


def test_xss_all_vectors_rendered_inert():
    """No user-supplied markup executes, for any of the attack vectors."""
    for xss in (
        "<img src=x onerror=alert(1)>",
        "<script>alert(1)</script>",
        "<svg onload=alert(1)>",
    ):
        results = run_analysis(f"{xss} hi", f"{xss} ho", 0.5)
        joined = "".join(results)
        assert xss not in joined, joined
        assert "&lt;" in joined, joined
        # No complete tag may be reconstructed from the outputs.
        assert f"<{xss.split()[0][1:]}" not in joined


def test_no_traceback_in_user_visible_results():
    """Never expose raw Python tracebacks to the user."""
    results = run_analysis("valid text", "valid text", 0.5)
    joined = "".join(results)
    assert "Traceback" not in joined
    assert "line " not in joined


# ---------------------------------------------------------------------------
# Gradio component configuration
# ---------------------------------------------------------------------------

def test_wired_components_exist_in_blocks():
    """The components referenced by the callbacks are present in the Blocks."""
    for name in ("txt_a", "txt_b", "threshold", "run_btn", "clear_btn",
                 "sample_dd", "count_a", "count_b", "val_a", "val_b",
                 "threshold_value", "results_html", "overlap_html",
                 "threshold_html", "terms_html", "explanation_html",
                 "count_display", "validation_display"):
        assert hasattr(demo, name), f"demo missing component {name}"
