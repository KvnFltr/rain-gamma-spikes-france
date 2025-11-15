"""Dashboard callback registration."""
from __future__ import annotations
from dash import Input, Output, html
import plotly.express as px
from typing import Iterable
import numpy as np
import pandas as pd
import plotly.graph_objects as go
from dash import Dash, Input, Output, html
from dash.development.base_component import Component


from config import (
    DATE_COLUMN, 
    RESULT_COLUMN, 
    UNIT_COLUMN,
    RADION_COLUMN,
    MEDIUM_COLUMN, 
    LAT_COLUMN,
    LON_COLUMN, 
    MUNICIPALITY_COLUMN, 
    RAINFALL_COLUMN
)
from .utils import (
    deserialize_dataset, 
    normalize_selection,
    format_integer, 
    format_date, 
    normalize_name,
    load_communes_geojson,
)

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
        Output("commune-corr-map", "figure"),
        Output("commune-mean-map", "figure"),
        Input("radionuclide-filter", "value"),
        Input("medium-filter", "value"),
        Input("date-range-slider", "value"),
        Input("radiation-data-store", "data"),
    )
    def update_commune_maps(
        selected_radionuclides: Iterable[str] | None,
        selected_media: Iterable[str] | None,
        slider_range: list[int] | None,
        payload: str | None,
    ) -> tuple[go.Figure, go.Figure]:
        """Update the commune-level choropleth maps for correlation and mean dose."""
        df = deserialize_dataset(payload)

        # Vérification des colonnes nécessaires
        needed = {MUNICIPALITY_COLUMN, RESULT_COLUMN, "Rainfall"}
        if df.empty or not needed.issubset(df.columns):
            msg = "No commune/rain/dose data to compute the choropleths."
            return _empty_histogram_figure(msg), _empty_histogram_figure(msg)

        # Copie et filtres
        f = df.copy()
        if selected_radionuclides:
            f = f[f[RADION_COLUMN].isin(normalize_selection(selected_radionuclides))]
        if selected_media:
            f = f[f[MEDIUM_COLUMN].isin(normalize_selection(selected_media))]
        if slider_range and len(slider_range) == 2 and DATE_COLUMN in f:
            start = pd.to_datetime(slider_range[0], unit="s")
            end = pd.to_datetime(slider_range[1], unit="s")
            f = f[f[DATE_COLUMN].between(start, end, inclusive="both")]

        # Types et nettoyage
        f[RESULT_COLUMN] = pd.to_numeric(f[RESULT_COLUMN], errors="coerce")
        f["Rainfall"] = pd.to_numeric(f["Rainfall"], errors="coerce")
        f = f.dropna(subset=[MUNICIPALITY_COLUMN, RESULT_COLUMN, "Rainfall"])
        if f.empty:
            msg = "No data left after filtering."
            return _empty_histogram_figure(msg), _empty_histogram_figure(msg)

        # Clé de jointure par nom normalisé
        f["commune_key"] = f[MUNICIPALITY_COLUMN].astype(str).map(normalize_name)

        # Agrégations par commune
        def _safe_corr(g: pd.DataFrame) -> float | None:
            # Exige un minimum de points pour éviter les corrélations absurdes
            if g[RESULT_COLUMN].count() >= 5 and g["Rainfall"].count() >= 5:
                corr_value = g[RESULT_COLUMN].corr(g["Rainfall"])
                return float(corr_value) if not pd.isna(corr_value) else np.nan
            return np.nan

        agg = (
            f.groupby("commune_key", as_index=False)
            .agg(
                mean_dose=(RESULT_COLUMN, "mean"),
                mean_rain=("Rainfall", "mean"),
                n_points=(RESULT_COLUMN, "count"),
                corr=lambda g: _safe_corr(g),
            )
        )

        # Charge polygones et prépare bornes de couleurs
        gj = load_communes_geojson()
        if agg["mean_dose"].notna().any():
            ql, qh = agg["mean_dose"].quantile([0.05, 0.95])
            mean_color = agg["mean_dose"].clip(ql, qh)
        else:
            mean_color = agg["mean_dose"]

        # Choroplèthe corrélation (r ∈ [-1, 1])
        corr_fig = px.choropleth(
            agg,
            geojson=gj,
            locations="commune_key",
            featureidkey="properties.nom_key",
            color="corr",
            color_continuous_scale=[(0.0, "#4575b4"), (0.5, "#ffffbf"), (1.0, "#d73027")],
            range_color=(-1, 1),
            hover_data={"mean_dose": ":.3f", "mean_rain": ":.2f", "n_points": True, "corr": ":.2f"},
            labels={"mean_dose": "Mean dose", "mean_rain": "Mean rain (mm)"},
        )
        corr_fig.update_layout(
            geo=dict(fitbounds="locations", visible=False),
            margin=dict(l=10, r=10, t=40, b=10),
            paper_bgcolor="rgba(13, 23, 44, 0.0)",
            plot_bgcolor="rgba(13, 23, 44, 0.0)",
            template="plotly_dark",
            coloraxis_colorbar=dict(title="r (rain↔dose)"),
            height=520,
        )

        # Choroplèthe dose moyenne
        mean_fig = px.choropleth(
            agg.assign(mean_color=mean_color),
            geojson=gj,
            locations="commune_key",
            featureidkey="properties.nom_key",
            color="mean_color",
            color_continuous_scale="Viridis",
            hover_data={"mean_dose": ":.3f", "mean_rain": ":.2f", "n_points": True, "corr": ":.2f"},
            labels={"mean_color": "Mean dose"},
        )
        mean_fig.update_layout(
            geo=dict(fitbounds="locations", visible=False),
            margin=dict(l=10, r=10, t=40, b=10),
            paper_bgcolor="rgba(13, 23, 44, 0.0)",
            plot_bgcolor="rgba(13, 23, 44, 0.0)",
            template="plotly_dark",
            coloraxis_colorbar=dict(title="Mean dose"),
            height=520,
        )

        return corr_fig, mean_fig


    @app.callback(
        Output("radiation-map", "figure"),
        Input("radiation-data-store", "data"),
    )
    def update_radiation_map(payload: str | None) -> go.Figure:
        """Update the geographic map of monitoring stations with colour-coded radiation."""
        df = deserialize_dataset(payload)

        # Vérifications de base : vérification si coord
        if df.empty or LAT_COLUMN not in df or LON_COLUMN not in df:
            return _empty_histogram_figure("No geolocation data available")

        df = df.dropna(subset=[LAT_COLUMN, LON_COLUMN])
        if df.empty:
            return _empty_histogram_figure("No geolocated radiation data available")

        # Essai des pts colorés + barre indicative
        try:
            has_result = RESULT_COLUMN in df
            color_col = None

            if has_result:
                df = df.copy()
                df[RESULT_COLUMN] = pd.to_numeric(df[RESULT_COLUMN], errors="coerce")
                
                #colaration si on a u min de valeurs numériques
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
                #si pas de dose exploitable, points bleus classiques
                fig = px.scatter_mapbox(
                    df,
                    lat=LAT_COLUMN,
                    lon=LON_COLUMN,
                    hover_data=hover_data,
                    zoom=5,
                )

            # Layout
            fig.update_layout(
                mapbox_style="open-street-map",
                height=500,
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
            # Si quelque chose marche pas, on revient à la carte simple de base
            #    pour voir clairement si probleme 
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
        Output("rainfall-timeseries", "figure"),
        Input("radiation-data-store", "data"),
    )
    def update_timeseries(payload: str | None) -> go.Figure:
        """Update the time series plot for rainfall and radiation."""
        df = deserialize_dataset(payload)

        if df.empty or RAINFALL_COLUMN not in df or DATE_COLUMN not in df:
            return _empty_histogram_figure("No time series data available")

        # Créer la série temporelle
        fig = px.line(df, x=DATE_COLUMN, y=[RAINFALL_COLUMN, RESULT_COLUMN])

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
                f"Dry day (<{threshold} mm)": "#ff4444", 
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



__all__ = ["register_all_callbacks"]
