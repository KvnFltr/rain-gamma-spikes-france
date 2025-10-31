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
    
    print("=== Lancement du nettoyage des données ===")
    clean_all_data()
    print("=== Fin du nettoyage des données ===")
    
    print("charg rad")
    df_rad_geo = pd.read_csv("C:/Users/lubin/Documents/Git/rain-gamma-spikes-france/data/cleaned/radiation_geo.csv", delimiter=";")
    print("charg weather")
    df_weather = pd.read_csv("C:/Users/lubin/Documents/Git/rain-gamma-spikes-france/data/cleaned/weather.csv", delimiter=";")
    
    print("chargement du df final")
    final_df = associate_weather_to_radiation(
        df_rad_geo,
        df_weather,
        config_rad=RADIATION_DATA_CONFIG,
        config_weather=WEATHER_DATA_CONFIG,
        max_distance_m=50000  # 50 km
    )
    print(final_df.info())
    print(final_df.head())
    

if __name__ == "__main__":
    main()