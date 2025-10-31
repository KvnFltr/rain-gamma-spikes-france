from playwright.sync_api import sync_playwright
from config import *
from src.utils.playwright_utils import *
from src.utils.utils import download_file_from_url


def get_all_data():
    """Télécharge toutes les données nécessaires."""
    get_radiation_data(
        radiation_config=RADIATION_DATA_CONFIG,
        asnr_radiation_url=ASNR_RADIATION_URL,
        initial_timeout=INITIAL_TIMEOUT
    )
    get_weather_data(
        data_raw_dir=DATA_RAW_DIR,
        meteofrance_weather_download_url=METEOFRANCE_WEATHER_DOWNLOAD_URL,
        weather_data_filename=WEATHER_DATA_FILENAME
    )
    get_municipality_data(
        villedereve_municipality_download_url=VILLEDEREVE_MUNICIPALITY_DOWNLOAD_URL,
        raw_data_dir=DATA_RAW_DIR,
        municipality_data_filename=MUNICIPALITY_DATA_FILENAME
    )



def get_radiation_data(
    radiation_config: dict,
    asnr_radiation_url: str,
    initial_timeout: int
):
    """Télécharge les données de l'ANSR en interagissant avec la page web."""
     
    # Installer les navigateurs requis par Playwright
    install_playwright_browsers()

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        page = browser.new_page()
        page.goto(asnr_radiation_url, wait_until="domcontentloaded", timeout=initial_timeout)

        close_modal(page) # Fermer la modale informative si elle est présente
        
        
        for medium_name, medium_info in radiation_config["medium"].items():
            medium_tag = medium_info["tag"]
            periods = medium_info["temporal_subdivisions"]

            # Procéder en plusieurs périodes pour ne pas dépasser la taille maximale autorisée par le site
            for period in periods:
                start_date, end_date = period

                select_collection_environment(page, medium_tag) # Selectionner le milieu de collecte
                fill_start_date(page, start_date)               # Choisir la date de début de la sélection
                fill_end_date(page, end_date)                   # Choisir la date de fin de la sélection
                refuse_cookies(page)                            # Refuser les cookies si la bannière est présente
                click_show_results(page)                        # Cliquer sur "Afficher les résultats"
                click_download_tab(page)                        # Cliquer sur l'onglet "Téléchargement"
                # Lancer le téléchargement des données
                start_downloading_data_playwright(page, get_radiation_data_filename(medium_name, start_date, end_date))

        # Fermer le navigateur
        browser.close()


def get_weather_data(
    data_raw_dir: str,
    meteofrance_weather_download_url: str,
    weather_data_filename: str

) -> str:
    """
    Télécharge les données météo depuis METEOFRANCE_WEATHER_DOWNLOAD_URL
    et les place dans data/raw.
    à compléter (en anglais bien sûr)
    Returns:
        str: Chemin absolu du fichier téléchargé.
    """
    return download_file_from_url(
        url=meteofrance_weather_download_url, 
        dest_folder=data_raw_dir,
        filename=weather_data_filename
    )


def get_municipality_data(
    villedereve_municipality_download_url: str,
    raw_data_dir: str,
    municipality_data_filename: str
) -> str:
    """
    Télécharge les données des municipalités depuis VILLEDEREVE_MUNICIPALITY_DOWNLOAD_URL
    et les place dans data/raw.
    Returns:
        str: Chemin absolu du fichier téléchargé.
    """
    return download_file_from_url(
        villedereve_municipality_download_url,
        dest_folder=raw_data_dir,
        filename=municipality_data_filename
    )

