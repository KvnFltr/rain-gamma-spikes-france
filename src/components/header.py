"""Reusable page header component."""

from __future__ import annotations

from dash import html
from dash.development.base_component import Component


def build_header(title: str, subtitle: str | None = None) -> html.Header:
    """Return a semantic header for dashboard pages."""

    children: list[Component] = [
        html.H1(title, className="app-title"),
    ]
    if subtitle:
        children.append(html.P(subtitle, className="app-subtitle"))
    return html.Header(children=children, className="app-header")


## New function to build a global loader when data is loading
def build_loader() -> html.Div:
    """Global spinner overlay during data loading."""
    return html.Div(
        className="global-loader",
        children=[
            html.Div(className="spinner"),
            html.Span("Chargement des données...", className="loader-text"),
        ],
    )  


__all__ = ["build_header", "build_loader"]
