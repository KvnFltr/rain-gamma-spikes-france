# src/components/drywet_boxplot_section.py
from dash import html
from .sections import build_graph_section

def build_drywet_boxplot_section():
    """
    Section pour comparer la radioactivité entre jours secs et pluvieux.
    Réutilise les contrôles existants (unit-filter, box-y-scale).
    """
    return build_graph_section(
        graph_id="drywet-boxplot",
        title="Radioactivity — dry vs rainy days",
        description="Distribution of radioactivity between dry (<0.1 mm) and rainy (≥0.1 mm) days.",
        controls=[],  # aucun contrôle additionnel ici
    )

__all__ = ["build_drywet_boxplot_section"]
