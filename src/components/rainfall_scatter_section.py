from dash import dcc, html
from .sections import build_graph_section

def build_rainfall_scatter_section():
    controls = [
        html.Div(
            [
                html.Label("Unit", className="control-label", htmlFor="scatter-unit-filter"),
                dcc.RadioItems(
                    id="scatter-unit-filter",
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
                html.Label("Y scale", className="control-label", htmlFor="scatter-y-scale"),
                dcc.RadioItems(
                    id="scatter-y-scale",
                    options=[{"label": "Linear", "value": "linear"}, {"label": "Log", "value": "log"}],
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
        graph_id="rainfall-scatter",
        title="Rainfall vs. radioactivity",
        description="Scatter of daily rainfall (mm) vs radioactivity result.",
        controls=controls,
    )