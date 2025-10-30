import pandas as pd
import glob
import os

# Dossier contenant les fichiers bruts
raw_dir = "data/raw/"

# Récupération des fichiers ASNR
soil_files = glob.glob(os.path.join(raw_dir, "asnr_soil_radiation_data_*.csv"))
water_files = glob.glob(os.path.join(raw_dir, "asnr_water_radiation_data_*.csv"))

# Liste pour stocker les DataFrames
dfs = []

# Chargement fichiers sol
for file in soil_files:
    df = pd.read_csv(file, delimiter=";")
    df["Milieu de collecte"] = "Sol"
    dfs.append(df)

# Chargement fichiers eau
for file in water_files:
    df = pd.read_csv(file, delimiter=";")
    df["Milieu de collecte"] = "Eau"
    dfs.append(df)

# Combinaison finale
asnr_df = pd.concat(dfs, ignore_index=True)