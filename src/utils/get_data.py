
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

# à supprimer si on utilise _close_element
def _refuse_cookies_if_present(page):
    """Ferme le bandeau cookies s’il est affiché."""
    def action():
        page.wait_for_selector("#tarteaucitronAlertBig", timeout=5000)
        bouton = page.locator("#tarteaucitronAllDenied2")
        bouton.click()
    _safe_playwright_action("Refus des cookies", action)

# à supprimer si on utilise _close_element
def _close_modal_if_present(page, modal_name):
    """Ferme la modale de fusion ASN/IRSN si elle apparaît."""
    def action():
        page.wait_for_selector("div.modal-content", timeout=5000)
        bouton_fermer = page.locator("div.modal-content span.close")
        bouton_fermer.click()
    _safe_playwright_action("Fermeture de la modale 'Fusion ASN/IRSN'", action)

def _close_element(page, selector, button_selector, description):
    """Ferme un élément (bandeau, modale, etc.) s'il est présent sur la page.

    Args:
        page: L'objet Playwright Page.
        selector: Le sélecteur CSS de l'élément à fermer.
        button_selector: Le sélecteur CSS du bouton de fermeture à l'intérieur de l'élément.
        description: Description textuelle de l'élément pour les logs.
    """

    def action():
        page.wait_for_selector(selector, timeout=TIMEOUT)
        bouton_fermer = page.locator(button_selector)
        bouton_fermer.click()
    _safe_playwright_action(f"Fermeture de l'élément '{description}'", action)
