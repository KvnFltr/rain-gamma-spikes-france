from dash import html
from .sections import build_graph_section

def build_daily_measurements_section():
    return build_graph_section(
        graph_id="daily-measurements-graph",
        title="Daily Measurements Count",
        description="Number of radiation measurements recorded each day.",
    )