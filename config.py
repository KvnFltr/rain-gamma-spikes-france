from typing import Dict
import os
from pathlib import Path

# API URLs
ASNR_RADIATION_URL: str = "https://mesure-radioactivite.fr/#/expert"
METEOFRANCE_WEATHER_DOWNLOAD_URL: str = "https://www.data.gouv.fr/api/1/datasets/r/92065ec0-ea6f-4f5e-8827-4344179c0a7f"
VILLEDEREVE_MUNICIPALITY_DOWNLOAD_URL: str = "https://www.data.gouv.fr/api/1/datasets/r/f5df602b-3800-44d7-b2df-fa40a0350325"

# Data directory paths
BASE_DATA_DIR: str = "data"
DATA_RAW_DIR: str = os.path.join(BASE_DATA_DIR, "raw")
DATA_CLEANED_DIR: str = os.path.join(BASE_DATA_DIR, "cleaned")

# Database configuration
USE_OF_A_DATABASE: bool = False # If we want to store the data in an SQLite database. 
DATABASE_RAW_DIR: str = os.path.join(DATA_RAW_DIR, "database")
DATABASE_RAW_PATH = os.path.join(DATABASE_RAW_DIR, "raw_data.db")

# Table names
WEATHER_TABLE_NAME = "weather_data"
MUNICIPALITY_TABLE_NAME = "municipality_data"
RADIATION_TABLE_PREFIX = "radiation_data"  # Prefix for radiation tables
RADIATION_CONCATENATED_TABLE_NAME = "radiation_data_concatenated"  # Concatenated table

# Names of data files
WEATHER_DATA_FILENAME_GZ: str = "meteofrance_weather_data.csv.gz"
WEATHER_DATA_FILENAME: str = "meteofrance_weather_data.csv"
MUNICIPALITY_DATA_FILENAME: str = "villedereve_municipality_data.csv"
CLEANED_DATA_FILENAME: str = "data.csv"
RADIATION_DATA_FILENAME_PATTERN = "asnr_*_radiation_data_*.csv"

def get_radiation_data_filename(medium_name: str, start_date: str, end_date: str) -> str:
    return f"asnr_{medium_name}_radiation_data_{start_date}_to_{end_date}.csv"

# Timeout in milliseconds for Playwright actions
TIMEOUT: int = 30000
# Initial timeout for browser launch and page loading
INITIAL_TIMEOUT: int = 60000
# Specific timeout for cookie banner
TIMEOUT_REFUSE_COOKIES: int = 100

# CSS selectors for web scraping
SELECTORS: Dict[str, Dict[str, str]] = {
    "modal": {
        "container": "div.modal-content", 
        "button": "div.modal-content span.close"
    },
              
    "collection_environment": {
        "container": "div.row.container-select:has(div.label-select:has-text('Milieu de collecte'))",
        "button": ".selectric .button", 
        "options": ".selectricItems"
    },
    
    "dates": {
        "start": {
            "container": "div.row.container-select:has(div.label-select:has-text('Date de début'))", 
            "input": "input.form-control"
        },
        "end": {
            "container": "div.row.container-select:has(div.label-select:has-text('Date de fin'))", 
            "input": "input.form-control"
        },
    },
    
    "cookies": {
        "banner": "#tarteaucitronAlertBig", 
        "refuse": "#tarteaucitronAllDenied2"
    },
                
    "results": {
        "container": "div.row.container-select:has(button[ng-click='showResult()'])",
        "button": "button.btn.little-margin.middle-size.color-purple[ng-click='showResult()']"
    },

    "download": {
        "tab": {
            "container": "ul li:has-text('Téléchargement')",
            "button": "li[ng-click='showDownloadTree()']"
        },
        "download_button": "button[ng-click='downloadTree()']"
    }
}

# Radiation data configuration
RADIATION_DATA_CONFIG: Dict[str, Dict] = {
    "medium": {
        "soil": {
            "tag": "Sol",
            "name": "soil",
            "temporal_subdivisions": [
                ("01-janvier-2020", "01-janvier-2025")
            ]
        },
        "water": {
            "tag": "Eau",
            "name": "water",
            "temporal_subdivisions": [
                ("01-janvier-2020", "01-janvier-2021"),
                ("01-janvier-2021", "01-janvier-2022"),
                ("01-janvier-2022", "01-janvier-2023"),
                ("01-janvier-2023", "01-janvier-2024"),
                ("01-janvier-2024", "01-janvier-2025")
            ]
        }
    },
    "required_columns": [
        "Date de début de prélèvement",
        "Date de fin de prélèvement",
        "Résultat",
        "Incertitude absolue",
        "Unité",
        "Commune",
        "Espèce",
        "Nature",
        "Radion",
        "Milieu de collecte"
    ],
    "dropna_columns": [
        "Commune",
        "Date de début de prélèvement",
        "Résultat",
        "Unité",
        "Radion",
        "Milieu de collecte"
    ],
    "drop_duplicates_columns": [
        "Date de début de prélèvement",
        "Date de fin de prélèvement",
        "Commune",
        "Radion",
        "Milieu de collecte"
    ],
    "municipality_name": "Commune",
    "date_start_column": "Date de début de prélèvement",

    "latitude_columns": {"cleaned": "latitude"},
    "longitude_columns": {"cleaned": "longitude"},
    "distance_to_nearest_weather_data": "DISTANCE_RADIATION_WEATHER_M",
    "measurement_environment_column":"Milieu de collecte"
}

# Municipality data configuration
MUNICIPALITY_DATA_CONFIG: Dict[str, any] = {
    "required_columns": [
        "nom",
        "latitude",
        "longitude"
    ],
    "name_column": {
        "primary": "nom_standard_majuscule",
        "cleaned": "nom"
    },
    "population_column": "population",
    "latitude_columns": {
        "primary": "latitude_centre",
        "fallback": "latitude_mairie",
        "cleaned": "latitude"
    },
    "longitude_columns": {
        "primary": "longitude_centre",
        "fallback": "longitude_mairie",
        "cleaned": "longitude"
    }
}

# Weather data configuration
WEATHER_DATA_CONFIG: Dict[str, any] = {
    "required_columns": ["LAMBX", "LAMBY", "DATE", "PRENEI", "PRELIQ"],
    "dropna_columns": ["LAMBX", "LAMBY", "DATE", "PRELIQ"],
    "lambert": {"x": "LAMBX", "y": "LAMBY"},
    "geo": {"lat": "latitude", "lon": "longitude"},
    "date_column": "DATE",
    "snowfall_column":"PRENEI",
    "rainfall_column":"PRELIQ"
}

# Cleaned data configuration
CLEANED_DATA_CONFIG: Dict[str, Dict[str, str]] = {
    "rename": {
        "Date de début de prélèvement": "Date start sampling radioactivity",
        "Date de fin de prélèvement": "Date end sampling radioactivity",
        "Résultat": "Result radioactivity",
        "Incertitude absolue": "Absolute uncertainty radioactivity",
        "Unité": "Unit radioactivity",
        "Commune": "Municipality name",
        "Espèce": "Species measurement environment radioactivity",
        "Nature": "Nature measurement environment radioactivity",
        "Radion": "Radionuclide",
        "Milieu de collecte": "Measurement environment",
        "latitude": "Latitude",
        "longitude": "Longitude",
        "DATE_METEO": "Date weather",
        "PRENEI": "Snowfall",
        "PRELIQ": "Rainfall",
        "DISTANCE_RADIATION_WEATHER_M": "Distance measurement weather and radiation m"
    }
}


### For dashboard :

DATA_PATH = Path("data/cleaned/data.csv")
GEOJSON_PATH = Path("data/geodata/communes.geojson")

DATE_COLUMN = "Date start sampling radioactivity"
RESULT_COLUMN = "Result radioactivity"
UNIT_COLUMN = "Unit radioactivity"
RADION_COLUMN = "Radionuclide"
MEDIUM_COLUMN = "Measurement environment"
LAT_COLUMN = "Latitude"
LON_COLUMN = "Longitude"
MUNICIPALITY_COLUMN = "Municipality name"


MEDIUM_LABELS = {
    "Sol": "Soil",
    "sol": "Soil",
    "Eau": "Water",
    "eau": "Water",
}

MEDIUM_COLOR_MAP = {
    "Water": "#5fa8d3",
    "Soil": "#f4a261",
}