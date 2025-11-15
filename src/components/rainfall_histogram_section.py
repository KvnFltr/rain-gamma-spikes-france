from .sections import build_graph_section

def build_rainfall_histogram_section():
    return build_graph_section(
        graph_id="rainfall-histogram",
        title="Radioactivity Distribution: Dry vs Rainy Days",
        description="Histogram comparing the distribution of radioactivity values on dry days (<0.1 mm) and rainy days (≥0.1 mm).",
    )

