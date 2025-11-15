from .sections import build_graph_section
from dash import dcc, html

def build_rainfall_histogram_section():
    medium_toggle = html.Div(
        [
            html.Label(
                "Medium", 
                className="filter-label",
                style={"margin-bottom": "0.5rem", "display": "block"}
           ),
            dcc.RadioItems(
                id="medium-filter1",
                options=[
                    {"label": "Water", "value": "water"},
                    {"label": "Soil", "value": "soil"},
                ],
                value="water",
                labelStyle={"display": "inline-block", "margin-left": "1rem"},
                inputStyle={"margin-left": "0.5rem"},
            )
        ],
        className="medium-toggle"
    )

    rainfall_slider = html.Div(
        [
            html.Label("Rainfall threshold (mm)", className="filter-label"),
            dcc.Slider(
                id="rainfall-threshold",
                min=0.0,
                max=4.0,
                step=0.05,
                value=0.1,
                marks={0: "0", 1: "1", 2: "2", 3: "3", 4: "4"},
                tooltip={"always_visible": True, "placement": "top"},
            )
        ],
        className="control-slider"
    )

    return build_graph_section(
        graph_id="rainfall-histogram",
        title="Radioactivity Distribution: Dry vs Rainy Days",
        description="Histogram comparing the distribution of radioactivity values on dry days (<0.1 mm) and rainy days (≥0.1 mm).",
        controls=[medium_toggle, rainfall_slider],
    )

