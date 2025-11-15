from dash import dcc, html
from .sections import build_graph_section

def build_rainfall_boxplot_section():
    controls = [
        html.Div(
            [
                html.Label("Unit", className="control-label", htmlFor="unit-filter"),
                dcc.RadioItems(
                    id="unit-filter",
                    options=[
                        {"label": "Bq/kg (soil)", "value": "becquerel par kg sec"},
                        {"label": "Bq/L (water)", "value": "becquerel par litre"},
                        {"label": "All", "value": "__all__"},
                    ],
                    value="__all__",
                    inline=True,
                    inputClassName="control-radio-input",
                    labelClassName="control-radio-label",
                ),
            ],
            className="control-group",
        ),
        html.Div(
            [
                html.Label("Y scale", className="control-label", htmlFor="box-y-scale"),
                dcc.RadioItems(
                    id="box-y-scale",
                    options=[
                        {"label": "Linear", "value": "linear"},
                        {"label": "Log", "value": "log"},
                    ],
                    value="linear",
                    inline=True,
                    inputClassName="control-radio-input",
                    labelClassName="control-radio-label",
                ),
            ],
            className="control-group",
        ),
    ]

    return build_graph_section(
        graph_id="rainfall-boxplot",
        title="Radioactivity by Rainfall Class (Boxplot)",
        description="Distribution of radioactivity per daily rainfall class (0 / 1–5 / 5–10 / >10 mm).",
        controls=controls,
    )
