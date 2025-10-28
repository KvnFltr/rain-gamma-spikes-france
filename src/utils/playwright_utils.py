import sys
import subprocess
from config import TIMEOUT
import zipfile
import os

def test_from_playwright_utils():
    print("hello from playwright_utils")


def install_playwright_browsers():
    """
    Installe les navigateurs requis par Playwright.
    À appeler après l'installation des dépendances Python (via requirements.txt).
    """
    try:
        # Vérifie que Playwright est installé (sinon, l'utilisateur doit d'abord installer les dépendances)
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


def click_on_element(page, container_selector, button_selector, description):
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


def select_dropdown_option(page, container_selector, button_selector, option_list_selector, option_text, description):
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
        container.wait_for(state="visible", timeout=2*TIMEOUT)

        # Localiser et interagir avec le bouton déroulant
        button = container.locator(button_selector)
        button.click()
        options_list = container.locator(option_list_selector)
        options_list.wait_for(state="visible", timeout=2*TIMEOUT)
        option = options_list.locator(f"li:has-text('{option_text}')")
        option.click()

    _safe_playwright_action(description, action)


def fill_field(page, container_selector, field_selector, value, description):
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
        container.wait_for(state="visible", timeout=2*TIMEOUT)

        # Localiser et interagir avec le champ
        field = container.locator(field_selector)        
        field.click()
        page.wait_for_timeout(TIMEOUT)  # Attendre un court délai si nécessaire
        field.fill("")  # Effacer le contenu existant
        field.fill(value)  # Remplir avec la nouvelle valeur
        field.press("Escape")  # Valider (si nécessaire)

    _safe_playwright_action(description, action)


def _extract_zip(zip_path, extract_to_dir, new_csv_name):
    """
    Extrait un fichier ZIP contenant un seul CSV, renomme le CSV extrait et supprime le ZIP.

    Args:
        zip_path (str): Chemin du fichier ZIP à extraire.
        extract_to_dir (str): Répertoire de destination.
        new_csv_name (str): Nouveau nom du fichier CSV final.
    """
    # Identifier le fichier CSV dans le ZIP et l'extraire
    with zipfile.ZipFile(zip_path, 'r') as zip_ref:
        csv_files = [name for name in zip_ref.namelist() if name.lower().endswith(".csv")]
    
        if not csv_files:
            raise FileNotFoundError("⚠️ Aucun fichier CSV trouvé dans le ZIP.")
        if len(csv_files) > 1:
            raise ValueError(f"⚠️ Plusieurs fichiers CSV trouvés dans le ZIP : {csv_files}")
        
        csv_file_in_zip = csv_files[0]

        extracted_csv_path = os.path.join(extract_to_dir, csv_file_in_zip)

    # Construire le chemin et renommer le fichier CSV
    new_csv_path = os.path.join(extract_to_dir, new_csv_name)
    os.rename(extracted_csv_path, new_csv_path)
    
    # Supprimer le fichier ZIP
    os.remove(zip_path)


def download_ASNR_data(page, button_selector, description):

    def action():
        # Localiser et cliquer sur le bouton de téléchargement
        page.wait_for_selector(button_selector, timeout=2*TIMEOUT)
        with page.expect_download() as download_info:
            page.locator(button_selector).click()
        download = download_info.value

        # Chemin pour sauvegarder le fichier téléchargé
        download_path = os.path.join("data", "raw", download.suggested_filename)
        
        # Sauvegarder le fichier ZIP téléchargé
        download.save_as(download_path)
        
        # Extraire et renommer le CSV, supprimer le ZIP
        new_csv_name = "data_ASNR_sol_2024.csv"
        extract_to_dir = os.path.join("data", "raw")
        _extract_zip(download_path, extract_to_dir, new_csv_name)

    _safe_playwright_action(description, action)
