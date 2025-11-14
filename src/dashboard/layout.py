"""Dashboard layout construction."""
from __future__ import annotations
import pandas as pd
from dash import dcc, html
from .utils import serialize_dataset, get_dataset
from ..components import (
    build_header,
    build_navbar,
    build_footer,
    build_metrics_row,
    build_stat_card,
    build_graph_section,
    build_rain_vs_radio_section,
)
from config import RADION_COLUMN, MEDIUM_COLUMN, DATE_COLUMN

from typing import Any


def _build_dropdown_options(dataset: pd.DataFrame | None, column: str) -> list[dict[str, str]]:
    """Return dropdown options derived from a dataframe column."""
    if dataset is None or column not in dataset:
        return []

    series = dataset[column]
    if series.isna().all():
        return []

    cleaned = (
        pd.Series(series.dropna().unique())
        .astype(str)
        .str.strip()
    )
    cleaned = cleaned[cleaned != ""]
    cleaned = cleaned[~cleaned.str.lower().isin({"nan", "none"})]
    values = cleaned.sort_values().tolist()
    return [{"label": value, "value": value} for value in values]


def _build_date_slider_config(dataset: pd.DataFrame | None) -> dict[str, Any] | None:
    """Compute configuration for the date range slider."""
    if dataset is None or DATE_COLUMN not in dataset or dataset.empty:
        return None

    min_date = dataset[DATE_COLUMN].min()
    max_date = dataset[DATE_COLUMN].max()
    if pd.isna(min_date) or pd.isna(max_date):
        return None

    min_value = int(min_date.timestamp())
    max_value = int(max_date.timestamp())
    if min_value == max_value:
        max_value = min_value + 86_400  # ensure slider has a range of at least one day

    year_marks = sorted(dataset[DATE_COLUMN].dt.year.unique())
    marks = {
        int(pd.Timestamp(year=year, month=1, day=1).timestamp()): str(year)
        for year in year_marks
    }
    if not marks:
        marks = {
            min_value: min_date.strftime("%Y-%m-%d"),
            max_value: max_date.strftime("%Y-%m-%d"),
        }

    return {
        "min": min_value,
        "max": max_value,
        "value": [min_value, max_value],
        "marks": marks,
    }


def _build_histogram_controls(
    radionuclide_options: list[dict[str, str]],
    medium_options: list[dict[str, str]],
    slider_config: dict[str, Any] | None,
) -> list:
    """Build control elements for the histogram section."""
    slider_defaults = slider_config or {"min": 0, "max": 0, "value": [0, 0], "marks": {}}

    return [
        html.Div(
            [
                html.Label("Radionuclide", className="control-label", htmlFor="radionuclide-filter"),
                dcc.Dropdown(
                    id="radionuclide-filter",
                    options=radionuclide_options,
                    value=[option["value"] for option in radionuclide_options] if radionuclide_options else None,
                    multi=True,
                    placeholder="Select radionuclides",
                    clearable=False,
                    persistence=True,
                    persistence_type="session",
                    className="control-input",
                    disabled=not radionuclide_options,
                ),
            ],
            className="control-group",
        ),
        html.Div(
            [
                html.Label("Measurement environment", className="control-label", htmlFor="medium-filter"),
                dcc.Dropdown(
                    id="medium-filter",
                    options=medium_options,
                    value=[option["value"] for option in medium_options] if medium_options else None,
                    multi=True,
                    placeholder="Select media",
                    clearable=False,
                    persistence=True,
                    persistence_type="session",
                    className="control-input",
                    disabled=not medium_options,
                ),
            ],
            className="control-group",
        ),
        html.Div(
            [
                html.Label("Sampling period", className="control-label", htmlFor="date-range-slider"),
                dcc.RangeSlider(
                    id="date-range-slider",
                    allowCross=False,
                    tooltip={"placement": "bottom", "always_visible": False},
                    updatemode="mouseup",
                    step=86_400,
                    disabled=slider_config is None,
                    className="control-input control-input--slider",
                    **slider_defaults,
                ),
            ],
            className="control-group control-group--slider",
        ),
        html.Div(
            [
                html.Label("Scale", className="control-label", htmlFor="hist-scale"),
                dcc.RadioItems(
                    id="hist-scale",
                    options=[
                        {"label": "Count", "value": "count"},
                        {"label": "Density", "value": "density"},
                    ],
                    value="count",
                    inline=True,
                    inputClassName="control-radio-input",
                    labelClassName="control-radio-label",
                ),
            ],
            className="control-group",
        ),
    ]


def _build_metrics_section(dataset: pd.DataFrame | None) -> html.Div:
    """Build the metrics row with stat cards."""
    return build_metrics_row(
        [
            build_stat_card("Monitoring sites", "—", identifier="stations-count"),
            build_stat_card("Measurements analysed", "—", identifier="measurements-count"),
            build_stat_card("Latest measurement", "—", identifier="last-update"),
        ]
    )


def _build_histogram_section(
    radionuclide_options: list[dict[str, str]],
    medium_options: list[dict[str, str]],
    slider_config: dict[str, Any] | None,
) -> html.Div:
    """Build the histogram section with controls."""
    histogram_controls = _build_histogram_controls(
        radionuclide_options,
        medium_options,
        slider_config,
    )

    return build_graph_section(
        "radiation-histogram",
        title="Gamma dose distribution",
        description=(
            "Explore how gamma dose results are distributed and compare collection media "
            "or radionuclides using the interactive controls."
        ),
        controls=histogram_controls,
        footer=html.Span("Unit: —", id="histogram-unit-legend", className="graph-section__legend-text"),
    )


def _build_map_section() -> html.Div:
    """Build the geographic map section."""
    return build_graph_section(
        "radiation-map",
        title="Geolocated monitoring stations",
        description=(
            "An interactive map highlighting radiation monitoring stations and associated weather observations."
        ),
    )


def _build_time_series_section() -> html.Div:
    """Build the time series section."""
    return build_graph_section(
        "rainfall-timeseries",
        title="Precipitation and gamma dose dynamics",
        description=(
            "A combined time-series view to correlate rainfall intensity with gamma dose variations over time."
        ),
    )


def _build_commune_correlation_section() -> html.Div:
    """Build the commune correlation map section."""
    return build_graph_section(
        "commune-corr-map",
        title="Corrélation pluie ↔ dose gamma (par commune)",
        description=(
            "Coefficient de corrélation de Pearson (r) entre la pluie et la dose gamma, "
            "calculé à partir des mesures disponibles par commune."
        ),
    )


def _build_commune_mean_section() -> html.Div:
    """Build the commune mean dose map section."""
    return build_graph_section(
        "commune-mean-map",
        title="Dose gamma moyenne (par commune)",
        description=("Moyenne des résultats de dose gamma, agrégée au niveau communal."),
    )


def _build_rain_vs_radio_section() -> html.Div:
    """Build the rain vs radioactivity scatter section."""
    return build_rain_vs_radio_section()


def build_layout() -> html.Div:
    """Return the main dashboard layout."""
    # Charger les données et préparer les options
    dataset = get_dataset()
    radionuclide_options = _build_dropdown_options(dataset, RADION_COLUMN)
    medium_options = _build_dropdown_options(dataset, MEDIUM_COLUMN)
    slider_config = _build_date_slider_config(dataset)
    store_payload = serialize_dataset(dataset)

    # Construire les sections
    metrics = _build_metrics_section(dataset)
    histogram_section = _build_histogram_section(
        radionuclide_options,
        medium_options,
        slider_config,
    )
    map_section = _build_map_section()
    time_series_section = _build_time_series_section()
    commune_corr_section = _build_commune_correlation_section()
    commune_mean_section = _build_commune_mean_section()
    rain_vs_radio_section = _build_rain_vs_radio_section()

    # Assembler le layout complet
    return html.Div(
        className="home-page",
        children=[
            build_header(
                "Rain & Dust Spikes",
                "Does the gamma dose rise after rainfall?",
            ),
            build_navbar(),
            html.Main(
                className="home-page__content",
                children=[
                    metrics,
                    histogram_section,
                    map_section,
                    commune_corr_section,
                    commune_mean_section,
                    time_series_section,
                    rain_vs_radio_section,
                    dcc.Store(id="radiation-data-store", data=store_payload, storage_type="memory"),
                ],
            ),
            build_footer(),
        ],
    )


__all__ = ["build_layout"]