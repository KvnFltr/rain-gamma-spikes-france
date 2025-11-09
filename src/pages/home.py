"""Layout and interactive callbacks for the dashboard home page."""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path
from typing import Any, Iterable

import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from dash import Dash, Input, Output, dcc, html
from dash.development.base_component import Component

import json
import unicodedata
from pathlib import Path

from ..components import (
    build_footer,
    build_graph_section,
    build_header,
    build_metrics_row,
    build_navbar,
    build_stat_card,
    build_rain_vs_radio_section,
)

DATA_PATH = Path("data/cleaned/cleaneddata.csv")
DATA_PATH = Path("data/cleaned/data.csv")

GEOJSON_PATH = Path("data/geodata/communes.geojson")

DATE_COLUMN = "Date start sampling radioactivity"
RESULT_COLUMN = "Result radioactivity"
UNIT_COLUMN = "Unit radioactivity"
RADION_COLUMN = "Radionuclide"
MEDIUM_COLUMN = "Measurement environment"
LAT_COLUMN = "Latitude"
LON_COLUMN = "Longitude"
MUNICIPALITY_COLUMN = "Municipality name"

def _norm_name(s: str) -> str:
    """Normalise un nom de commune : accents/majuscules/tirets/espaces."""
    if not isinstance(s, str):
        return ""
    s = unicodedata.normalize("NFKD", s).encode("ascii", "ignore").decode("ascii")
    return (
        s.lower()
         .replace("-", " ")
         .replace("’", "'")
         .replace("`", "'")
         .strip()
    )

@lru_cache(maxsize=1)
def _load_communes_geojson() -> dict:
    """Charge le GeoJSON des communes et ajoute 'properties.nom_key' normalisé pour la jointure."""
    with open(GEOJSON_PATH, "r", encoding="utf-8") as f:
        gj = json.load(f)
    for feat in gj.get("features", []):
        props = feat.setdefault("properties", {})
        nom = props.get("nom", "")
        props["nom_key"] = _norm_name(nom)
    return gj

_MEDIUM_LABELS = {
    "Sol": "Soil",
    "sol": "Soil",
    "Eau": "Water",
    "eau": "Water",
    "AIR": "Air",
    "Air": "Air",
    "AIR AMBIANT": "Air",
}

_MEDIUM_COLOR_MAP = {
    "Water": "#5fa8d3",
    "Soil": "#f4a261",
    "Air": "#94c973",
}

@lru_cache(maxsize=1)
def _cached_dataset() -> pd.DataFrame:
    """Load and cache the cleaned dataset used by the dashboard."""

    if not DATA_PATH.exists():
        raise FileNotFoundError(DATA_PATH)

    raw_df = pd.read_csv(DATA_PATH, sep=";", low_memory=False)
    dataset = raw_df.copy()

    if RESULT_COLUMN in dataset:
        dataset[RESULT_COLUMN] = pd.to_numeric(dataset[RESULT_COLUMN], errors="coerce")
        dataset = dataset.dropna(subset=[RESULT_COLUMN])

    if DATE_COLUMN in dataset:
        dataset[DATE_COLUMN] = pd.to_datetime(dataset[DATE_COLUMN], errors="coerce", utc=True)
        dataset = dataset.dropna(subset=[DATE_COLUMN])
        dataset[DATE_COLUMN] = dataset[DATE_COLUMN].dt.tz_localize(None)
        dataset = dataset.sort_values(DATE_COLUMN)

    if MEDIUM_COLUMN in dataset:
        dataset[MEDIUM_COLUMN] = dataset[MEDIUM_COLUMN].replace(_MEDIUM_LABELS)

    return dataset.reset_index(drop=True)


def _get_dataset() -> pd.DataFrame | None:
    """Return a copy of the cached dataset, or ``None`` if unavailable."""

    try:
        return _cached_dataset().copy()
    except (FileNotFoundError, pd.errors.EmptyDataError, pd.errors.ParserError):
        return None


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


def _normalise_selection(selection: Iterable[str] | str | None) -> list[str]:
    """Return a list of selected values regardless of Dash payload type."""

    if selection is None:
        return []
    if isinstance(selection, str):
        return [selection]
    return list(selection)


def _stat_card_children(title: str, value: str) -> list[Component]:
    """Return the children used within a statistic card."""

    return [
        html.Span(title, className="stat-card__title"),
        html.Strong(value, className="stat-card__value"),
    ]


def _serialize_dataset(dataset: pd.DataFrame | None) -> str | None:
    """Serialize the dataframe to JSON for storage in :class:`dcc.Store`."""

    if dataset is None or dataset.empty:
        return None
    return dataset.to_json(date_format="iso", orient="records")


def _deserialize_dataset(payload: str | None) -> pd.DataFrame:
    """Deserialize dataset JSON stored in :class:`dcc.Store`."""

    if not payload:
        return pd.DataFrame()
    dataframe = pd.read_json(payload, orient="records")
    if DATE_COLUMN in dataframe:
        dataframe[DATE_COLUMN] = pd.to_datetime(dataframe[DATE_COLUMN], errors="coerce")
        dataframe = dataframe.dropna(subset=[DATE_COLUMN])
    if RESULT_COLUMN in dataframe:
        dataframe[RESULT_COLUMN] = pd.to_numeric(dataframe[RESULT_COLUMN], errors="coerce")
        dataframe = dataframe.dropna(subset=[RESULT_COLUMN])
    if MEDIUM_COLUMN in dataframe:
        dataframe[MEDIUM_COLUMN] = dataframe[MEDIUM_COLUMN].replace(_MEDIUM_LABELS)
    return dataframe


def _compute_bin_count(series: pd.Series) -> int:
    """Determine an appropriate number of histogram bins."""

    data = pd.Series(series.dropna())
    if data.empty:
        return 10

    values = data.to_numpy(dtype=float)
    values = values[np.isfinite(values)]
    if values.size <= 1:
        return 5

    q25, q75 = np.percentile(values, [25, 75])
    iqr = q75 - q25
    if iqr <= 0:
        return int(min(50, max(5, round(np.sqrt(values.size)))))

    bin_width = 2 * iqr / np.cbrt(values.size)
    if bin_width <= 0:
        return int(min(50, max(5, round(np.sqrt(values.size)))))

    data_range = values.max() - values.min()
    if data_range == 0:
        return 5

    bins = int(np.ceil(data_range / bin_width))
    return int(min(max(bins, 6), 60))


def _format_integer(value: int | float | None) -> str:
    """Format integers with thousands separators for display."""

    if value is None or pd.isna(value):
        return "—"
    return f"{int(value):,}"


def _format_date(value: pd.Timestamp | None) -> str:
    """Return a nicely formatted date string."""

    if value is None or pd.isna(value):
        return "—"
    return value.strftime("%b %d, %Y")


def _empty_histogram_figure(message: str) -> go.Figure:
    """Return a placeholder histogram figure with an informative message."""

    fig = go.Figure()
    fig.update_layout(
        template="simple_white",
        paper_bgcolor="rgba(0, 0, 0, 0)",
        plot_bgcolor="rgba(0, 0, 0, 0)",
        height=420,
        margin=dict(l=20, r=20, t=40, b=60),
        xaxis_title="Gamma dose result (Bq/kg or Bq/L)",
        yaxis_title="Number of samples",
        font=dict(color="#0f172a"),
        showlegend=False,
    )
    fig.update_xaxes(gridcolor="#d7dde8")
    fig.update_yaxes(gridcolor="#d7dde8")

    fig.update_layout(
        template="plotly_dark",
        paper_bgcolor="rgba(13, 23, 44, 0.0)",
        plot_bgcolor="rgba(13, 23, 44, 0.0)",
        height=420,
        margin=dict(l=20, r=20, t=40, b=60),
        xaxis_title="Gamma dose result (Bq/kg or Bq/L)",
        yaxis_title="Frequency",
        font=dict(color="#f8fbff"),
        showlegend=False,
    )

    fig.add_annotation(
    text=message,
    x=0.5,
    y=0.5,
    xref="paper",
    yref="paper",
    showarrow=False,
    font=dict(size=16, color="#a0b4d0"),
    )
    return fig



def layout() -> html.Div:
    """Return the main dashboard layout."""

    dataset = _get_dataset()
    radionuclide_options = _build_dropdown_options(dataset, RADION_COLUMN)
    medium_options = _build_dropdown_options(dataset, MEDIUM_COLUMN)
    slider_config = _build_date_slider_config(dataset)
    slider_defaults = slider_config or {"min": 0, "max": 0, "value": [0, 0], "marks": {}}
    store_payload = _serialize_dataset(dataset)

    metrics = build_metrics_row(
        [
            build_stat_card("Monitoring sites", "—", identifier="stations-count"),
            build_stat_card("Measurements analysed", "—", identifier="measurements-count"),
            build_stat_card("Latest measurement", "—", identifier="last-update"),
        ]
    )

    histogram_controls = [
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

    histogram_section = build_graph_section(
        "radiation-histogram",
        title="Gamma dose distribution",
        description=(
            "Explore how gamma dose results are distributed and compare collection media "
            "or radionuclides using the interactive controls."
        ),
        controls=histogram_controls,
        footer=html.Span("Unit: —", id="histogram-unit-legend", className="graph-section__legend-text"),
    )

    map_section = build_graph_section(
        "radiation-map",
        title="Geolocated monitoring stations",
        description=(
            "An interactive map highlighting radiation monitoring stations and associated weather observations."
        ),
    )

    time_series_section = build_graph_section(
        "rainfall-timeseries",
        title="Precipitation and gamma dose dynamics",
        description=(
            "A combined time-series view to correlate rainfall intensity with gamma dose variations over time."
        ),
    )

    commune_corr_section = build_graph_section(
        "commune-corr-map",
        title="Corrélation pluie ↔ dose gamma (par commune)",
        description=(
            "Coefficient de corrélation de Pearson (r) entre la pluie et la dose gamma, "
            "calculé à partir des mesures disponibles par commune."
        ),
    )

    commune_mean_section = build_graph_section(
        "commune-mean-map",
        title="Dose gamma moyenne (par commune)",
        description=("Moyenne des résultats de dose gamma, agrégée au niveau communal."),
    )


    rain_vs_radio_section = build_rain_vs_radio_section()

    return html.Div(
        className="home-page",
        children=[
            build_header(
                "Rain & Dust Spikes",
                "Why does the gamma dose rise after rainfall?",
            ),
            build_navbar(),
            html.Main(
                className="home-page__content",
                children=[
                    metrics,
                    histogram_section,
                    map_section,    
                    time_series_section,
                    rain_vs_radio_section,
                    dcc.Store(id="radiation-data-store", data=store_payload, storage_type="memory"),
                ],
            ),
            build_footer(),
        ],
    )


def register_callbacks(app: Dash) -> None:
    """Register interactive callbacks for the home page."""

    @app.callback(
        Output("stations-count", "children"),
        Output("measurements-count", "children"),
        Output("last-update", "children"),
        Input("radiation-data-store", "data"),
    )
    def _update_stat_cards(payload: str | None) -> tuple[list[Component], list[Component], list[Component]]:
        dataset = _deserialize_dataset(payload)

        if dataset.empty:
            return (
                _stat_card_children("Monitoring sites", "—"),
                _stat_card_children("Measurements analysed", "—"),
                _stat_card_children("Latest measurement", "—"),
            )

        site_count = 0
        if {LAT_COLUMN, LON_COLUMN}.issubset(dataset.columns):
            site_count = (
                dataset[[LAT_COLUMN, LON_COLUMN]]
                .dropna()
                .drop_duplicates()
                .shape[0]
            )
        if site_count == 0 and MUNICIPALITY_COLUMN in dataset:
            site_count = dataset[MUNICIPALITY_COLUMN].nunique()

        measurement_count = int(dataset.shape[0])
        latest_date = dataset[DATE_COLUMN].max() if DATE_COLUMN in dataset else None

        return (
            _stat_card_children("Monitoring sites", _format_integer(site_count)),
            _stat_card_children("Measurements analysed", _format_integer(measurement_count)),
            _stat_card_children("Latest measurement", _format_date(latest_date)),
        )

    @app.callback(
        Output("radiation-histogram", "figure"),
        Output("histogram-unit-legend", "children"),
        Input("radionuclide-filter", "value"),
        Input("medium-filter", "value"),
        Input("date-range-slider", "value"),
        Input("radiation-data-store", "data"),
    )
    def _update_histogram(
        selected_radionuclides: Iterable[str] | None,
        selected_media: Iterable[str] | None,
        slider_range: list[int] | None,
        payload: str | None,
    ) -> tuple[go.Figure, Component]:
        dataset = _deserialize_dataset(payload)

        if dataset.empty:
            return _empty_histogram_figure("No radiation measurements are available yet."), html.Span(
                "Unit: —", className="graph-section__legend-text"
            )

        filtered = dataset.copy()

        radionuclide_filter = _normalise_selection(selected_radionuclides)
        medium_filter = _normalise_selection(selected_media)

        if radionuclide_filter:
            filtered = filtered[filtered[RADION_COLUMN].isin(radionuclide_filter)]
        if medium_filter:
            filtered = filtered[filtered[MEDIUM_COLUMN].isin(medium_filter)]
        if slider_range and len(slider_range) == 2:
            start = pd.to_datetime(slider_range[0], unit="s")
            end = pd.to_datetime(slider_range[1], unit="s")
            filtered = filtered[filtered[DATE_COLUMN].between(start, end)]

        if filtered.empty:
            return _empty_histogram_figure("No data matches the current filters."), html.Span(
                "Unit: —", className="graph-section__legend-text"
            )

        color_dimension: str | None = None
        color_kwargs: dict[str, Any] = {}
        if MEDIUM_COLUMN in filtered and filtered[MEDIUM_COLUMN].nunique() > 1:
            color_dimension = MEDIUM_COLUMN
            medium_values = filtered[MEDIUM_COLUMN].dropna().astype(str).unique().tolist()
            fallback_palette = px.colors.qualitative.Set2
            color_kwargs["color_discrete_map"] = {
                value: _MEDIUM_COLOR_MAP.get(value, fallback_palette[i % len(fallback_palette)])
                for i, value in enumerate(medium_values)
            }
        elif RADION_COLUMN in filtered and filtered[RADION_COLUMN].nunique() > 1:
            color_dimension = RADION_COLUMN
            color_kwargs["color_discrete_sequence"] = px.colors.qualitative.Set2

        bin_count = _compute_bin_count(filtered[RESULT_COLUMN])
        if MEDIUM_COLUMN in filtered and filtered[MEDIUM_COLUMN].nunique() > 1:
            color_dimension = MEDIUM_COLUMN
        elif RADION_COLUMN in filtered and filtered[RADION_COLUMN].nunique() > 1:
            color_dimension = RADION_COLUMN

        histogram = px.histogram(
            filtered,
            x=RESULT_COLUMN,
            color=color_dimension,
            nbins=bin_count,  # ou remplace par 40 si tu veux forcer
            opacity=0.85,
            labels={
                RESULT_COLUMN: "Gamma dose result (Bq/kg or Bq/L)",
                MEDIUM_COLUMN: "Measurement environment",
                RADION_COLUMN: "Radionuclide",
            },
            **color_kwargs,
        )

        histogram.update_traces(
            marker_line_color="rgba(15, 23, 42, 0.15)",
            marker_line_width=1,
            hovertemplate="%{y} samples<br>Gamma dose: %{x:.2f}<extra></extra>",
        )

        if color_dimension is None:
            histogram.update_traces(marker_color="#2563eb")

        histogram.update_layout(
            template="simple_white",
            paper_bgcolor="rgba(0, 0, 0, 0)",
            plot_bgcolor="rgba(0, 0, 0, 0)",
            bargap=0.04,
            bargroupgap=0.0,
            barmode="overlay",
            legend=dict(
                title="" if not color_dimension else "",
                bgcolor="rgba(255, 255, 255, 0.92)",
                bordercolor="rgba(15, 23, 42, 0.08)",
                borderwidth=1,
            ),
        )

        histogram.update_traces(marker_line_width=0)
        histogram.update_layout(
            template="plotly_dark",
            paper_bgcolor="rgba(13, 23, 44, 0.0)",
            plot_bgcolor="rgba(13, 23, 44, 0.0)",
            bargap=0.05,
            legend=dict(
                title="" if not color_dimension else "Legend",
                bgcolor="rgba(15, 23, 42, 0.6)",
                orientation="h",
                yanchor="bottom",
                y=1.02,
                x=0,
                xanchor="left",
                font=dict(size=12),
            ),
            margin=dict(l=20, r=20, t=50, b=70),
            height=420,
            font=dict(color="#0f172a"),
        )
        histogram.update_xaxes(
            title="Gamma dose result (Bq/kg or Bq/L)",
            gridcolor="#d7dde8",
            zeroline=False,
        )
        histogram.update_yaxes(
            title="Number of samples",
            gridcolor="#d7dde8",
            zeroline=False,
            margin=dict(l=20, r=20, t=40, b=60),
            height=420,
            font=dict(color="#f8fbff"),
        )
        histogram.update_xaxes(
            title="Gamma dose result (Bq/kg or Bq/L)",
            gridcolor="rgba(148, 163, 184, 0.25)",
            zerolinecolor="rgba(148, 163, 184, 0.35)",
        )
        histogram.update_yaxes(
            title="Frequency",
            gridcolor="rgba(148, 163, 184, 0.2)",
            zerolinecolor="rgba(148, 163, 184, 0.35)",
        )

        units = []
        if UNIT_COLUMN in filtered:
            units = (
                pd.Series(filtered[UNIT_COLUMN].dropna().unique())
                .astype(str)
                .sort_values()
                .tolist()
            )

        if units:
            legend_text = f"Unit{'s' if len(units) > 1 else ''}: {', '.join(units)}"
        else:
            legend_text = "Unit: Not specified"

        return histogram, html.Span(legend_text, className="graph-section__legend-text")

    @app.callback(
        Output("rain-radio-graph", "figure"),
        Input("radiation-data-store", "data"),
    )
    def _update_rain_radio_scatter(payload: str | None):
        df = _deserialize_dataset(payload)

        # Filtrer unité Bq/kg sec
        df = df[df[UNIT_COLUMN] == "becquerel par kg sec"]

        # Filtrer présence colonnes
        if df.empty or "Rainfall" not in df or RESULT_COLUMN not in df:
            return px.scatter(
                title="Rainfall vs Radioactivity — no data available"
            )

        # Convertir
        df["Rainfall"] = pd.to_numeric(df["Rainfall"], errors="coerce")
        df = df.dropna(subset=["Rainfall", RESULT_COLUMN])

        fig = px.scatter(
            df,
            x="Rainfall",
            y=RESULT_COLUMN,
            labels={"Rainfall": "Rainfall (mm)", RESULT_COLUMN: "Radioactivity (Bq/kg sec)"},
            trendline="ols",
            opacity=0.8,
            title="Rainfall vs Radioactivity (Bq/kg sec)",
        )

        fig.update_layout(
            template="simple_white",
            paper_bgcolor="rgba(0, 0, 0, 0)",
            plot_bgcolor="rgba(0, 0, 0, 0)",
            height=420,
        )

        return fig


__all__ = ["layout", "register_callbacks"]
