import pandas as pd
from config import *
import glob
import os
import unidecode

def concatenate_radiation_data():
    # Récupération de tous les fichiers ASNR (sol, eau)
    asnr_files = glob.glob(os.path.join(DATA_RAW_DIR, "asnr_*_radiation_data_*.csv"))

    # Liste pour stocker les DataFrames
    dfs = []

    for file in asnr_files:
        # Extraire le nom du milieu depuis le nom du fichier
        file_name = os.path.basename(file)
        medium_name = file_name.split("_")[1]  # Ex: "asnr_soil_radiation_data_..." → "soil"

        # Charger le fichier CSV
        df = pd.read_csv(file, delimiter=";")

        # Ajouter la colonne "Milieu de collecte" en fonction du milieu détecté
        if medium_name in RADIATION_MEASUREMENT_ENVIRONMENTS:
            df["Milieu de collecte"] = RADIATION_MEASUREMENT_ENVIRONMENTS[medium_name]["tag"]
        else:
            df["Milieu de collecte"] = medium_name  # Cas par défaut si le milieu n'est pas dans le dictionnaire

        dfs.append(df)

    # Combinaison finale
    asnr_df = pd.concat(dfs, ignore_index=True)

    return asnr_df

    print(f"✅ Données de radiation ASNR concaténées : {asnr_df.shape[0]} lignes, {asnr_df.shape[1]} colonnes.")
    print(asnr_df.head())
    print(asnr_df["Milieu de collecte"].value_counts())
    print(asnr_df.info())




def clean_radiation_data(asnr_df: pd.DataFrame, config: dict) -> pd.DataFrame:
    # Suppression des lignes où les colonnes spécifiées sont manquantes
    asnr_df = asnr_df.dropna(subset=config["dropna_columns"])

    # Suppression des doublons
    asnr_df = asnr_df.drop_duplicates(
        subset=config["drop_duplicates_columns"],
        keep="first"
    )

    asnr_df[config["municipality_name"]] = asnr_df[config["municipality_name"]].str.replace(r"^L'", "", regex=True)

    # Sélection des colonnes à conserver
    asnr_df = asnr_df[config["required_columns"]]
    
    return asnr_df




def clean_municipality_data(mun_df: pd.DataFrame, config: dict) -> pd.DataFrame:
    # Normalisation du nom de commune : majuscules & sans accents
    mun_df[config["name_column"]["cleaned"]] = (
        mun_df[config["name_column"]["primary"]]
        .str.upper()
        .apply(unidecode.unidecode)
    )

    # Harmonisation des noms commençant par "L'"
    mun_df[config["name_column"]["cleaned"]] = mun_df[config["name_column"]["cleaned"]].str.replace(r"^L'", "", regex=True)

    # Création des colonnes latitude et longitude
    mun_df[config["latitude_columns"]["cleaned"]] = mun_df[config["latitude_columns"]["primary"]].fillna(
        mun_df[config["latitude_columns"]["fallback"]]
    )
    mun_df[config["longitude_columns"]["cleaned"]] = mun_df[config["longitude_columns"]["primary"]].fillna(
        mun_df[config["longitude_columns"]["fallback"]]
    )

    # Conserver la commune la plus peuplée par nom
    mun_df = (
        mun_df.sort_values(config["population_column"], ascending=False)
              .drop_duplicates(subset=config["name_column"]["cleaned"], keep="first")
    )

    # Sélection des colonnes pertinentes
    mun_df = mun_df[config["required_columns"]]

    print(f"✅ Données {mun_df.shape[0]} lignes, {mun_df.shape[1]} colonnes.")
    print(mun_df.head())
    print(mun_df.info())
    #return mun_df