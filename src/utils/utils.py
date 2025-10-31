import os
import urllib.request
import gzip
import shutil
import pandas as pd
from pyproj import Transformer
import glob


def download_file_from_url(
    url: str, 
    dest_folder: str = "data/raw", 
    filename: str | None = None
) -> str:
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


def merge_dataframes(
    left_df: pd.DataFrame,
    right_df: pd.DataFrame,
    left_key: str,
    right_key: str,
    how: str = "left",
    suffixes: tuple = ("", "_right")
) -> pd.DataFrame:

    merged = left_df.merge(
        right_df,
        left_on=left_key,
        right_on=right_key,
        how=how,
        suffixes=suffixes
    )
    return merged



def concatenate_csv_files(
    data_raw_dir: str,
    filename_pattern: str,
    medium_column_name: str,
    medium_mapping: dict = None,
    delimiter: str = ";"
) -> pd.DataFrame:
    """
    Fonction générique pour concaténer plusieurs fichiers CSV en un seul DataFrame,
    en ajoutant une colonne indiquant le milieu de collecte.

    Args:
        data_raw_dir (str): Répertoire contenant les fichiers CSV.
        filename_pattern (str): Motif de nom de fichier pour la recherche.
        config (dict): Dictionnaire de configuration (ex: RADIATION_DATA_CONFIG).
        medium_column_name (str): Nom de la colonne à ajouter pour le milieu de collecte.
        medium_mapping (dict, optionnel): Dictionnaire de mapping des milieux.
        delimiter (str, optionnel): Délimiteur utilisé dans les fichiers CSV.

    Returns:
        pd.DataFrame: DataFrame concaténé.
    """
    
    # Récupération de tous les fichiers correspondants
    files = glob.glob(os.path.join(data_raw_dir, filename_pattern))
    dfs = []

    for file in files:
        # Extraire le nom du milieu depuis le nom du fichier
        file_name = os.path.basename(file)
        medium_name = file_name.split("_")[1]  # Ex: "asnr_soil_radiation_data_..." -> "soil"

        # Charger le fichier CSV
        df = pd.read_csv(file, delimiter=delimiter)

        # Ajouter la colonne "Milieu de collecte" en fonction du milieu détecté
        if medium_mapping and medium_name in medium_mapping:
            df[medium_column_name] = medium_mapping[medium_name]["tag"]
        else:
            df[medium_column_name] = medium_name  # Cas par défaut

        dfs.append(df)

    # Combinaison finale
    return pd.concat(dfs, ignore_index=True)


def convert_lambert_to_wgs84(df, x_col, y_col, lat_col, lon_col):
    # Conversion NTF Lambert II étendu -> WGS84 (vectorisé)
    transformer = Transformer.from_crs("EPSG:27572", "EPSG:4326", always_xy=True)

    df[lon_col], df[lat_col] = transformer.transform(
        df[x_col].values,
        df[y_col].values
    )

    return df