"""HTML endpoint contract for ``demo.app.run_check``.

Standardises on ``<span class="badge badge-allow|warn|block|error">…</span>``.
Every badge type must render; no inline ``<div style=…>`` badges.
"""

from demo.app import run_check


def test_badge_uses_span_class_not_div_style():
    result = run_check("text1", "text2", 0.5)
    assert result.startswith("<span class="), result
    assert "badge" in result
    assert "<div style=" not in result
    assert result.endswith("</span>")


def test_badge_allow():
    assert 'class="badge badge-allow"' in run_check(
        "The cat sat on the mat", "The cat is on the mat", 0.5
    )


def test_badge_warn():
    result = run_check("a b c d e", "a b c d f", 0.9)
    assert "badge-warn" in result, result


def test_badge_block():
    assert 'class="badge badge-block"' in run_check("hello", "hello", 0.5)


def test_badge_error():
    assert 'class="badge badge-error"' in run_check("", "text", 0.5)
