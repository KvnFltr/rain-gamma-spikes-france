from src.utils.get_data import *
from src.utils.clean_data import *

from config import *
import pandas as pd
import os

def main():
    #print("=== Lancement du téléchargement des données ===")
    #get_all_data()
    #get_weather_data()
    #print("=== Fin du téléchargement des données ===")
    #concatenate_radiation_data()

    #asnr_df = concatenate_radiation_data()
    #asnr_df = clean_radiation_data(asnr_df, CLEAN_RADIATION_DATA_CONFIG)
    
    #mun_df = pd.read_csv("data/raw/villedereve_municipality_data.csv", delimiter=",")
    #mun_df = clean_municipality_data(mun_df, CLEAN_MUNICIPALITY_DATA_CONFIG)

    #geolocate_radiation_data(asnr_df, mun_df, CLEAN_RADIATION_DATA_CONFIG, CLEAN_MUNICIPALITY_DATA_CONFIG)
    print("chargement du dataframe")
    weather_df_raw = pd.read_csv(os.path.join(DATA_RAW_DIR, "meteofrance_weather_data.csv"), sep=";")
    print("done")
    weather_df = clean_weather_data(weather_df_raw, WEATHER_DATA_CONFIG)

if __name__ == "__main__":
    main()