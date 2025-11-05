"""Metric-focused building blocks used across dashboard pages."""

from __future__ import annotations

from dash import html
from dash.development.base_component import Component


def build_metrics_row(children: list[Component]) -> html.Div:
    """Arrange metric/statistic cards within a responsive row."""

    return html.Div(children=children, className="metrics-row")


def build_stat_card(title: str, value: str, *, identifier: str) -> html.Div:
    """Return a placeholder card for a key performance indicator."""

    return html.Div(
        className="stat-card",
        id=identifier,
        children=[
            html.Span(title, className="stat-card__title"),
            html.Strong(value, className="stat-card__value"),
        ],
    )


__all__ = ["build_metrics_row", "build_stat_card"]
