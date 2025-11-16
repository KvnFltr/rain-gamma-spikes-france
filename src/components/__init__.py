"""Reusable UI components for the dashboard."""

from .sections import build_graph_section, build_metrics_row, build_stat_card
from .daily_measurements_section import build_daily_measurements_section
from .rainfall_histogram_section import build_rainfall_histogram_section
from .rainfall_boxplot_section import build_rainfall_boxplot_section 
from .rainfall_scatter_section import build_rainfall_scatter_section

from .footer import build_footer
from .header import build_header
from .navbar import build_navbar

__all__ = [
    "build_footer",
    "build_header",
    "build_navbar",
    "build_metrics_row",
    "build_stat_card",
    "build_daily_measurements_section",
    "build_rainfall_histogram_section",
    "build_rainfall_boxplot_section",
    "build_rainfall_scatter_section",
    "build_graph_section",
]
