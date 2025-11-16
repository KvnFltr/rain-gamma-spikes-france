"""Dashboard callback registration."""
from __future__ import annotations
from dash import Input, Output, html
import plotly.express as px
import pandas as pd
import plotly.graph_objects as go
from dash import Dash, Input, Output, html
from dash.development.base_component import Component

from config import (
    DATE_COLUMN, 
    RESULT_COLUMN, 
    UNIT_COLUMN,
    LAT_COLUMN,
    LON_COLUMN, 
    MUNICIPALITY_COLUMN, 
    RAINFALL_COLUMN,
)
from .utils import (
    deserialize_dataset, 
    format_integer, 
    format_date,
)


def register_all_callbacks(app: Dash) -> None:
    """Register all dashboard callbacks."""

    @app.callback(
        Output("stations-count", "children"),
        Output("measurements-count", "children"),
        Output("last-update", "children"),
        Input("radiation-data-store", "data"),
    )
    def update_stat_cards(
        payload: str | None,
    ) -> tuple[list[Component], list[Component], list[Component]]:
        """Update the statistics cards with current data metrics."""
        dataset = deserialize_dataset(payload)

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
            _stat_card_children("Monitoring sites", format_integer(site_count)),
            _stat_card_children("Measurements analysed", format_integer(measurement_count)),
            _stat_card_children("Latest measurement", format_date(latest_date)),
        )
    

    @app.callback(
        Output("rainfall-histogram", "figure"),
        Input("radiation-data-store", "data"),
        Input("medium-filter1", "value"),
        Input("rainfall-threshold", "value"),
    )
    def update_rainfall_histogram(payload: str | None, medium: str, threshold: float):
        """Histogram comparing radioactivity distributions, filtered by medium."""
        
        df = deserialize_dataset(payload)
        
        needed = {RESULT_COLUMN, UNIT_COLUMN, RAINFALL_COLUMN}
        if df.empty or not needed.issubset(df.columns):
            return px.histogram(title="No data available")
       
        if medium == "water":
            df = df[df[UNIT_COLUMN] == "becquerel par litre"]
            axis_label = "Radioactivity (Bq/L)"
        elif medium == "soil":
            df = df[df[UNIT_COLUMN] == "becquerel par kg sec"]
            axis_label = "Radioactivity (Bq/kg dry)"

        df[RESULT_COLUMN] = pd.to_numeric(df[RESULT_COLUMN], errors="coerce")
        df[RAINFALL_COLUMN] = pd.to_numeric(df[RAINFALL_COLUMN], errors="coerce")
        df = df.dropna(subset=[RESULT_COLUMN, RAINFALL_COLUMN])

        if df.empty:
            return px.histogram(title="No matching data to display")

        df["Rain category"] = df[RAINFALL_COLUMN].apply(
            lambda x: "Dry" if x < threshold else "Rainy"
        )

        bins = [0, 0.0125, 0.025, 0.05, 0.1, 0.2, 0.4, 0.8, 1.6, 3.2, 6.4, 12.8, 25.6, 51.2, 102.4, 204.8, 409.6, 1000]
        bin_labels = [f"{bins[i]} - {bins[i+1]}" for i in range(len(bins)-1)]
        df["Radio_bin"] = pd.cut(df[RESULT_COLUMN], bins=bins, labels=bin_labels, include_lowest=True)
  
        fig = px.histogram(
            df,
            x="Radio_bin",
            color="Rain category",
            opacity=0.8,
            barmode='group',
            histnorm='percent',
            category_orders={"Radio_bin": bin_labels},
            color_discrete_map={
                "Dry": "#e0f2fe",
                "Rainy": "#38bdf8",
            },
            labels={
                "Radio_bin": axis_label,
                "Rain category": "Rain category"
            },
            title="Radioactivity Distribution on Dry vs Rainy Days"
        )

        fig.update_layout(
            template="plotly_dark",
            paper_bgcolor="rgba(13, 23, 44, 0.0)",
            plot_bgcolor="rgba(13, 23, 44, 0.0)",
            margin=dict(l=20, r=20, t=50, b=60),
            height=450,
        )

        return fig

    @app.callback(
        Output("radiation-map", "figure"),
        Input("radiation-data-store", "data"),
        Input("map-year-filter", "value"),
        Input("map-month-filter", "value"),
    )
    def update_radiation_map(
        payload: str | None,
        selected_year: int | None,
        selected_month: int | None,
    ) -> go.Figure:
        """Update the geographic map of monitoring stations with colour-coded radiation + year/month filters."""
        df = deserialize_dataset(payload)

        # Time filtering: year/month
        if DATE_COLUMN in df:
            df = df.copy()
            df[DATE_COLUMN] = pd.to_datetime(df[DATE_COLUMN], errors="coerce")

            if selected_year is not None:
                df = df[df[DATE_COLUMN].dt.year == selected_year]

            if selected_month is not None:
                df = df[df[DATE_COLUMN].dt.month == selected_month]

        # Basic checks: mandatory coordinates
        if df.empty or LAT_COLUMN not in df or LON_COLUMN not in df:
            return _empty_histogram_figure("No geolocation data available for this period")

        df = df.dropna(subset=[LAT_COLUMN, LON_COLUMN])
        if df.empty:
            return _empty_histogram_figure("No geolocated radiation data available for this period")

        # coloured dots + indicator bar
        try:
            has_result = RESULT_COLUMN in df
            color_col = None

            if has_result:
                df = df.copy()
                df[RESULT_COLUMN] = pd.to_numeric(df[RESULT_COLUMN], errors="coerce")

                # colouring if we have a minimum of numerical values
                if df[RESULT_COLUMN].dropna().shape[0] >= 2:
                    vals = df[RESULT_COLUMN]

                    # limit the influence of extreme values
                    q_low, q_high = vals.quantile([0.05, 0.95])
                    if (
                        pd.notna(q_low)
                        and pd.notna(q_high)
                        and q_low != q_high
                    ):
                        df["_dose_for_color"] = vals.clip(q_low, q_high)
                        color_col = "_dose_for_color"
                    else:
                        color_col = RESULT_COLUMN
                else:
                    has_result = False

            # Hover data
            hover_data = {}
            if MUNICIPALITY_COLUMN in df:
                hover_data[MUNICIPALITY_COLUMN] = True
            if has_result:
                hover_data[RESULT_COLUMN] = ":.3f"
            if not hover_data:
                hover_data = None

            # Construction of the figure
            if has_result and color_col is not None:
                fig = px.scatter_mapbox(
                    df,
                    lat=LAT_COLUMN,
                    lon=LON_COLUMN,
                    color=color_col,
                    color_continuous_scale="Turbo",  # blue -> red
                    hover_data=hover_data,
                    zoom=5,
                )
            else:
                # if no usable dose, classic blue dots
                fig = px.scatter_mapbox(
                    df,
                    lat=LAT_COLUMN,
                    lon=LON_COLUMN,
                    hover_data=hover_data,
                    zoom=5,
                )
            # Make the points more visible
            fig.update_traces(
                marker=dict(
                    size=20,  
                    opacity=0.7, # visible overlays
                )
            )


            # Layout bigger zoom
            fig.update_layout(
                mapbox_style="open-street-map",
                mapbox=dict(
                    center=dict(lat=46.5, lon=2.5),  # france center
                    zoom=5.2,  #zoom effect 
                ),
                height=800,  # view height
                margin=dict(l=0, r=0, t=0, b=0),
            )


            # Colour bar on the left if you have a coloraxis
            if has_result and color_col is not None and "coloraxis" in fig.layout:
                fig.update_layout(
                    coloraxis_colorbar=dict(
                        title=dict(
                            text="Gamma dose",
                            font=dict(color="white"),
                        ),
                        tickfont=dict(
                            color="white",
                        ),
                        x=0.02, # stuck to the left edge
                        xanchor="left",
                        y=0.5,
                        yanchor="middle",
                        len=0.7,
                        thickness=12,
                        bgcolor="rgba(15, 23, 42, 0.7)",  # semi-transparent background
                        outlinewidth=0,
                    )
                )

            return fig

        except Exception as e:
            # If something does not work, we revert to the basic simple card.
            simple_fig = px.scatter_mapbox(
                df,
                lat=LAT_COLUMN,
                lon=LON_COLUMN,
                hover_data=[MUNICIPALITY_COLUMN, RESULT_COLUMN]
                if MUNICIPALITY_COLUMN in df and RESULT_COLUMN in df
                else None,
                zoom=5,
            )
            simple_fig.update_layout(
                mapbox_style="open-street-map",
                height=500,
                margin=dict(l=0, r=0, t=0, b=0),
            )
            return simple_fig

            
    @app.callback(
        Output("daily-measurements-graph", "figure"),
        Input("radiation-data-store", "data"),
    )
    def update_daily_measurements_graph(payload: str | None):
        """Plot the number of radiation measurements per day."""
        
        if payload is None:
            return px.line(title="No data available")

        df = deserialize_dataset(payload)

        if df.empty or DATE_COLUMN not in df:
            return px.line(title="No date data available")

        df[DATE_COLUMN] = pd.to_datetime(df[DATE_COLUMN], errors="coerce")
        df = df.dropna(subset=[DATE_COLUMN])

        daily_counts = (
            df.groupby(df[DATE_COLUMN].dt.date)
            .size()
            .reset_index(name="count")
        )

        daily_counts.rename(columns={DATE_COLUMN: "date"}, inplace=True)

        fig = px.bar(
            daily_counts,
            x="date",
            y="count",
            title="Daily Measurements Count",
        )
        fig.update_traces(
            selector=dict(type="bar"),
            marker=dict(
                color="#ffffff",
                line=dict(color="#ffffff", width=0.6),
            ),
            opacity=1.0,
        )

        fig.update_layout(
            template="plotly_dark",
            paper_bgcolor="rgba(13, 23, 44, 0.0)",
            plot_bgcolor="rgba(13, 23, 44, 0.0)",
            margin=dict(l=20, r=20, t=50, b=60),
            height=450
        )

        return fig
    


    

    # Boxplot: radioactivity by rainfall class (true boxplot, unit filter, linear/log Y scale)
    @app.callback(
        Output("rainfall-boxplot", "figure"),
        Input("radiation-data-store", "data"),
        Input("unit-filter", "value"),
        Input("box-y-scale", "value"),
    )
    def update_rainfall_boxplot(
        payload: str | None,
        unit_value: str | None,
        y_scale: str | None,
    ) -> go.Figure:
        df = deserialize_dataset(payload)
        needed = {RESULT_COLUMN, RAINFALL_COLUMN}
        if df.empty or not needed.issubset(df.columns):
            return _empty_boxplot("No radioactivity/rainfall data available.")

        # Minimal cleaning (no capping, no winsorisation)
        f = df.copy()
        f[RESULT_COLUMN] = pd.to_numeric(f[RESULT_COLUMN], errors="coerce")
        f[RAINFALL_COLUMN] = pd.to_numeric(f[RAINFALL_COLUMN], errors="coerce")
        if DATE_COLUMN in f:
            f[DATE_COLUMN] = pd.to_datetime(f[DATE_COLUMN], errors="coerce")
        f = f.dropna(subset=[RESULT_COLUMN, RAINFALL_COLUMN])
        if f.empty:
            return _empty_boxplot("No valid data after parsing.")

        # Unit filter (soil/water) requested
        if unit_value and unit_value != "__all__" and UNIT_COLUMN in f:
            f = f[f[UNIT_COLUMN] == unit_value]

        if f.empty:
            return _empty_boxplot("No data matches the current filters.")

        # Fixed rain classes
        f["Rain class"] = f[RAINFALL_COLUMN].apply(_rain_bin)
        order_bins = ["0", "1–5", "5–10", ">10"]

        # Labels X with staff
        counts = f.groupby("Rain class", as_index=True)[RESULT_COLUMN].size()
        xticks = [f"{c} (n={int(counts.get(c, 0))})" for c in order_bins]

        # Unit for the Y-axis
        y_label = _y_axis_label([unit_value] if unit_value and unit_value != "__all__" else [])

        # Classic box plot (Tukey whiskers + visible outliers) + average as marker
        fig = px.box(
            f,
            x="Rain class",
            y=RESULT_COLUMN,
            category_orders={"Rain class": order_bins},
            points="outliers",
            labels={"Rain class": "Daily rainfall (mm)", RESULT_COLUMN: y_label},
            title="Radioactivity by rainfall class — boxplot",
        )
        fig.update_traces(boxmean=True, marker=dict(opacity=0.45, size=3), line_width=1.2)

        means = (
            f.groupby("Rain class", as_index=False)[RESULT_COLUMN].mean()
             .reindex(order_bins)
        )
        fig.add_trace(
            go.Scatter(
                x=order_bins,
                y=means[RESULT_COLUMN],
                mode="markers",
                name="",
                showlegend=False,
                marker_symbol="triangle-up",
                marker_size=10,
                marker_line_width=1,
            )
        )


        # Style + Y scale
        fig.update_layout(
            template="plotly_dark",
            paper_bgcolor="rgba(13, 23, 44, 0.0)",
            plot_bgcolor="rgba(13, 23, 44, 0.0)",
            margin=dict(l=20, r=20, t=60, b=70),
            height=450,
            legend=dict(orientation="h", yanchor="bottom", y=1.02, x=0, xanchor="left"),
        )
        fig.update_xaxes(
            title="Daily rainfall (mm)",
            tickmode="array", tickvals=order_bins, ticktext=xticks,
            gridcolor="rgba(148,163,184,0.10)",
        )
        fig.update_yaxes(
            title=y_label,
            type=(y_scale or "linear"),
            gridcolor="rgba(148,163,184,0.20)",
            rangemode="tozero",
        )

        # Informative subtitle
        unit_sub = unit_value if unit_value and unit_value != "__all__" else "mixed"
        fig.add_annotation(
            text=f"Unit: {unit_sub} • scale: {y_scale or 'linear'}",
            xref="paper", yref="paper", x=0, y=1.08,
            showarrow=False, font=dict(size=12, color="rgba(200,210,225,0.9)")
        )

        return fig

    # Scatter: Rainfall vs Radioactivity
    @app.callback(
        Output("rainfall-scatter", "figure"),
        Input("radiation-data-store", "data"),
        Input("scatter-unit-filter", "value"),
        Input("scatter-y-scale", "value"),
    )
    def update_rainfall_scatter(
        payload: str | None,
        unit_value: str | None,
        y_scale: str | None,
    ) -> go.Figure:
        df = deserialize_dataset(payload)
        needed = {RESULT_COLUMN, RAINFALL_COLUMN}
        if df.empty or not needed.issubset(df.columns):
            return _empty_histogram_figure("No rainfall/radioactivity data available.")

        f = df.copy()
        f[RESULT_COLUMN] = pd.to_numeric(f[RESULT_COLUMN], errors="coerce")
        f[RAINFALL_COLUMN] = pd.to_numeric(f[RAINFALL_COLUMN], errors="coerce")
        if DATE_COLUMN in f:
            f[DATE_COLUMN] = pd.to_datetime(f[DATE_COLUMN], errors="coerce")

        # Unit filter (space/case tolerant)
        if unit_value and unit_value != "__all__" and UNIT_COLUMN in f:
            f["_unit_norm"] = f[UNIT_COLUMN].astype(str).str.strip().str.lower()
            target = str(unit_value).strip().lower()
            f = f[f["_unit_norm"] == target]

        # Final NA drop
        f = f.dropna(subset=[RESULT_COLUMN, RAINFALL_COLUMN])
        if y_scale == "log":
            f = f[(f[RESULT_COLUMN] > 0) & (f[RAINFALL_COLUMN] > 0)]

        if f.empty:
            return _empty_histogram_figure("No data matches the current filters.")

        # Sampling for performance (scattergl)
        max_points = 50000
        if len(f) > max_points:
            f = f.sample(max_points, random_state=42)

        # ScatterGL
        fig = px.scatter(
            f,
            x=RAINFALL_COLUMN,
            y=RESULT_COLUMN,
            opacity=0.45,
            labels={RAINFALL_COLUMN: "Rainfall (mm)", RESULT_COLUMN: _y_axis_label(
                [unit_value] if unit_value and unit_value != "__all__" else []
            )},
            title="Rainfall vs. radioactivity",
            render_mode="webgl",
        )
        fig.update_traces(marker=dict(size=5), selector=dict(mode="markers"))

        # Style
        fig.update_layout(
            template="plotly_dark",
            paper_bgcolor="rgba(13, 23, 44, 0.0)",
            plot_bgcolor="rgba(13, 23, 44, 0.0)",
            margin=dict(l=20, r=20, t=60, b=60),
            height=450,
            legend=dict(orientation="h", yanchor="bottom", y=1.02, x=0, xanchor="left"),
        )
        fig.update_xaxes(gridcolor="rgba(148,163,184,0.12)")
        fig.update_yaxes(
            type=(y_scale or "linear"),
            gridcolor="rgba(148,163,184,0.20)",
            rangemode="tozero",
        )

        # Informative subtitle
        unit_sub = unit_value if unit_value and unit_value != "__all__" else "mixed"
        fig.add_annotation(
            text=f"Unit: {unit_sub} • scale: {y_scale or 'linear'} • n={len(f):,}",
            xref="paper", yref="paper", x=0, y=1.08, showarrow=False,
            font=dict(size=12, color="rgba(200,210,225,0.9)"),
        )
        return fig

def _rain_bin(mm: float) -> str:
    """
    Args:
        mm: Rainfall amount in millimeters.

    Returns:
        str: Rainfall category as a string ("0", "1–5", "5–10", or ">10").
    """
    if mm <= 0: 
        return "0"
    if mm < 5:
        return "1–5"
    if mm < 10:
        return "5–10"
    return ">10"


def _y_axis_label(units: list[str]) -> str:
    """
    Args:
        units: List of unit strings (e.g., ["Bq/kg", "nSv/h"]).

    Returns:
        str: Formatted y-axis label based on the first unit in the list.
    """
    if not units:
        return "Radioactivity"
    u = units[0].lower()
    if "nanoseivert" in u or "nsv" in u:
        return "Gamma dose (nSv/h)"
    if "par litre" in u:
        return "Radioactivity (Bq/L)"
    if "par kg" in u:
        return "Radioactivity (Bq/kg)"
    return f"Radioactivity ({units[0]})"

def _empty_boxplot(message: str) -> go.Figure:
    """
    Args:
        message: Informative message to display in the empty boxplot.

    Returns:
        go.Figure: Empty Plotly boxplot figure with the message centered.
    """
    fig = go.Figure()
    fig.update_layout(
        template="plotly_dark",
        paper_bgcolor="rgba(13, 23, 44, 0.0)",
        plot_bgcolor="rgba(13, 23, 44, 0.0)",
        height=420,
        margin=dict(l=20, r=20, t=40, b=60),
    )
    fig.add_annotation(
        text=message, x=0.5, y=0.5, xref="paper", yref="paper",
        showarrow=False, font=dict(size=16, color="#a0b4d0")
    )
    return fig

def _stat_card_children(title: str, value: str) -> list[Component]:
    """
    Args:
        title: Title text for the statistic card.
        value: Value text for the statistic card.

    Returns:
        list[Component]: List of Dash components for a statistic card.
    """
    return [
        html.Span(title, className="stat-card__title"),
        html.Strong(value, className="stat-card__value"),
    ]

def _empty_histogram_figure(message: str) -> go.Figure:
    """
    Args:
        message: Informative message to display in the empty histogram.

    Returns:
        go.Figure: Empty Plotly histogram figure with the message centered.
    """
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


__all__ = ["register_all_callbacks"]