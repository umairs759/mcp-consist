"""HTML helpers for the MCP-CONSIST workbench UI.

Every user-derived string is passed through ``html.escape`` before being
interpolated, so rendered output is always inert (no XSS). No inline event
handlers are emitted by these helpers.
"""

from __future__ import annotations

import html

BADGE_CLASSES = {
    "ALLOW": "badge badge-allow",
    "WARN": "badge badge-warn",
    "BLOCK": "badge badge-block",
    "ERROR": "badge badge-error",
}

STATUS_TITLES = {
    "ALLOW": "ALLOW",
    "WARN": "WARN",
    "BLOCK": "BLOCK",
    "ERROR": "ERROR",
}


def badge(status: str) -> str:
    """Render a status badge span. ``status`` must be one of ALLOW/WARN/BLOCK/ERROR."""
    cls = BADGE_CLASSES.get(status, "badge badge--error")
    label = STATUS_TITLES.get(status, "ERROR")
    return f'<span class="{cls}">{html.escape(label)}</span>'


def chips(items) -> str:
    """Render a list of term chips from an iterable of strings."""
    if not items:
        return '<em style="color:#5B6572;font-size:12px;">(none)</em>'
    parts = []
    for item in items:
        parts.append(
            f'<span class="term-chip">{html.escape(str(item))}</span>'
        )
    return "".join(parts)


def meta_row(label: str, value) -> str:
    """Render a single metadata row."""
    return (
        f'<div class="meta-item">'
        f'<span style="color:#8B95A1;">{html.escape(str(label))}</span>: '
        f'<b>{html.escape(str(value))}</b>'
        f"</div>"
    )


def explanation_box(text: str) -> str:
    return f'<div class="explanation-box">{html.escape(str(text))}</div>'


def error_box(text: str) -> str:
    return f'<div class="error-box">{html.escape(str(text))}</div>'


def esc(text) -> str:
    """Escape a user-derived string for safe HTML insertion."""
    return html.escape(str(text))
