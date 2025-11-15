from .sections import build_graph_section
from dash import dcc, html

def build_rainfall_histogram_section():
    medium_toggle = html.Div(
        dcc.RadioItems(
            id="medium-filter1",
            options=[
                {"label": "Water", "value": "water"},
                {"label": "Soil", "value": "soil"},
            ],
            value="water",
            labelStyle={"display": "inline-block", "margin-right": "1rem"},
            inputStyle={"margin-right": "0.5rem"},
        ),
        className="medium-toggle"
    )
    return build_graph_section(
        graph_id="rainfall-histogram",
        title="Radioactivity Distribution: Dry vs Rainy Days",
        description="Histogram comparing the distribution of radioactivity values on dry days (<0.1 mm) and rainy days (≥0.1 mm).",
        controls=[medium_toggle],
    )

