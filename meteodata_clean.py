import sys, os, csv, gzip, shutil, math
from pathlib import Path
from typing import Optional
import requests
import pandas as pd
from pyproj import Transformer, CRS


#URL de l’API pour le téléchargement de QUOT_SIM2_previous-2020-202509.csv.gz"
API_URL = "https://www.data.gouv.fr/api/1/datasets/r/92065ec0-ea6f-4f5e-8827-4344179c0a7f" 


#CHEMINS
DOWNLOADS = Path.home() / "Downloads"
DOWNLOAD_PATH = DOWNLOADS / "QUOT_SIM2_previous-2020-202509.csv.gz"  # le .gz téléchargé (pas celui latest 202509)
RAW_CSV_PATH = DOWNLOADS / "meteodata_raw.csv"        # CSV décompressé
OUTPUT_GZ = DOWNLOADS / "meteodata_full.csv.gz"       # CSV final (compressé)
LOG_PATH = DOWNLOADS / "meteodata_badlines.log"       # lignes invalides rencontrées

#PARAMS LECTURE
CHUNK_ROWS = 200_000     # taille des chunks (Il me semble que 200k soit un bon compromis mémoire/vitesse 16Go RAM)
SEP = ";"                # séparateur dans le CSV source
ENCODING = "utf-8"       # encodage du CSV source
NEED_COLS = ["LAMBX", "LAMBY", "DATE", "PRENEI", "PRELIQ"] # colonnesextraire (coordx, coordy, date, précipitations solides, liquides)
DTYPES = {
    "LAMBX": "float64",
    "LAMBY": "float64",
    "DATE": "Int64",     # entier nullable
    "PRENEI": "float64",
    "PRELIQ": "float64",
}

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
    print(f"\nFichier téléchargé: {dest} ({dest.stat().st_size/1e6:.1f} Mo)")

def check_gzip_integrity(gz_path: Path) -> int:
    """
    Tente une décompression 'à vide' pour vérifier l’intégrité gzip (CRC).
    Retourne le nombre d’octets décompressés (approx) sans écrire au disque.
    """
    total_out = 0
    with gzip.open(gz_path, "rb") as f:
        while True:
            chunk = f.read(1024 * 1024)
            if not chunk:
                break
            total_out += len(chunk)
    return total_out

def ensure_download():
    if not DOWNLOAD_PATH.exists():
        print(f"Téléchargement depuis l’API:\n{API_URL}")
        download(API_URL, DOWNLOAD_PATH)
    else:
        print(f"Fichier déjà présent: {DOWNLOAD_PATH} ({DOWNLOAD_PATH.stat().st_size/1e6:.1f} Mo)")
    # Vérif GZIP
    print("Vérification intégrité GZIP… (CRC)")
    out_bytes = check_gzip_integrity(DOWNLOAD_PATH)
    print(f"OK: décompression testée ~{out_bytes/1e6:.1f} Mo (non écrit sur disque)")

def stream_transform():
    """
    Lecture en chunks depuis le .gz, transformation, et écriture en .gz de sortie.
    Tolérance aux lignes invalides, log dans LOG_PATH.
    """
    # Prépare sortie gzip texte
    if OUTPUT_GZ.exists():
        OUTPUT_GZ.unlink()
    if LOG_PATH.exists():
        LOG_PATH.unlink()

    crs_src = CRS.from_epsg(27572)   # Lambert II étendu (Ce que Lubin à recommandé)
    crs_tgt = CRS.from_epsg(4326)    # WGS84
    transformer = Transformer.from_crs(crs_src, crs_tgt, always_xy=True)

    # On utilise le moteur 'python' pour une meilleure tolérance sur gros CSV
    # chunksize + compression='gzip' permettent la décompression streamée
    total_rows_in = 0
    total_rows_out = 0
    bad_lines_count = 0
    wrote_header = False

    # IMPORTANT: on force usecols pour ne pas charger inutilement des colonnes
    # et on fixe dtype pour éviter les surprises de typage
    reader = pd.read_csv(
        DOWNLOAD_PATH,
        sep=SEP,
        compression="gzip",
        encoding=ENCODING,
        usecols=lambda c: (c in NEED_COLS),   # retient seulement les colonnes utiles
        dtype=DTYPES,
        engine="python",                      # plus robuste aux irrégularités
        on_bad_lines="warn",                  # loggue les lignes mauvaises
        chunksize=CHUNK_ROWS
    )

    with gzip.open(OUTPUT_GZ, "wt", encoding="utf-8", newline="") as gz_out, \
         open(LOG_PATH, "w", encoding="utf-8") as flog:
        writer = None

        for i, chunk in enumerate(reader, start=1):
            before = len(chunk)
            total_rows_in += before

            # Log des warnings de pandas (on_bad_lines="warn") ne donne pas les lignes elles-mêmes,
            # donc on ne peut que noter l’écart si jamais on perdait des lignes ici.

            # Filtre lignes nulles nécessaires
            chunk = chunk.dropna(subset=["LAMBX", "LAMBY", "DATE"])
            if chunk.empty:
                continue

            # Projection Lambert -> lon/lat (numpy vectorisé)
            lons, lats = transformer.transform(chunk["LAMBX"].to_numpy(), chunk["LAMBY"].to_numpy())
            chunk["lon"] = lons
            chunk["lat"] = lats

            # Date YYYYMMDD -> ISO
            # On garde DATE en string pour éviter les conversions foireuses (ex: 20240101)
            chunk["DATE"] = chunk["DATE"].astype("Int64").astype("string")
            chunk["date_iso"] = pd.to_datetime(chunk["DATE"], format="%Y%m%d", errors="coerce").dt.strftime("%Y-%m-%d")

            out = chunk[["lon", "lat", "date_iso", "PRENEI", "PRELIQ"]].copy()

            # Écriture incrémentale dans le .gz final
            out.to_csv(
                gz_out,
                index=False,
                sep=";",
                header=not wrote_header
            )
            wrote_header = True
            total_rows_out += len(out)

            sys.stdout.write(f"\rChunks traités: {i}  |  in: {total_rows_in:,}  → out: {total_rows_out:,}")
            sys.stdout.flush()

    print()
    print(f"Terminé: {OUTPUT_GZ}  |  lignes écrites: {total_rows_out:,}")
    print(f"(Entrées lues ≈ {total_rows_in:,})")
    if bad_lines_count:
        print(f"Lignes problématiques loguées dans: {LOG_PATH}")

def main():
    ensure_download()
    stream_transform()

if __name__ == "__main__":
    main()
