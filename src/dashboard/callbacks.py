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
    RAINFALL_COLUMN
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

        # --- 1) Filtrage temporel : année / mois (si DATE_COLUMN existe) ---
        if DATE_COLUMN in df:
            df = df.copy()
            df[DATE_COLUMN] = pd.to_datetime(df[DATE_COLUMN], errors="coerce")

            if selected_year is not None:
                df = df[df[DATE_COLUMN].dt.year == selected_year]

            if selected_month is not None:
                df = df[df[DATE_COLUMN].dt.month == selected_month]

        # --- 2) Vérifications de base : coordonnées obligatoires ---
        if df.empty or LAT_COLUMN not in df or LON_COLUMN not in df:
            return _empty_histogram_figure("No geolocation data available for this period")

        df = df.dropna(subset=[LAT_COLUMN, LON_COLUMN])
        if df.empty:
            return _empty_histogram_figure("No geolocated radiation data available for this period")

        # --- 3) Essai : points colorés + barre indicative ---
        try:
            has_result = RESULT_COLUMN in df
            color_col = None

            if has_result:
                df = df.copy()
                df[RESULT_COLUMN] = pd.to_numeric(df[RESULT_COLUMN], errors="coerce")

                # coloration si on a un minimum de valeurs numériques
                if df[RESULT_COLUMN].dropna().shape[0] >= 2:
                    vals = df[RESULT_COLUMN]

                    # limiter l’influence des valeurs extrêmes
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

            # Construction de la figure
            if has_result and color_col is not None:
                fig = px.scatter_mapbox(
                    df,
                    lat=LAT_COLUMN,
                    lon=LON_COLUMN,
                    color=color_col,
                    color_continuous_scale="Turbo",  # bleu -> rouge
                    hover_data=hover_data,
                    zoom=5,
                )
            else:
                # si pas de dose exploitable, points bleus classiques
                fig = px.scatter_mapbox(
                    df,
                    lat=LAT_COLUMN,
                    lon=LON_COLUMN,
                    hover_data=hover_data,
                    zoom=5,
                )
             # Rendre les points plus lisibles 
            fig.update_traces(
                marker=dict(
                    size=20,      # plus petit que le défaut
                    opacity=0.7, # superpositions plus visibles
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


            # Barre de couleur à gauche si on a une coloraxis
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
                        x=0.02,      # collé au bord gauche
                        xanchor="left",
                        y=0.5,
                        yanchor="middle",
                        len=0.7,
                        thickness=12,
                        bgcolor="rgba(15, 23, 42, 0.7)",  # fond semi-transp.
                        outlinewidth=0,
                    )
                )

            return fig

        except Exception as e:
            # Si quelque chose ne marche pas, on revient à la carte simple de base
            print(f"Error generating radiation map with color scale: {e}")
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
                color="#ffffff",         # blanc pur
                line=dict(color="#ffffff", width=0.6),  # bord blanc fin pour lisibilité
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
            lambda x: f"Dry day (<{threshold} mm)" if x < threshold else f"Rainy day (≥{threshold} mm)"
        )

        bins = [0, 0.0125, 0.025, 0.05, 0.1, 0.2, 0.4, 0.8, 1.6, 3.2, 6.4, 12.8, 25.6, 51.2, 102.4, 204.8, 409.6, 1000]
        bin_labels = [f"{bins[i]} - {bins[i+1]}" for i in range(len(bins)-1)]
        df["Radio_bin"] = pd.cut(df[RESULT_COLUMN], bins=bins, labels=bin_labels, include_lowest=True)

        # Histogram
        fig = px.histogram(
            df,
            x="Radio_bin",
            color="Rain category",
            color_discrete_map={
                f"Dry day (<{threshold} mm)": "#e0f2fe", 
                f"Rainy day (≥{threshold} mm)": "#38bdf8",
            },
            opacity=1,
            barmode='group',
            histnorm='percent',
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


def _stat_card_children(title: str, value: str) -> list[Component]:
    """Return the children used within a statistic card."""
    return [
        html.Span(title, className="stat-card__title"),
        html.Strong(value, className="stat-card__value"),
    ]


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


__all__ = ["register_all_callbacks"]
