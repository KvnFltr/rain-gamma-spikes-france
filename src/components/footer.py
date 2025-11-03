"""Footer component shared by dashboard pages."""

from __future__ import annotations

from dash import html


def build_footer() -> html.Footer:
    """Return a semantic footer with project metadata."""

    return html.Footer(
        className="app-footer",
        children=[
            html.Small(
                "© Rain & Dust Spikes — Dashboard prototype based on open data sources",
                className="footer-text",
            ),
        ],
    )


__all__ = ["build_footer"]
