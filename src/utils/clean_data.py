import pandas as pd
import glob
import os
import unidecode
from config import *
from src.utils.utils import *
import numpy as np
from sklearn.neighbors import BallTree

def clean_all_data():
    
    print("Concaténation des données de radiation...")
    radiation_df = concatenate_radiation_data(
        data_raw_dir=DATA_RAW_DIR,
        radiation_data_filename_pattern=RADIATION_DATA_FILENAME_PATTERN,
        config=RADIATION_DATA_CONFIG,
    )

    print("charg mun")
    mun_df = pd.read_csv("data/raw/villedereve_municipality_data.csv", delimiter=",")

    print("chargement du dataframe weather")
    weather_df_raw = pd.read_csv(os.path.join(DATA_RAW_DIR, "meteofrance_weather_data.csv"), sep=";")

    print("clean ansr")
    asnr_df = clean_radiation_data(asnr_df, RADIATION_DATA_CONFIG)

    print("clean mun")
    mun_df = clean_municipality_data(mun_df, MUNICIPALITY_DATA_CONFIG)

    print("fusion asnr, num")
    asnr_geo = geolocate_radiation_data(asnr_df, mun_df, RADIATION_DATA_CONFIG, MUNICIPALITY_DATA_CONFIG)
    
    print("clean weather")
    weather_df = clean_weather_data(weather_df_raw, WEATHER_DATA_CONFIG)
    
    print("chargement du df final")
    final_df = associate_weather_to_radiation(
        asnr_geo,
        weather_df,
        config_rad=RADIATION_DATA_CONFIG,
        config_weather=WEATHER_DATA_CONFIG,
        max_distance_m=50000  # 50 km
    )
    print("Sauvegarde du jeu de donnée nettoyé...")
    final_df.to_csv(os.path.join(DATA_CLEANED_DIR, "cleaned_df.csv"), sep=";",index=False)


def concatenate_radiation_data(
    data_raw_dir: str,
    radiation_data_filename_pattern: str,
    config: dict,
) -> pd.DataFrame:
    """
    Fonction dédiée à la concaténation des données de radiations,
    en utilisant la fonction générique.

    Args:
        data_raw_dir (str): Répertoire contenant les fichiers CSV.
        radiation_data_filename_pattern (str): Motif de nom de fichier pour la recherche.
        radiation_data_config (dict): Dictionnaire de configuration des données de radiations.
        radiation_measurement_environments (dict): Dictionnaire de mapping des milieux de mesure.

    Returns:
        pd.DataFrame: DataFrame concaténé des données de radiations.
    """
    
    return concatenate_csv_files(
        data_raw_dir=data_raw_dir,
        filename_pattern=radiation_data_filename_pattern,
        medium_column_name=config["measurement_environment_column"],
        medium_mapping=config["medium"],
    )




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
    radiation_data_config: dict,
    municipality_data_config: dict
) -> pd.DataFrame:
    print("Géolocalisation des données de radiation...")

    # Jointure
    merged_df = merge_dataframes(
        left_df=radiation_df,
        right_df=municipality_df,
        left_key=radiation_data_config["municipality_name"],
        right_key=municipality_data_config["name_column"]["cleaned"],
        how="left"
    )

    latitude_name = municipality_data_config["latitude_columns"]["cleaned"]
    longitude_name = municipality_data_config["longitude_columns"]["cleaned"]
    date_column = radiation_data_config["date_start_column"]

    # Vérification - combien de communes non matchées ?
    missing = merged_df[latitude_name].isna().sum()
    total = merged_df.shape[0]

    # Supprimer les lignes sans coordonnées géographiques
    merged_df = merged_df.dropna(subset=[latitude_name, longitude_name])
    
    # Supprimer la colonne ayant servie à la jointure
    merged_df = merged_df.drop(columns=[municipality_data_config["name_column"]["cleaned"]])
    
    # Transformation de la colonne de date en datetime
    merged_df[date_column] = pd.to_datetime(merged_df[date_column], errors="coerce")
    merged_df = merged_df.dropna(subset=[date_column])

    print(f"Jointure réalisée. Conservés : {total-missing}/{total} ({(total-missing)/total:.2%})")
    
    #merged_df.to_csv(os.path.join(DATA_CLEANED_DIR, "radiation_geo.csv"), sep=";",index=False) ########################## debug

    return merged_df


def clean_weather_data(weather_df: pd.DataFrame, config: dict) -> pd.DataFrame:
    # Sélection des colonnes
    weather_df = weather_df[config["required_columns"]]

    # Suppression des lignes où les données essentielles sont manquantes
    weather_df = weather_df.dropna(subset=config["dropna_columns"])

    
    # Multiplication des coordonnées Lambert par 100
    weather_df[config["lambert"]["x"]] *= 100
    weather_df[config["lambert"]["y"]] *= 100

    # Conversion coordonnées Lambert -> Latitude / Longitude
    weather_df = convert_lambert_to_wgs84(
        df=weather_df,
        x_col=config["lambert"]["x"],
        y_col=config["lambert"]["y"],
        lat_col=config["geo"]["lat"],
        lon_col=config["geo"]["lon"]
    )
    # Suppression des colonnes Lambert
    weather_df = weather_df.drop(columns=[config["lambert"]["x"], config["lambert"]["y"]])

    # Conversion de DATE en datetime (ex: 20200101 -> 2020-01-01)
    weather_df[config["date_column"]] = pd.to_datetime(
        weather_df[config["date_column"]].astype(str),
        format="%Y%m%d",
        errors="coerce"
    )
    weather_df = weather_df.dropna(subset=[config["date_column"]])
    

    #weather_df.to_csv(os.path.join(DATA_CLEANED_DIR, "weather.csv"), sep=";",index=False) ########################## debug
    
    return weather_df



def associate_weather_to_radiation(
    radiation_df,
    weather_df,
    config_rad,
    config_weather,
    max_distance_m=50000
):
    lat_rad = config_rad["latitude_columns"]["cleaned"]
    lon_rad = config_rad["longitude_columns"]["cleaned"]
    date_rad = config_rad["date_start_column"]

    lat_met = config_weather["geo"]["lat"]
    lon_met = config_weather["geo"]["lon"]
    date_met = config_weather["date_column"]
    snow_met = config_weather["snowfall_column"]
    rain_met = config_weather["rainfall_column"]
    
    dist_rad_met = config_rad["distance_to_nearest_weather_data"]

    # Rayon Terre pour conversion haversine
    R = 6371000

    # Ajouter colonnes résultat
    result_rows = []

    # Groupby météo par date pour éviter cross join massif
    weather_by_date = {
        d: df for d, df in weather_df.groupby(date_met)
    }
    
    # Boucle optimisée par date
    for day, subset_asnr in radiation_df.groupby(date_rad):

        if day not in weather_by_date:
            continue  # aucune station ce jour-là

        subset_weather = weather_by_date[day]

        # Convertir en radians
        weather_coords = np.vstack([
            np.radians(subset_weather[lat_met].values),
            np.radians(subset_weather[lon_met].values)
        ]).T

        radiation_coords = np.vstack([
            np.radians(subset_asnr[lat_rad].values),
            np.radians(subset_asnr[lon_rad].values)
        ]).T

        # BallTree Haversine
        tree = BallTree(weather_coords, metric='haversine')

        # Requête nearest neighbor
        dist, ind = tree.query(radiation_coords, k=1)
        dist_m = dist[:, 0] * R

        # Filtrer par distance max
        mask = dist_m <= max_distance_m
        valid_idx = np.where(mask)[0]

        for i in valid_idx:
            weather_row = subset_weather.iloc[ind[i][0]]
            asnr_row = subset_asnr.iloc[i]

            result = asnr_row.to_dict()
            result.update({
                f"{date_met}_METEO": weather_row[date_met],
                snow_met: weather_row[snow_met],
                rain_met: weather_row[rain_met],
                dist_rad_met: dist_m[i],
            })
            result_rows.append(result)

    result_df = pd.DataFrame(result_rows)

    print(f"✅ Association terminée : {len(result_df)}/{len(radiation_df)} conservés ({len(result_df)/len(radiation_df):.2%})")

    return result_df