"""Dash application initialization."""

from dash import Dash
from . import layout, callbacks
from pathlib import Path
assets_path = Path(__file__).resolve().parents[1] / "assets"

def create_app() -> Dash:
    """Create and configure the Dash application."""
    app = Dash(
        __name__,
        suppress_callback_exceptions=True,
        assets_folder=str(assets_path),
    )
    app.layout = layout.build_layout()
    callbacks.register_all_callbacks(app)

    return app
