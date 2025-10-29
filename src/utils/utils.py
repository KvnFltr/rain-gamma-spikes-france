import os
import urllib.request

def download_file_from_url(url: str, dest_folder: str = "data/raw", filename: str | None = None) -> str:
    """
    Télécharge un fichier depuis l'URL donnée et le place dans le dossier dest_folder.
    
    Args:
        url (str): L'URL du fichier à télécharger.
        dest_folder (str): Dossier de destination (par défaut 'data/raw').
        filename (str | None): Nom du fichier de sortie. Si None, utilise le nom de l'URL.
    
    Returns:
        str: Chemin absolu du fichier téléchargé.
    """
    # Création du dossier s'il n'existe pas
    os.makedirs(dest_folder, exist_ok=True)

    # Si aucun nom n’est donné, on récupère celui de l’URL
    if filename is None:
        filename = os.path.basename(url)
        if not filename:  # Si l'URL se termine par un slash
            filename = "downloaded_file"

    # Construction du chemin complet
    file_path = os.path.join(dest_folder, filename)

    # Téléchargement du fichier
    try:
        print(f"Téléchargement de {filename}...")
        
        
        with urllib.request.urlopen(url) as response:
            # Récupération de la taille prévue si dispo
            content_length = response.headers.get("Content-Length")
            if content_length:
                expected_size = int(content_length)
                print(f"Estimated file size : {expected_size / (1024**2):.2f} Mo")
            print("⏳ Please wait, downloading in progress...")

            with open(file_path, 'wb') as out_file:
                out_file.write(response.read())

        actual_size = os.path.getsize(file_path)
        print(f"✅ Fichier téléchargé : {file_path} ({actual_size / (1024**2):.2f} Ko)")

    except Exception as e:
        print(f"⚠️ Erreur lors du téléchargement : {e}")
        raise

    return os.path.abspath(file_path)



import os
import urllib.request
import gzip
import shutil

def download_file_from_url(url: str, dest_folder: str = "data/raw", filename: str | None = None) -> str:
    """
    Télécharge un fichier depuis l'URL donnée et le place dans le dossier dest_folder.
    Si le fichier est un .gz, il est automatiquement décompressé en .csv.
    
    Args:
        url (str): L'URL du fichier à télécharger.
        dest_folder (str): Dossier de destination (par défaut 'data/raw').
        filename (str | None): Nom du fichier de sortie. Si None, utilise le nom de l'URL.
    
    Returns:
        str: Chemin absolu du fichier téléchargé (ou décompressé si .gz).
    """
    # Création du dossier s'il n'existe pas
    os.makedirs(dest_folder, exist_ok=True)

    # Détermination du nom du fichier
    if filename is None:
        filename = os.path.basename(url) or "downloaded_file"

    file_path = os.path.join(dest_folder, filename)

    try:
        print(f"Téléchargement de {filename}...")

        with urllib.request.urlopen(url) as response:
            # Taille estimée
            content_length = response.headers.get("Content-Length")
            if content_length:
                expected_size = int(content_length)
                print(f"Taille estimée : {expected_size / (1024**2):.2f} Mo")
            print("⏳ Please wait, downloading in progress...")

            with open(file_path, "wb") as out_file:
                out_file.write(response.read())

        actual_size = os.path.getsize(file_path)
        print(f"✅ Fichier téléchargé : {file_path} ({actual_size / (1024**2):.2f} Mo)")

        # Décompression automatique si .gz
        if file_path.endswith(".gz"):
            decompressed_path = file_path[:-3]  # retire l'extension .gz
            print(f"⏳ Décompression du fichier gzip vers {decompressed_path} ...")
            with gzip.open(file_path, "rb") as f_in:
                with open(decompressed_path, "wb") as f_out:
                    shutil.copyfileobj(f_in, f_out)
            print("✅ Fichier décompressé avec succès.")
            os.remove(file_path)  # Optionnel : supprimer le .gz
            file_path = decompressed_path

    except Exception as e:
        print(f"⚠️ Erreur lors du téléchargement : {e}")
        raise

    return os.path.abspath(file_path)



