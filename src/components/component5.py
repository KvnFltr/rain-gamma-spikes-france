"""
Graph: Rainfall vs Radioactivity (Bq/kg sec).
"""

from __future__ import annotations

from dash import dcc, html

from .component2 import _DEF_GRAPH_CONFIG, _DEF_GRAPH_LAYOUT


def build_rain_vs_radio_section() -> html.Section:
    """Section contenant le scatter pluie vs radioactivité."""

    return html.Section(
        className="graph-section",
        children=[
            html.H2("Rainfall vs Radioactivity", className="graph-section__title"),
            html.P(
                "Scatter plot comparing rainfall amounts with radioactivity levels "
                "(filtered to Bq/kg dry matter).",
                className="graph-section__description",
            ),
            dcc.Loading(
                id="loading-rain-radio",
                type="cube",
                children=dcc.Graph(
                    id="rain-radio-graph",
                    figure={"data": [], "layout": _DEF_GRAPH_LAYOUT},
                    config=_DEF_GRAPH_CONFIG,
                ),
            ),
        ],
    )


__all__ = ["build_rain_vs_radio_section"]
