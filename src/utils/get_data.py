from playwright.sync_api import sync_playwright, TimeoutError
from config import ASNR_RADIATION_URL, METEOFRANCE_WEATHER_DOWNLOAD_URL, VILLEDEREVE_MUNICIPALITY_DOWNLOAD_URL
from src.utils.playwright_utils import *


def test():
    print(test_from_playwright_utils())
    print(ASNR_RADIATION_URL)
    print(METEOFRANCE_WEATHER_DOWNLOAD_URL)
    print(VILLEDEREVE_MUNICIPALITY_DOWNLOAD_URL)



def get_data_ASNR():
    """Télécharge les données de l'ANSR en interagissant avec la page web."""
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        page = browser.new_page()
        page.goto(ASNR_RADIATION_URL, wait_until="domcontentloaded", timeout=60000)

        # 1. Fermer la modale informative si elle est présente
        click_on_element(page, 
                          "div.modal-content", 
                          "div.modal-content span.close", 
                          "Fermeture de la modale informative")
        
        # 2. Sélectionner le menu déroulant "Milieu de collecte" et choisir "Sol"
        select_dropdown_option(page,
                                "div.row.container-select:has(div.label-select:has-text('Milieu de collecte'))",
                                ".selectric .button",
                                ".selectricItems",
                                "Sol",
                                "Sélection du milieu de collecte 'Sol'")

        # 3. Choisir la date de début de la sélection
        fill_field(page,
                    "div.row.container-select:has(div.label-select:has-text('Date de début'))",
                    "input.form-control",
                    "01-janvier-2024",
                    "Saisie de la date de début de la sélection")
        # 4. Choisir la date de fin de la sélection
        fill_field(page,
                    "div.row.container-select:has(div.label-select:has-text('Date de fin'))",
                    "input.form-control",
                    "01-janvier-2025",
                    "Saisie de la date de fin de la sélection")

        # 5. Refuser les cookies si la bannière est présente
        click_on_element(page, 
                          "#tarteaucitronAlertBig",
                          "#tarteaucitronAllDenied2",
                          "Refus des cookies")

        # 6. Cliquer sur "Afficher les résultats"
        click_on_element(page,
                          "div.row.container-select:has(button[ng-click='showResult()'])",
                          "button.btn.little-margin.middle-size.color-purple[ng-click='showResult()']",
                          "Clic sur 'Afficher les résultats'")
        
        # 7. Cliquer sur l'onglet "Téléchargement"
        click_on_element(page,
                          "ul li:has-text('Téléchargement')",
                          "li[ng-click='showDownloadTree()']",
                          "Clic sur l'onglet 'Téléchargement'")
        
        # 8. Cliquer sur le bouton de téléchargement des données au format CSV
        download_ASNR_data(page, 
                            "button[ng-click='downloadTree()']", 
                            "Téléchargement des données ASNR au format CSV")

        # fin de fonction

