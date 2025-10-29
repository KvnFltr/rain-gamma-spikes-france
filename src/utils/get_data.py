from playwright.sync_api import sync_playwright, TimeoutError
from config import *
from src.utils.playwright_utils import *


def test():
    print(test_from_playwright_utils())
    print(ASNR_RADIATION_URL)
    print(METEOFRANCE_WEATHER_DOWNLOAD_URL)
    print(VILLEDEREVE_MUNICIPALITY_DOWNLOAD_URL)



def get_radiation_data():
    """Télécharge les données de l'ANSR en interagissant avec la page web."""

    # Installer les navigateurs requis par Playwright
    install_playwright_browsers()

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        page = browser.new_page()
        page.goto(ASNR_RADIATION_URL, wait_until="domcontentloaded", timeout=INITIAL_TIMEOUT)

        # Téléchargement des données de radiation du sol 
        get_soil_radiation_data(page)
        # généraliser pour d'autres types de données plus tard... (eau, air, etc.)
        
        # Fermer le navigateur
        browser.close()


def get_soil_radiation_data(page):
    
    close_modal(page)                          # 1. Fermer la modale informative si elle est présente
    select_collection_environment(page, "Sol") # 2. Sélectionner le menu déroulant "Milieu de collecte" et choisir "Sol"
    fill_start_date(page, "01-janvier-2024")   # 3. Choisir la date de début de la sélection
    fill_end_date(page, "01-janvier-2025")     # 4. Choisir la date de fin de la sélection
    refuse_cookies(page)                       # 5. Refuser les cookies si la bannière est présente
    click_show_results(page)                   # 6. Cliquer sur "Afficher les résultats"
    click_download_tab(page)                   # 7. Cliquer sur l'onglet "Téléchargement"
    
    # 8. Cliquer sur le bouton de téléchargement des données au format CSV
    start_downloading_data_playwright(page, "asnr_soil_radiation_data_2024.csv")
