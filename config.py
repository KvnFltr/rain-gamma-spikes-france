from typing import Dict, List, Tuple

# API URLs
ASNR_RADIATION_URL: str = "https://mesure-radioactivite.fr/#/expert"
METEOFRANCE_WEATHER_DOWNLOAD_URL: str = "https://www.data.gouv.fr/api/1/datasets/r/92065ec0-ea6f-4f5e-8827-4344179c0a7f"
VILLEDEREVE_MUNICIPALITY_DOWNLOAD_URL: str = "https://www.data.gouv.fr/api/1/datasets/r/f5df602b-3800-44d7-b2df-fa40a0350325"

# Data directory paths
DATA_RAW_DIR: str = "data/raw"
DATA_CLEANED_DIR: str = "data/cleaned"

# Names of data files
WEATHER_DATA_FILENAME_GZ: str = "meteofrance_weather_data.csv.gz"
WEATHER_DATA_FILENAME: str = "meteofrance_weather_data.csv"
MUNICIPALITY_DATA_FILENAME: str = "villedereve_municipality_data.csv"
CLEANED_DATA_FILENAME: str = "data.csv"
RADIATION_DATA_FILENAME_PATTERN = "asnr_*_radiation_data_*.csv"

def get_radiation_data_filename(medium_name: str, start_date: str, end_date: str) -> str:
    return f"asnr_{medium_name}_radiation_data_{start_date}_to_{end_date}.csv"

# Timeout in milliseconds for Playwright actions
TIMEOUT: int = 10000
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