
import subprocess
import sys

from config import (ASNR_RADIATION_BASE_URL, 
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


def _click_on_element(page, selector, button_selector, description):
    """
    Clique sur un élément identifié par un sélecteur.

    Args:
        page: L'objet Playwright Page.
        selector: Le sélecteur CSS de l'élément à attendre.
        button_selector: Le sélecteur CSS du bouton à cliquer.
        description: Description textuelle de l'action pour les logs.
    """

    def action():
        page.wait_for_selector(selector, timeout=TIMEOUT)
        button = page.locator(button_selector)
        button.click()
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
