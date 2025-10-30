import sys
import subprocess
from config import *
import zipfile
import os
from playwright.sync_api import TimeoutError as PlaywrightTimeoutError

##################################

# Fonctions génériques Playwright 
 
##################################

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
        print("✅ Navigateurs installés avec succès.")
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
    print(f"\n{description}...")
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

def _check_if_element_visible(page, selector, timeout):
    """
    Vérifie si un élément est visible sur la page.

    Args:
        page: L'objet Playwright Page.
        selector: Le sélecteur CSS de l'élément.
        timeout: Temps maximum d'attente en millisecondes.

    Returns:
        bool: True si l'élément est visible, False sinon.
    """
    try:
        page.wait_for_selector(selector, state="visible", timeout=timeout)
        return True
    except PlaywrightTimeoutError:
        return False

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
        container.wait_for(state="visible", timeout=TIMEOUT)

        # Localiser et interagir avec le bouton déroulant
        button = container.locator(button_selector)
        button.click()
        options_list = container.locator(option_list_selector)
        options_list.wait_for(state="visible", timeout=TIMEOUT)
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
        container.wait_for(state="visible", timeout=TIMEOUT)

        # Localiser et interagir avec le champ
        field = container.locator(field_selector)        
        field.click()
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
    with zipfile.ZipFile(zip_path, 'r') as zip_ref:
        csv_files = [name for name in zip_ref.namelist() if name.lower().endswith(".csv")]

        if not csv_files:
            raise FileNotFoundError("⚠️ Aucun fichier CSV trouvé dans le ZIP.")
        if len(csv_files) > 1:
            raise ValueError(f"⚠️ Plusieurs fichiers CSV trouvés dans le ZIP : {csv_files}")

        csv_file_in_zip = csv_files[0]

        # Extraire le CSV dans le dossier de destination
        zip_ref.extract(csv_file_in_zip, path=extract_to_dir)

    # Construire les chemins complets
    extracted_csv_path = os.path.join(extract_to_dir, csv_file_in_zip)
    new_csv_path = os.path.join(extract_to_dir, new_csv_name)

    # Renommer le fichier CSV extrait
    os.rename(extracted_csv_path, new_csv_path)

    # Supprimer le fichier ZIP
    os.remove(zip_path)

def _click_on_download(page, button_selector, csv_name, destination_dir, description):

    def action():
        # Localiser et cliquer sur le bouton de téléchargement
        page.wait_for_selector(button_selector, timeout=TIMEOUT)
        with page.expect_download() as download_info:
            page.locator(button_selector).click()
        download = download_info.value

        # Chemin pour sauvegarder le fichier téléchargé
        download_path = os.path.join(destination_dir, download.suggested_filename)
        
        # Sauvegarder le fichier ZIP téléchargé
        download.save_as(download_path)
        
        # Extraire et renommer le CSV, supprimer le ZIP
        new_csv_name = csv_name
        _extract_zip(download_path, destination_dir, new_csv_name)

    _safe_playwright_action(description, action)

##############################

# Fonctions métier Playwright
 
##############################

def close_modal(page):
    _click_on_element(
        page, 
        SELECTORS["modal"]["container"], 
        SELECTORS["modal"]["button"], 
        "Fermeture de la modale informative"
    )

def select_collection_environment(page, environment_text):
    _select_dropdown_option(
        page,
        SELECTORS["collection_environment"]["container"],
        SELECTORS["collection_environment"]["button"],
        SELECTORS["collection_environment"]["options"],
        environment_text,
        f"Sélection du milieu de collecte '{environment_text}'"
    )

def fill_start_date(page, date):
    _fill_field(
        page,
        SELECTORS["dates"]["start"]["container"],
        SELECTORS["dates"]["start"]["input"],
        date,
        "Saisie de la date de début de la sélection"
    )

def fill_end_date(page, date):
    _fill_field(
        page,
        SELECTORS["dates"]["end"]["container"],
        SELECTORS["dates"]["end"]["input"],
        date,
        "Saisie de la date de fin de la sélection"
    )

def refuse_cookies(page):
    if _check_if_element_visible(page, SELECTORS["cookies"]["banner"], TIMEOUT_REFUSE_COOKIES):
        _click_on_element(
            page,
            SELECTORS["cookies"]["banner"],
            SELECTORS["cookies"]["refuse"],
            "Refus des cookies"
        )
    else:
        print("ℹ️ Bannière de cookies absente/déjà fermée.")
    
def click_show_results(page):
    _click_on_element(
        page,
        SELECTORS["results"]["container"],
        SELECTORS["results"]["button"],
        "Clic sur 'Afficher les résultats'"
    )


def click_download_tab(page):
    _click_on_element(
        page,
        SELECTORS["download"]["tab"]["container"],
        SELECTORS["download"]["tab"]["button"],
        "Clic sur l'onglet 'Téléchargement'"
    )

def start_downloading_data_playwright(page, csv_name):
    _click_on_download(
        page,
        SELECTORS["download"]["download_button"],
        csv_name,
        DATA_RAW_DIR,
        "Téléchargement des données au format CSV"
    )