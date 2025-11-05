"""Application factory for the Dash dashboard."""

from __future__ import annotations

from dash import Dash, html

from .pages import home


def create_app() -> Dash:
    """Instantiate and configure the Dash application."""

    app = Dash(
        __name__,
        suppress_callback_exceptions=True,
        title="Rain & Dust Spikes",
    )
    app.layout = lambda: html.Div(  # Late binding to always return fresh layout
        children=[
            home.layout(),
        ],
        className="app-container",
    )
    home.register_callbacks(app)
    return app


__all__ = ["create_app"]
