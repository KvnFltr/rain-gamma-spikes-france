"""Placeholder for a simple example page to respect the agreed project structure."""

from __future__ import annotations

from dash import html


def layout() -> html.Div:
    """Return a minimal layout showcasing the simple page stub."""

    return html.Div(
        className="simple-page",
        children=[
            html.H2("Simple Page"),
            html.P(
                "This page is intentionally minimal and reserved for future content.",
                className="simple-page__description",
            ),
        ],
    )


__all__ = ["layout"]
