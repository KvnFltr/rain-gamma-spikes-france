"""Simple navigation bar component."""

from __future__ import annotations

from dash import dcc, html
from dash.development.base_component import Component


def build_navbar(active_page: str = "home") -> html.Nav:
    """Render the dashboard navigation bar."""

    links: list[Component] = [
        dcc.Link(
            "Dashboard",
            href="/",
            className="nav-link nav-link--active" if active_page == "home" else "nav-link",
        ),
    ]
    return html.Nav(children=links, className="app-navbar")


__all__ = ["build_navbar"]
