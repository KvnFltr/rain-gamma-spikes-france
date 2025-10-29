import sys
import requests
import pandas as pd
from pyproj import Transformer, CRS
from pathlib import Path

API_URL = "https://www.data.gouv.fr/api/1/datasets/r/92065ec0-ea6f-4f5e-8827-4344179c0a7f"

DOWNLOADS = Path.home() / "Downloads"
DOWNLOAD_PATH = DOWNLOADS / "QUOT_SIM2_latest-20250901-20251020.csv.gz"
OUTPUT_GZ = DOWNLOADS / "meteodata_full.csv.gz"  # <-- seul fichier produit

def download(url: str, dest: Path, chunk_size: int = 1_048_576):
    dest.parent.mkdir(parents=True, exist_ok=True)
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
    # 1) Télécharger dans Téléchargements si absent
    if not DOWNLOAD_PATH.exists():
        print(f"Téléchargement depuis l’API:\n{API_URL}")
        download(API_URL, DOWNLOAD_PATH)
    else:
        print(f"Fichier déjà présent: {DOWNLOAD_PATH}")

    # 2) Lecture du CSV.gz complet
    print("Lecture du CSV.gz…")
    df = pd.read_csv(DOWNLOAD_PATH, sep=";", compression="gzip", low_memory=False)

    # 3) Vérif colonnes
    for col in ["LAMBX", "LAMBY", "DATE", "PRENEI", "PRELIQ"]:
        if col not in df.columns:
            raise RuntimeError(f"Colonne manquante: {col}")

    # 4) Lambert II étendu -> WGS84
    crs_src = CRS.from_epsg(27572)
    crs_tgt = CRS.from_epsg(4326)
    transformer = Transformer.from_crs(crs_src, crs_tgt, always_xy=True)
    print("Conversion coordonnées → lon/lat…")
    lons, lats = transformer.transform(df["LAMBX"].values, df["LAMBY"].values)
    df["lon"] = lons
    df["lat"] = lats

    # 5) Date lisible
    print("Formatage des dates…")
    df["date_iso"] = pd.to_datetime(df["DATE"].astype(str), format="%Y%m%d", errors="coerce").dt.strftime("%Y-%m-%d")

    # 6) Colonnes finales (pluie = PRELIQ, neige = PRENEI)
    out = df[["lon", "lat", "date_iso", "PRENEI", "PRELIQ"]].copy()

    # 7) Sauvegarde UNIQUE (compressée) dans Téléchargements
    out.to_csv(OUTPUT_GZ, index=False, compression="gzip", sep=";", encoding="utf-8")
    print(f"Terminé: {OUTPUT_GZ} — lignes: {len(out)}")

if __name__ == "__main__":
    main()