import os
from typing import Dict, Any
from playwright.sync_api import sync_playwright
from config import (
    DATA_RAW_DIR,
    DATABASE_RAW_DIR,
    RADIATION_DATA_CONFIG,
    ASNR_RADIATION_URL,
    INITIAL_TIMEOUT,
    DATABASE_RAW_PATH,
    RADIATION_TABLE_PREFIX,
    WEATHER_DATA_FILENAME_GZ,
    METEOFRANCE_WEATHER_DOWNLOAD_URL,
    WEATHER_TABLE_NAME,
    VILLEDEREVE_MUNICIPALITY_DOWNLOAD_URL,
    MUNICIPALITY_DATA_FILENAME,
    MUNICIPALITY_TABLE_NAME,
    USE_OF_A_DATABASE,
    get_radiation_data_filename

)
from src.utils.utils import (
    delete_files_in_directory,
    download_file_from_url
)
from src.utils.playwright_utils import (
    install_playwright_browsers,
    close_modal,
    select_collection_environment,
    fill_start_date,
    fill_end_date,
    refuse_cookies,
    click_show_results,
    click_download_tab,
    start_downloading_data_playwright
)
from src.utils.db_utils import (
    save_csv_to_sqlite
)

def get_all_data() -> None:
    """
    Download all necessary data: radiation, weather, and municipality data.
    
    This function orchestrates the download of all required datasets by calling
    the appropriate download functions with predefined configuration values.
    """

    # Clear the raw data directory
    delete_files_in_directory(DATA_RAW_DIR)
    delete_files_in_directory(DATABASE_RAW_DIR)

    
    # Download all required datasets
    get_radiation_data(
        radiation_config=RADIATION_DATA_CONFIG,
        asnr_radiation_url=ASNR_RADIATION_URL,
        initial_timeout=INITIAL_TIMEOUT,
        db_path=DATABASE_RAW_PATH,
        table_prefix=RADIATION_TABLE_PREFIX,
        data_raw_dir=DATA_RAW_DIR
    )
    
    get_weather_data(
        data_raw_dir=DATA_RAW_DIR,
        weather_data_filename_gz=WEATHER_DATA_FILENAME_GZ,
        meteofrance_weather_download_url=METEOFRANCE_WEATHER_DOWNLOAD_URL,
        db_path=DATABASE_RAW_PATH,
        table_name=WEATHER_TABLE_NAME
    )
    
    get_municipality_data(
        villedereve_municipality_download_url=VILLEDEREVE_MUNICIPALITY_DOWNLOAD_URL,
        raw_data_dir=DATA_RAW_DIR,
        municipality_data_filename=MUNICIPALITY_DATA_FILENAME,
        db_path=DATABASE_RAW_PATH,
        table_name=MUNICIPALITY_TABLE_NAME
    )
    get_communes_geojson()

def get_communes_geojson():
    """
    Télécharge un GeoJSON (et non un TopoJSON) des communes de France
    et l'enregistre dans data/geodata/communes.geojson.

    Source: API officielle geo.api.gouv.fr (FeatureCollection GeoJSON)
    -> properties contient au moins: nom, code
    """
    import requests
    from pathlib import Path

    GEO_DIR = Path("data/geodata")
    GEO_PATH = GEO_DIR / "communes.geojson"
    GEO_URL = "https://www.data.gouv.fr/api/1/datasets/r/00c0c560-3ad1-4a62-9a29-c34c98c3701e"

    GEO_DIR.mkdir(parents=True, exist_ok=True)

    print(f"Téléchargement du GeoJSON des communes : {GEO_URL}")
    with requests.get(GEO_URL, stream=True, timeout=180) as r:
        r.raise_for_status()
        with open(GEO_PATH, "wb") as f:
            for chunk in r.iter_content(chunk_size=1 << 15):
                if chunk:
                    f.write(chunk)
    print(f"✓ Fichier GeoJSON enregistré dans {GEO_PATH}")


def get_radiation_data(
    radiation_config: Dict[str, Any],
    asnr_radiation_url: str,
    initial_timeout: int,
    db_path: str,
    table_prefix: str,
    data_raw_dir: str
) -> None:
    """
    Download radiation data from ASNR by interacting with the web page and save to SQLite.
    
    This function uses Playwright to automate web browser interactions with the ASNR
    radiation measurement website. It handles modal dialogs, cookie banners, and 
    downloads data for multiple measurement environments (soil, water) across 
    different time periods. Each downloaded dataset is saved as a CSV file and
    also stored in a separate SQLite table.
    
    Args:
        radiation_config: Configuration dictionary containing medium types and 
            temporal subdivisions for data collection.
        asnr_radiation_url: URL of the ASNR radiation data website.
        initial_timeout: Initial timeout in milliseconds for page loading.
        db_path: Path to the SQLite database file.
        table_prefix: Prefix for radiation table names in the database.
        data_raw_dir: Path to the raw data directory where the file will be saved.
    """

    # Install required Playwright browsers
    install_playwright_browsers()

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        page = browser.new_page()
        page.goto(asnr_radiation_url, wait_until="domcontentloaded", timeout=initial_timeout)
        
        # Close the informational modal if present
        close_modal(page)
        
        for medium_name, medium_info in radiation_config["medium"].items():
            medium_tag = medium_info["tag"]
            periods = medium_info["temporal_subdivisions"]

            # Process data in multiple periods to avoid exceeding the site's maximum allowed size
            for period in periods:
                start_date, end_date = period

                select_collection_environment(page, medium_tag)  # Select the collection environment
                fill_start_date(page, start_date)                # Set the start date of the selection
                fill_end_date(page, end_date)                    # Set the end date of the selection
                refuse_cookies(page)                             # Refuse cookies if the banner is present
                click_show_results(page)                         # Click on "Show results"
                click_download_tab(page)                         # Click on the "Download" tab
                
                # Get the filename for this period
                filename = get_radiation_data_filename(medium_name, start_date, end_date)
                
                # Start downloading the data and get the dataframe
                start_downloading_data_playwright(page, filename)

                if USE_OF_A_DATABASE:
                    # Get the full path to the downloaded CSV file
                    csv_file_path = os.path.join(data_raw_dir, filename)

                    # Save the dataframe to SQLite database
                    # Create a unique table name for each medium and period
                    table_name = f"{table_prefix}_{medium_name}_{start_date.replace('-', '')}_{end_date.replace('-', '')}"
                    save_csv_to_sqlite(
                        csv_path=csv_file_path,
                        db_path=db_path,
                        table_name=table_name,
                        compression=None  # Radiation CSV files are not compressed
                    )

        # Close the browser
        browser.close()


def get_weather_data(
    data_raw_dir: str,
    meteofrance_weather_download_url: str,
    weather_data_filename_gz: str,
    db_path: str,
    table_name: str,
    compression: str = 'gzip'
) -> None:
    """
    Download weather data from Météo-France, save it to the raw data directory,
    and load it into a SQLite database.
    
    This function retrieves meteorological data from the Météo-France open data portal,
    saves it as a compressed CSV file in the specified directory, and then loads
    the raw data into a SQLite database table.
    
    Args:
        data_raw_dir: Path to the raw data directory where the file will be saved.
        meteofrance_weather_download_url: URL to download the weather data from.
        weather_data_filename_gz: Name of the file to save (including extension).
        db_path: Path to the SQLite database file.
        table_name: Name of the table to create in the database.
    """
    
    # Download the file
    download_file_from_url(
        url=meteofrance_weather_download_url, 
        dest_folder=data_raw_dir,
        filename=weather_data_filename_gz
    )
    
    if USE_OF_A_DATABASE:
        # Save to SQLite database
        compression = compression
        save_csv_to_sqlite(
            csv_path=os.path.join(data_raw_dir, weather_data_filename_gz),
            db_path=db_path,
            table_name=table_name,
            compression=compression
        )

    # Delete the ZIP file
    os.remove(os.path.join(data_raw_dir, weather_data_filename_gz))


def get_municipality_data(
    villedereve_municipality_download_url: str,
    raw_data_dir: str,
    municipality_data_filename: str,
    db_path: str,
    table_name: str
) -> None:
    """
    Download municipality data from Ville de Rêve, save it to the raw data directory,
    and load it into a SQLite database.
    
    This function retrieves French municipality information including names, coordinates,
    and population data, saves it to the specified directory, and then loads the raw
    data into a SQLite database table.
    
    Args:
        villedereve_municipality_download_url: URL to download the municipality data from.
        raw_data_dir: Path to the raw data directory where the file will be saved.
        municipality_data_filename: Name of the file to save (including extension).
        db_path: Path to the SQLite database file.
        table_name: Name of the table to create in the database.
    
    """
    # Download the file
    file_path = download_file_from_url(
        villedereve_municipality_download_url,
        dest_folder=raw_data_dir,
        filename=municipality_data_filename
    )
    
    if USE_OF_A_DATABASE:
        # Save to SQLite database
        save_csv_to_sqlite(
            csv_path=file_path,
            db_path=db_path,
            table_name=table_name,
            sep=","
        )

if __name__ == "__main__":
    get_all_data()