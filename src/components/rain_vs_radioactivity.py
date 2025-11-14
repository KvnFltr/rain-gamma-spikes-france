from typing import Any
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from dash.development.base_component import Component
import dash

def build_rain_vs_radio_section(data: pd.DataFrame) -> Component:
    """
    Crée un graphique de dispersion montrant la radioactivité en fonction de la pluie,
    avec une couleur différente pour chaque unité de radioactivité.
    """
    fig = px.scatter(
        data,
        x="Rainfall",
        y="Result radioactivity",
        color="Unit radioactivity",
        title="Radioactivité en fonction de la pluie",
        labels={
            "Rainfall": "Pluie (mm)",
            "Result radioactivity": "Radioactivité (unité)",
            "Unit radioactivity": "Unité de radioactivité"
        },
        hover_data=["Municipality name", "Radionuclide"],
    )
    fig.update_layout(
        legend_title_text="Unité de radioactivité",
        hovermode="closest",
    )
    return dcc.Graph(id="rain-radio-graph", figure=fig)