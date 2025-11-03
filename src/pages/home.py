"""Layout definition for the dashboard home page."""

from __future__ import annotations

from dash import dcc, html

from ..components import (
    build_footer,
    build_graph_section,
    build_header,
    build_metrics_row,
    build_navbar,
    build_stat_card,
)


def layout() -> html.Div:
    """Return the main dashboard layout."""

    metrics = build_metrics_row(
        [
            build_stat_card("Stations suivies", "—", identifier="stations-count"),
            build_stat_card("Mesures analysées", "—", identifier="measurements-count"),
            build_stat_card("Dernière mise à jour", "—", identifier="last-update"),
        ]
    )

    histogram_section = build_graph_section(
        "radiation-histogram",
        title="Distribution des doses gamma",
        description=(
            "Histogramme interactif permettant de comparer la répartition des"
            " doses gamma avant et après les épisodes pluvieux."
        ),
    )

    map_section = build_graph_section(
        "radiation-map",
        title="Stations de mesure géolocalisées",
        description=(
            "Carte interactive affichant les stations de surveillance de la radioactivité"
            " et les cumuls de pluie correspondants."
        ),
    )

    time_series_section = build_graph_section(
        "rainfall-timeseries",
        title="Précipitations et radioactivité",
        description=(
            "Visualisation dynamique corrélant les précipitations journalières"
            " aux variations de la dose gamma."
        ),
    )

    return html.Div(
        className="home-page",
        children=[
            build_header(
                "Rain & Dust Spikes",
                "Pourquoi la dose gamma grimpe-t-elle après la pluie ?",
            ),
            build_navbar(),
            html.Main(
                className="home-page__content",
                children=[
                    metrics,
                    histogram_section,
                    map_section,
                    time_series_section,
                    dcc.Store(id="radiation-data-store"),
                ],
            ),
            build_footer(),
        ],
    )


__all__ = ["layout"]
