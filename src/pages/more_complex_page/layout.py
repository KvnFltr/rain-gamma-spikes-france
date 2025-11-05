"""Demonstration layout for a more sophisticated dashboard page."""

from __future__ import annotations

from dash import html

from ...components import build_footer, build_header, build_navbar
from .page_specific_component import build_highlight


def layout() -> html.Div:
    """Return the layout for the example complex page."""

    return html.Div(
        className="complex-page",
        children=[
            build_header("Advanced Analytics", "Modular page example"),
            build_navbar(),
            html.Main(
                className="complex-page__content",
                children=[
                    build_highlight(
                        title="Reserved section",
                        description=(
                            "This page demonstrates how additional complex layouts can be "
                            "mounted while preserving the agreed architecture."
                        ),
                    )
                ],
            ),
            build_footer(),
        ],
    )


__all__ = ["layout"]
