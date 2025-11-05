"""Specialised histogram builders for gamma dose visualisations."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable

import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from dash import dcc, html
from dash.development.base_component import Component

_DRY_COLOR = "#e9c46a"
_RAINY_COLOR = "#2a9d8f"


@dataclass(slots=True)
class GammaHistogramConfig:
    """Configuration used when building gamma dose histograms."""

    gamma_column: str
    rainfall_column: str
    rainfall_threshold_mm: float = 1.0
    gamma_unit: str | None = None
    title: str = "Daily gamma dose: rainy vs dry days"
    subtitle: str | None = "Example grouping uses a 1 mm rainfall threshold."


def _freedman_diaconis_bins(values: pd.Series, *, minimum: int = 8, maximum: int = 80) -> int:
    """Return a sensible number of histogram bins for the provided values."""

    cleaned = pd.Series(values).dropna()
    if cleaned.empty:
        return minimum

    array = cleaned.to_numpy(dtype=float)
    array = array[np.isfinite(array)]
    if array.size <= 1:
        return minimum

    q1, q3 = np.percentile(array, [25, 75])
    iqr = q3 - q1
    if iqr <= 0:
        heuristic = int(round(np.sqrt(array.size)))
        return max(minimum, min(maximum, heuristic))

    bin_width = 2 * iqr / np.cbrt(array.size)
    if bin_width <= 0:
        heuristic = int(round(np.sqrt(array.size)))
        return max(minimum, min(maximum, heuristic))

    span = array.max() - array.min()
    if span == 0:
        return minimum

    bins = int(np.ceil(span / bin_width))
    return max(minimum, min(maximum, bins))


def _infer_gamma_unit(column: str, explicit_unit: str | None) -> str:
    """Return the gamma dose unit using heuristics derived from metadata."""

    if explicit_unit:
        return explicit_unit

    if "(" in column and ")" in column:
        between_parentheses = column.split("(", 1)[1].split(")", 1)[0]
        inferred = between_parentheses.strip()
        if inferred:
            return inferred

    return "nSv/h"


def _format_threshold(threshold: float) -> str:
    """Human readable rainfall threshold used for legend text."""

    if threshold.is_integer():
        return f"{threshold:.0f} mm"
    return f"{threshold:g} mm"


def build_gamma_histogram_figure(
    dataset: pd.DataFrame,
    *,
    config: GammaHistogramConfig,
) -> go.Figure:
    """Create a Plotly histogram comparing rainy and dry day gamma doses."""

    if dataset.empty:
        raise ValueError("Dataset must contain observations to build the histogram.")

    required_columns = {config.gamma_column, config.rainfall_column}
    if not required_columns.issubset(dataset.columns):
        missing = ", ".join(sorted(required_columns - set(dataset.columns)))
        raise KeyError(f"Dataset is missing required columns: {missing}")

    working = dataset[[config.gamma_column, config.rainfall_column]].copy()
    working[config.gamma_column] = pd.to_numeric(working[config.gamma_column], errors="coerce")
    working[config.rainfall_column] = pd.to_numeric(working[config.rainfall_column], errors="coerce")
    working = working.dropna()

    if working.empty:
        raise ValueError("Dataset does not contain numeric gamma dose and rainfall values.")

    unit = _infer_gamma_unit(config.gamma_column, config.gamma_unit)

    threshold = float(config.rainfall_threshold_mm)
    threshold_text = _format_threshold(threshold)
    rainy_label = f"Rainy day (≥ {threshold_text})"
    dry_label = f"Dry day (< {threshold_text})"

    working["rain_category"] = np.where(
        working[config.rainfall_column] >= threshold,
        rainy_label,
        dry_label,
    )

    bin_count = _freedman_diaconis_bins(working[config.gamma_column])

    histogram = px.histogram(
        working,
        x=config.gamma_column,
        color="rain_category",
        nbins=bin_count,
        barmode="overlay",
        opacity=0.82,
        color_discrete_map={
            dry_label: _DRY_COLOR,
            rainy_label: _RAINY_COLOR,
        },
        labels={
            config.gamma_column: f"Daily mean gamma dose ({unit})",
            "rain_category": "Day type",
        },
    )

    histogram.update_traces(
        hovertemplate=(
            "Day type: %{fullData.name}<br>"
            "Gamma dose: %{x:.1f} "
            f"{unit}<br>Days: %{y}<extra></extra>"
        ),
        marker_line_color="rgba(13, 23, 44, 0.35)",
        marker_line_width=0.8,
    )

    histogram.update_layout(
        title=dict(text=config.title, x=0.5, xanchor="center"),
        bargap=0.04,
        legend=dict(
            title="Day type",
            orientation="h",
            yanchor="bottom",
            y=1.02,
            x=0,
            bgcolor="rgba(255, 255, 255, 0.7)",
            bordercolor="rgba(15, 23, 42, 0.15)",
            borderwidth=1,
        ),
        template="plotly_white",
        paper_bgcolor="rgba(0, 0, 0, 0)",
        plot_bgcolor="rgba(0, 0, 0, 0)",
        margin=dict(l=60, r=40, t=70, b=70),
        height=420,
    )

    histogram.update_xaxes(
        title=f"Daily mean gamma dose ({unit})",
        gridcolor="rgba(148, 163, 184, 0.25)",
        zerolinecolor="rgba(148, 163, 184, 0.35)",
    )
    histogram.update_yaxes(
        title="Number of days",
        gridcolor="rgba(148, 163, 184, 0.2)",
        zerolinecolor="rgba(148, 163, 184, 0.3)",
    )

    if config.subtitle:
        histogram.add_annotation(
            text=config.subtitle,
            xref="paper",
            yref="paper",
            x=0.0,
            y=1.08,
            showarrow=False,
            font=dict(size=12, color="#475569"),
        )

    return histogram


def build_gamma_histogram_graph(
    dataset: pd.DataFrame,
    *,
    config: GammaHistogramConfig,
    graph_id: str = "gamma-histogram",
    graph_class: str | None = None,
    extra_controls: Iterable[Component] | None = None,
) -> Component:
    """Return a :class:`dcc.Graph` configured with the gamma histogram figure."""

    figure = build_gamma_histogram_figure(dataset, config=config)
    graph_kwargs: dict[str, object] = {"id": graph_id, "figure": figure}
    if graph_class:
        graph_kwargs["className"] = graph_class

    graph_component: Component = dcc.Graph(**graph_kwargs)

    if extra_controls:
        return html.Div(
            className="gamma-histogram",
            children=[html.Div(list(extra_controls), className="gamma-histogram__controls"), graph_component],
        )

    return graph_component


__all__ = [
    "GammaHistogramConfig",
    "build_gamma_histogram_figure",
    "build_gamma_histogram_graph",
]
