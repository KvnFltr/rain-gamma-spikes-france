"""Graph containers and related reusable layout helpers."""

from __future__ import annotations

from typing import Iterable

from dash import dcc, html
from dash.development.base_component import Component

_DEF_GRAPH_CONFIG = {"displaylogo": False}
_DEF_GRAPH_LAYOUT = {
    "template": "simple_white",
    "paper_bgcolor": "rgba(0, 0, 0, 0)",
    "plot_bgcolor": "rgba(0, 0, 0, 0)",
    "font": {"color": "#0f172a"},
}


def build_graph_section(
    graph_id: str,
    *,
    title: str,
    description: str,
    controls: Iterable[Component] | None = None,
    footer: Component | None = None,
) -> html.Section:
    """Create a titled section wrapping a :class:`dcc.Graph` placeholder."""

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


__all__ = ["build_graph_section"]
