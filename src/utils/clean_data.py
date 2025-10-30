import pandas as pd
import glob
import os
import unidecode
from config import *
from src.utils.utils import *

def concatenate_radiation_data():
    # Récupération de tous les fichiers ASNR (sol, eau)
    asnr_files = glob.glob(os.path.join(DATA_RAW_DIR, RADIATION_DATA_FILENAME_PATTERN))

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
    radiation_df = pd.concat(dfs, ignore_index=True)

    return radiation_df



def clean_radiation_data(radiation_df: pd.DataFrame, config: dict) -> pd.DataFrame:
    # Suppression des lignes où les colonnes spécifiées sont manquantes
    radiation_df = radiation_df.dropna(subset=config["dropna_columns"])

    # Suppression des doublons
    radiation_df = radiation_df.drop_duplicates(
        subset=config["drop_duplicates_columns"],
        keep="first"
    )
    
    # Normalisation du nom des communes
    radiation_df[config["municipality_name"]] = (
        radiation_df[config["municipality_name"]]
        .str.upper()
        .apply(unidecode.unidecode)
    )
    radiation_df[config["municipality_name"]] = radiation_df[config["municipality_name"]].str.replace(r"^L'", "", regex=True)


    # Sélection des colonnes à conserver
    radiation_df = radiation_df[config["required_columns"]]

    return radiation_df

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
    return mun_df




def geolocate_radiation_data(
    radiation_df: pd.DataFrame,
    municipality_df: pd.DataFrame,
    config_rad: dict,
    config_mun: dict
) -> pd.DataFrame:
    print("Géolocalisation des données de radiation...")

    # Jointure
    merged_df = merge_dataframes(
        left_df=radiation_df,
        right_df=municipality_df,
        left_key=config_rad["municipality_name"],
        right_key=config_mun["name_column"]["cleaned"],
        how="left"
    )

    latitude_name = config_mun["latitude_columns"]["cleaned"]
    longitude_name = config_mun["longitude_columns"]["cleaned"]

    # Vérification - combien de communes non matchées ?
    missing = merged_df[latitude_name].isna().sum()
    total = merged_df.shape[0]

    # Supprimer les lignes sans coordonnées géographiques
    merged_df = merged_df.dropna(subset=[latitude_name, longitude_name])
    
    # Supprimer la colonne ayant servie à la jointure
    merged_df = merged_df.drop(columns=[config_mun["name_column"]["cleaned"]])
    
    print(f"Jointure réalisée. Taux de perte : {missing}/{total} ({missing/total:.2%})")
    
    return merged_df

def clean_weather_data(weather_df: pd.DataFrame, config: dict) -> pd.DataFrame:
    # Sélection des colonnes
    weather_df = weather_df[config["required_columns"]]

    print("suppr nan")
    # Suppression des lignes où les données essentielles sont manquantes
    weather_df = weather_df.dropna(subset=config["dropna_columns"])

    print("conv lambert")
    # Conversion coordonnées Lambert -> Latitude / Longitude
    weather_df = convert_lambert_to_wgs84(
        df=weather_df,
        x_col=config["lambert"]["x"],
        y_col=config["lambert"]["y"],
        lat_col=config["geo"]["lat"],
        lon_col=config["geo"]["lon"]
    )
    print("suppr lamb")
    # Suppression des colonnes Lambert
    weather_df = weather_df.drop(columns=[config["lambert"]["x"], config["lambert"]["y"]])
    
    print("conv de la date en datetime")
    # Conversion de DATE en datetime (ex: 20200101 -> 2020-01-01)
    weather_df[config["date_column"]] = pd.to_datetime(
        weather_df[config["date_column"]].astype(str),
        format="%Y%m%d",
        errors="coerce"
    )
    weather_df = weather_df.dropna(subset=[config["date_column"]])
    
    print(weather_df.info())
    print(weather_df.head())

    return weather_df