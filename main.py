from src.utils.get_data import *
from src.utils.clean_data import *

from config import *
import pandas as pd
def main():
    #print("=== Lancement du téléchargement des données ===")
    #get_all_data()
    #get_weather_data()
    #print("=== Fin du téléchargement des données ===")
    #concatenate_radiation_data()

    
    mun_raw = pd.read_csv("data/raw/villedereve_municipality_data.csv", delimiter=",")

    clean_municipality_data(mun_raw, CLEAN_MUNICIPALITY_DATA_CONFIG)

if __name__ == "__main__":
    main()