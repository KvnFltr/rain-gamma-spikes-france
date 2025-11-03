"""Reusable layout sections for the dashboard."""

from __future__ import annotations

from dash import dcc, html
from dash.development.base_component import Component


_DEF_GRAPH_CONFIG = {"displaylogo": False}
_DEF_GRAPH_LAYOUT = {"template": "plotly_white", "paper_bgcolor": "#ffffff"}


def build_graph_section(
    graph_id: str,
    *,
    title: str,
    description: str,
) -> html.Section:
    """Create a titled section wrapping a graph placeholder."""

    return html.Section(
        className="graph-section",
        children=[
            html.H2(title, className="graph-section__title"),
            html.P(description, className="graph-section__description"),
            dcc.Loading(
                id=f"loading-{graph_id}",
                type="cube",
                children=dcc.Graph(
                    id=graph_id,
                    figure={"data": [], "layout": _DEF_GRAPH_LAYOUT},
                    config=_DEF_GRAPH_CONFIG,
                ),
            ),
        ],
    )


def build_metrics_row(children: list[Component]) -> html.Div:
    """Arrange metric/statistics cards in a responsive row."""

    return html.Div(children=children, className="metrics-row")


def build_stat_card(title: str, value: str, *, identifier: str) -> html.Div:
    """Return a card placeholder for key metrics."""

    return html.Div(
        className="stat-card",
        id=identifier,
        children=[
            html.Span(title, className="stat-card__title"),
            html.Strong(value, className="stat-card__value"),
        ],
    )


__all__ = ["build_graph_section", "build_metrics_row", "build_stat_card"]
