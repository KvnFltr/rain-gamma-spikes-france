"""Reusable layout sections for the dashboard."""

from __future__ import annotations

from typing import Iterable

from dash import dcc, html
from dash.development.base_component import Component


_DEF_GRAPH_CONFIG = {"displaylogo": False}
_DEF_GRAPH_LAYOUT = {
    "template": "plotly_dark",
    "paper_bgcolor": "rgba(13, 23, 44, 0.0)",
    "plot_bgcolor": "rgba(13, 23, 44, 0.0)",
    "font": {"color": "#f8fbff"},
}


def build_graph_section(
    graph_id: str,
    *,
    title: str,
    description: str,
    controls: Iterable[Component] | None = None,
    footer: Component | None = None,
) -> html.Section:
    """Create a titled section wrapping a graph placeholder.

    Parameters
    ----------
    graph_id:
        Identifier for the embedded :class:`dcc.Graph` component.
    title:
        Section heading displayed above the graph.
    description:
        Short explanatory text displayed below the heading.
    controls:
        Optional collection of interactive components rendered above the graph
        (e.g. dropdown filters or sliders).
    footer:
        Optional component rendered below the graph, typically used for
        legends or contextual notes.
    """

    section_children: list[Component] = [
        html.H2(title, className="graph-section__title"),
        html.P(description, className="graph-section__description"),
    ]

    if controls:
        section_children.append(
            html.Div(list(controls), className="graph-section__controls"),
        )

    section_children.append(
        dcc.Loading(
            id=f"loading-{graph_id}",
            type="cube",
            children=dcc.Graph(
                id=graph_id,
                figure={"data": [], "layout": _DEF_GRAPH_LAYOUT},
                config=_DEF_GRAPH_CONFIG,
            ),
        )
    )

    if footer is not None:
        section_children.append(
            html.Div(footer, className="graph-section__footer"),
        )

    return html.Section(
        className="graph-section",
        children=section_children,
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
