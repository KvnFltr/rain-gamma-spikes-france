"""Custom elements showcased on the complex example page."""

from __future__ import annotations

from dash import html


def build_highlight(*, title: str, description: str) -> html.Section:
    """Render a highlighted informational block."""

    return html.Section(
        className="complex-page__highlight",
        children=[
            html.H3(title, className="complex-page__highlight-title"),
            html.P(description, className="complex-page__highlight-description"),
        ],
    )


__all__ = ["build_highlight"]
