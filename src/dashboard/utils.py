"""Utility functions for data processing and formatting."""

import unicodedata
import pandas as pd
import numpy as np
import json
from typing import Iterable
from functools import lru_cache
from config import DATE_COLUMN, RESULT_COLUMN, MEDIUM_COLUMN, DATA_PATH, GEOJSON_PATH, MEDIUM_LABELS

def normalize_name(s: str) -> str:
    """Normalize numicipality's name for display."""
    if not isinstance(s, str):
        return ""
    s = unicodedata.normalize("NFKD", s).encode("ascii", "ignore").decode("ascii")
    return (
        s.lower()
         .replace("-", " ")
         .replace("’", "'")
         .replace("`", "'")
         .strip()
    )

def normalize_selection(selection: Iterable[str] | str | None) -> list[str]:
    """Normalize selection from Dash payload."""

    if selection is None:
        return []
    if isinstance(selection, str):
        return [selection]
    return list(selection)

def format_integer(value: int | float | None) -> str:
    """Format integers with thousands separators for display."""

    if value is None or pd.isna(value):
        return "—"
    return f"{int(value):,}"

def format_date(value: pd.Timestamp | None) -> str:
    """Format date for display."""

    if value is None or pd.isna(value):
        return "—"
    return value.strftime("%b %d, %Y")

def compute_bin_count(series: pd.Series) -> int:
    """Determine an appropriate number of histogram bins."""

    data = pd.Series(series.dropna())
    if data.empty:
        return 10

    values = data.to_numpy(dtype=float)
    values = values[np.isfinite(values)]
    if values.size <= 1:
        return 5

    q25, q75 = np.percentile(values, [25, 75])
    iqr = q75 - q25
    if iqr <= 0:
        return int(min(50, max(5, round(np.sqrt(values.size)))))

    bin_width = 2 * iqr / np.cbrt(values.size)
    if bin_width <= 0:
        return int(min(50, max(5, round(np.sqrt(values.size)))))

    data_range = values.max() - values.min()
    if data_range == 0:
        return 5

    bins = int(np.ceil(data_range / bin_width))
    return int(min(max(bins, 6), 60))

def serialize_dataset(dataset: pd.DataFrame | None) -> str | None:
    """Serialize dataframe to JSON."""

    if dataset is None or dataset.empty:
        return None
    return dataset.to_json(date_format="iso", orient="records")

def deserialize_dataset(payload: str | None) -> pd.DataFrame:
    """Deserialize dataset JSON stored in :class:`dcc.Store`."""

    if not payload:
        return pd.DataFrame()
    dataframe = pd.read_json(payload, orient="records")
    if DATE_COLUMN in dataframe:
        dataframe[DATE_COLUMN] = pd.to_datetime(dataframe[DATE_COLUMN], errors="coerce")
        dataframe = dataframe.dropna(subset=[DATE_COLUMN])
    if RESULT_COLUMN in dataframe:
        dataframe[RESULT_COLUMN] = pd.to_numeric(dataframe[RESULT_COLUMN], errors="coerce")
        dataframe = dataframe.dropna(subset=[RESULT_COLUMN])
    if MEDIUM_COLUMN in dataframe:
        dataframe[MEDIUM_COLUMN] = dataframe[MEDIUM_COLUMN].replace(MEDIUM_LABELS)
    return dataframe

@lru_cache(maxsize=1)
def load_dataset() -> pd.DataFrame:
    """Load and cache the cleaned dataset used by the dashboard."""

    if not DATA_PATH.exists():
        raise FileNotFoundError(DATA_PATH)

    raw_df = pd.read_csv(DATA_PATH, sep=";", low_memory=False)
    dataset = raw_df.copy()

    if RESULT_COLUMN in dataset:
        dataset[RESULT_COLUMN] = pd.to_numeric(dataset[RESULT_COLUMN], errors="coerce")
        dataset = dataset.dropna(subset=[RESULT_COLUMN])

    if DATE_COLUMN in dataset:
        dataset[DATE_COLUMN] = pd.to_datetime(dataset[DATE_COLUMN], errors="coerce", utc=True)
        dataset = dataset.dropna(subset=[DATE_COLUMN])
        dataset[DATE_COLUMN] = dataset[DATE_COLUMN].dt.tz_localize(None)
        dataset = dataset.sort_values(DATE_COLUMN)

    if MEDIUM_COLUMN in dataset:
        dataset[MEDIUM_COLUMN] = dataset[MEDIUM_COLUMN].replace(MEDIUM_LABELS)

    return dataset.reset_index(drop=True)


def get_dataset() -> pd.DataFrame | None:
    """Return a copy of the cached dataset, or ``None`` if unavailable."""

    try:
        return load_dataset().copy()
    except (FileNotFoundError, pd.errors.EmptyDataError, pd.errors.ParserError):
        return None


@lru_cache(maxsize=1)
def load_communes_geojson() -> dict:
    """Charge le GeoJSON des communes et ajoute 'properties.nom_key' normalisé pour la jointure."""
    with open(GEOJSON_PATH, "r", encoding="utf-8") as f:
        gj = json.load(f)
    for feat in gj.get("features", []):
        props = feat.setdefault("properties", {})
        nom = props.get("nom", "")
        props["nom_key"] = normalize_name(nom)
    return gj