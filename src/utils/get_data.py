
import subprocess
import sys
from playwright.sync_api import sync_playwright, TimeoutError

from config import (ASNR_RADIATION_URL, 
                    METEOFRANCE_WEATHER_DOWNLOAD_URL, 
                    VILLEDEREVE_MUNICIPALITY_DOWNLOAD_URL,
                    TIMEOUT
)

def test():
    print(ASNR_RADIATION_BASE_URL)
    print(METEOFRANCE_WEATHER_DOWNLOAD_URL)
    print(VILLEDEREVE_MUNICIPALITY_DOWNLOAD_URL)


def install_playwright_browsers():
    """
    Installe les navigateurs requis par Playwright.
    À appeler après l'installation des dépendances Python (via requirements.txt).
    """
    try:
        # Vérifie que Playwright est installé (sinon, l'utilisateur doit d'abord installer les dépendances)
        import playwright
        print("Installation des navigateurs pour Playwright...")
        subprocess.run(["playwright", "install"], check=True)
        print("Navigateurs installés avec succès.")
    except ImportError:
        print(
            "Erreur : Playwright n'est pas installé. "
            "Veuillez d'abord exécuter `pip install -r requirements.txt`."
        )
        sys.exit(1)
    except subprocess.CalledProcessError as e:
        print(f"Erreur lors de l'installation des navigateurs : {e}")
        sys.exit(1)


def _safe_playwright_action(description, action):
    """Exécute une action Playwright en la journalisant et en gérant les erreurs."""
    print(f"\n➡️ {description}...")
    try:
        action()
        print(f"✅ {description} réussie.")
    except TimeoutError:
        print(f"⚠️ Timeout lors de : {description}")
    except Exception as e:
        print(f"⚠️ Erreur lors de {description} : {e}")


def _click_on_element(page, container_selector, button_selector, description):
    """
    Clique sur un élément identifié par un sélecteur.

    Args:
        page: L'objet Playwright Page.
        container_selector: Le sélecteur CSS de l'élément à attendre.
        button_selector: Le sélecteur CSS du bouton à cliquer.
        description: Description textuelle de l'action pour les logs.
    """
    def action():
        page.wait_for_selector(container_selector, timeout=TIMEOUT)
        button = page.locator(button_selector)
        button.click()
    _safe_playwright_action(description, action)


def _select_dropdown_option(page, container_selector, button_selector, option_list_selector, option_text, description):
    """
    Sélectionne une option dans un menu déroulant identifié par son conteneur.

    Args:
        page: L'objet Playwright Page.
        container_selector: Sélecteur CSS du conteneur parent (contenant le menu).
        button_selector: Sélecteur CSS du bouton de menu déroulant à cliquer.
        option_list_selector: Sélecteur CSS de la liste d’options (qui apparaît après clic).
        option_text: Texte exact de l’option à sélectionner.
        description: Description textuelle pour les logs.
    """
    def action():
        # Localiser le conteneur du menu
        container = page.locator(container_selector)
        container.wait_for(state="visible", timeout=10000)

        # Localiser et interagir avec le bouton déroulant
        button = container.locator(button_selector)
        button.click()
        options_list = container.locator(option_list_selector)
        options_list.wait_for(state="visible", timeout=10000)
        option = options_list.locator(f"li:has-text('{option_text}')")
        option.click()

    _safe_playwright_action(description, action)


def _fill_field(page, container_selector, field_selector, value, description):
    """
    Remplit un champ de formulaire avec une valeur donnée.

    Args:
        page: L'objet Playwright Page.
        container_selector: Sélecteur CSS du conteneur du champ.
        field_selector: Sélecteur CSS du champ à remplir.
        value: Valeur à entrer dans le champ.
        description: Description textuelle de l'action pour les logs.
    """
    def action():
        # Localiser le conteneur
        container = page.locator(container_selector)
        container.wait_for(state="visible", timeout=10000)

        # Localiser et interagir avec le champ
        field = container.locator(field_selector)        
        field.click()
        page.wait_for_timeout(TIMEOUT)  # Attendre un court délai si nécessaire
        field.fill("")  # Effacer le contenu existant
        field.fill(value)  # Remplir avec la nouvelle valeur
        field.press("Escape")  # Valider (si nécessaire)

    _safe_playwright_action(description, action)


def get_data_ASNR():
    """Télécharge les données de l'ANSR en interagissant avec la page web."""
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        page = browser.new_page()
        page.goto(ASNR_RADIATION_URL, wait_until="domcontentloaded", timeout=60000)

        # 1. Fermer la modale informative si elle est présente
        _click_on_element(page, 
                          "div.modal-content", 
                          "div.modal-content span.close", 
                          "Fermeture de la modale informative")
        
        # 2. Sélectionner le menu déroulant "Milieu de collecte" et choisir "Sol"
        _select_dropdown_option(page,
                                "div.row.container-select:has(div.label-select:has-text('Milieu de collecte'))",
                                ".selectric .button",
                                ".selectricItems",
                                "Sol",
                                "Sélection du milieu de collecte 'Sol'"
                                )

        # 3. Choisir la date de début de la sélection
        _fill_field(page,
                    "div.row.container-select:has(div.label-select:has-text('Date de début'))",
                    "input.form-control",
                    "01-janvier-2024",
                    "Saisie de la date de début de la sélection"
                    )
        # 4. Choisir la date de fin de la sélection
        _fill_field(page,
                    "div.row.container-select:has(div.label-select:has-text('Date de fin'))",
                    "input.form-control",
                    "01-janvier-2025",
                    "Saisie de la date de fin de la sélection"
                    )

        # 5. Refuser les cookies si la bannière est présente
        _click_on_element(page, 
                          "#tarteaucitronAlertBig",
                          "#tarteaucitronAllDenied2",
                          "Refus des cookies")

        # 6. Cliquer sur "Afficher les résultats"
        _click_on_element(page,
                          "div.row.container-select:has(button[ng-click='showResult()'])",
                          "button.btn.little-margin.middle-size.color-purple[ng-click='showResult()']",
                          "Clic sur 'Afficher les résultats'"
                          )
        
        # 7. Cliquer sur l'onglet "Téléchargement"
        _click_on_element(page,
                          "ul li:has-text('Téléchargement')",
                          "li[ng-click='showDownloadTree()']",
                          "Clic sur l'onglet 'Téléchargement'"
                          )
        
        # 8. Cliquer sur le bouton de téléchargement des données au format CSV


        # fin de fonction

