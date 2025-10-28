
import os
import sys
import requests
import pandas as pd
from pyproj import Transformer, CRS

API_URL = "https://www.data.gouv.fr/api/1/datasets/r/92065ec0-ea6f-4f5e-8827-4344179c0a7f"
DOWNLOAD_PATH = "data/QUOT_SIM2_latest-20250901-20251020.csv.gz"
OUTPUT_PATH = "output/meteodata_full.csv.gz"

def download(url: str, dest: str, chunk_size: int = 1_048_576):
    os.makedirs(os.path.dirname(dest), exist_ok=True)
    with requests.get(url, stream=True, timeout=120) as r:
        r.raise_for_status()
        total = int(r.headers.get("content-length", 0))
        done = 0
        with open(dest, "wb") as f:
            for ch in r.iter_content(chunk_size=chunk_size):
                if ch:
                    f.write(ch)
                    done += len(ch)
                    if total:
                        pct = done * 100 // total
                        sys.stdout.write(f"\rTéléchargement: {pct}% ({done/1e6:.1f}/{total/1e6:.1f} Mo)")
                        sys.stdout.flush()
    print(f"\nFichier téléchargé: {dest}")

def main():
    # 1) Télécharger si absent
    if not os.path.exists(DOWNLOAD_PATH):
        print(f"Téléchargement depuis l’API:\n{API_URL}")
        download(API_URL, DOWNLOAD_PATH)
    else:
        print(f"Fichier déjà présent: {DOWNLOAD_PATH}")

    # 2) Lecture du CSV.gz complet (séparateur ;)
    print("Lecture du CSV.gz complet…")
    df = pd.read_csv(DOWNLOAD_PATH, sep=";", compression="gzip", low_memory=False)

    # 3) Vérifications colonnes (en MAJ)
    for col in ["LAMBX", "LAMBY", "DATE", "PRENEI", "PRELIQ"]:
        if col not in df.columns:
            raise RuntimeError(f"Colonne manquante dans le CSV: {col}")

    # 4) Conversion Lambert II étendu -> WGS84
    crs_src = CRS.from_epsg(27572)  # NTF Lambert II étendu
    crs_tgt = CRS.from_epsg(4326)   # WGS84
    transformer = Transformer.from_crs(crs_src, crs_tgt, always_xy=True)

    print("Conversion coordonnées → lon/lat…")
    lons, lats = transformer.transform(df["LAMBX"].values, df["LAMBY"].values)
    df["lon"] = lons
    df["lat"] = lats

    # 5) Date lisible
    print("Formatage des dates…")
    df["date_iso"] = pd.to_datetime(df["DATE"].astype(str), format="%Y%m%d", errors="coerce").dt.strftime("%Y-%m-%d")

    # 6) Colonnes finales
    out = df[["lon", "lat", "date_iso", "PRENEI", "PRELIQ"]].copy()

    # 7) Écriture CSV.gz
    os.makedirs(os.path.dirname(OUTPUT_PATH), exist_ok=True)
    out.to_csv(OUTPUT_PATH, index=False, compression="gzip")
    print(f"Terminé: {OUTPUT_PATH} (lignes: {len(out)})")

if __name__ == "__main__":
    main()
