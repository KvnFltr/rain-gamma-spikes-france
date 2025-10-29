from playwright.sync_api import sync_playwright
from config import *
from src.utils.playwright_utils import *
from src.utils.utils import download_file_from_url


def get_all_data():
    """Télécharge toutes les données nécessaires."""
    get_radiation_data()
    get_weather_data()
    get_municipality_data()

def get_radiation_data():
    """Télécharge les données de l'ANSR en interagissant avec la page web."""

    # Installer les navigateurs requis par Playwright
    install_playwright_browsers()

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        page = browser.new_page()
        page.goto(ASNR_RADIATION_URL, wait_until="domcontentloaded", timeout=INITIAL_TIMEOUT)

        close_modal(page) # Fermer la modale informative si elle est présente
        
        # Définitions des périodes de collecte pour chaque milieu
        # (Le téléchargement sur le site est limité en taille de fichier)
        soil_periods = [("01-janvier-2020", "01-janvier-2025")]
        water_periods = [
            ("01-janvier-2020", "01-janvier-2021"),
            ("01-janvier-2021", "01-janvier-2022"),
            ("01-janvier-2022", "01-janvier-2023"),
            ("01-janvier-2023", "01-janvier-2024"),
            ("01-janvier-2024", "01-janvier-2025")
        ]

        for medium in [("Sol", "soil"), ("Eau", "water")]:
            medium_tag, medium_name = medium
            
            if medium_tag == "Sol":
                periods = soil_periods
            else:
                periods = water_periods
            for period in periods:
                start_date, end_date = period

                select_collection_environment(page, medium_tag) # Selectionner le milieu de collecte
                fill_start_date(page, start_date)               # Choisir la date de début de la sélection
                fill_end_date(page, end_date)                   # Choisir la date de fin de la sélection
                refuse_cookies(page)                            # Refuser les cookies si la bannière est présente
                click_show_results(page)                        # Cliquer sur "Afficher les résultats"
                click_download_tab(page)                        # Cliquer sur l'onglet "Téléchargement"
                # Lancer le téléchargement des données
                start_downloading_data_playwright(page, f"asnr_{medium_name}_radiation_data_{start_date}_to_{end_date}.csv")

        # Fermer le navigateur
        browser.close()


def get_weather_data() -> str:
    """
    Télécharge les données météo depuis METEOFRANCE_WEATHER_DOWNLOAD_URL
    et les place dans data/raw.
    Returns:
        str: Chemin absolu du fichier téléchargé.
    """
    return download_file_from_url(
        METEOFRANCE_WEATHER_DOWNLOAD_URL, 
        dest_folder="data/raw", 
        filename="meteofrance_weather_data.csv.gz"
    )


def get_municipality_data() -> str:
    """
    Télécharge les données des municipalités depuis VILLEDEREVE_MUNICIPALITY_DOWNLOAD_URL
    et les place dans data/raw.
    Returns:
        str: Chemin absolu du fichier téléchargé.
    """
    return download_file_from_url(
        VILLEDEREVE_MUNICIPALITY_DOWNLOAD_URL,
        dest_folder="data/raw",
        filename="villedereve_municipality_data.csv"
    )

