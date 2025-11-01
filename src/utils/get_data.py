from typing import Dict, Any
from playwright.sync_api import sync_playwright
from config import *
from src.utils.playwright_utils import *
from src.utils.utils import *


def get_all_data() -> None:
    """
    Download all necessary data: radiation, weather, and municipality data.
    
    This function orchestrates the download of all required datasets by calling
    the appropriate download functions with predefined configuration values.
    """

    # Clear the raw data directory
    delete_files_in_directory(DATA_RAW_DIR)

    # Download all required datasets
    get_radiation_data(
        radiation_config=RADIATION_DATA_CONFIG,
        asnr_radiation_url=ASNR_RADIATION_URL,
        initial_timeout=INITIAL_TIMEOUT
    )
    get_weather_data(
        data_raw_dir=DATA_RAW_DIR,
        meteofrance_weather_download_url=METEOFRANCE_WEATHER_DOWNLOAD_URL,
        weather_data_filename=WEATHER_DATA_FILENAME_GZ
    )
    get_municipality_data(
        villedereve_municipality_download_url=VILLEDEREVE_MUNICIPALITY_DOWNLOAD_URL,
        raw_data_dir=DATA_RAW_DIR,
        municipality_data_filename=MUNICIPALITY_DATA_FILENAME
    )



def get_radiation_data(
    radiation_config: Dict[str, Any],
    asnr_radiation_url: str,
    initial_timeout: int
) -> None:
    """
    Download radiation data from ASNR by interacting with the web page.
    
    This function uses Playwright to automate web browser interactions with the ASNR
    radiation measurement website. It handles modal dialogs, cookie banners, and 
    downloads data for multiple measurement environments (soil, water) across 
    different time periods.
    
    Args:
        radiation_config: Configuration dictionary containing medium types and 
            temporal subdivisions for data collection.
        asnr_radiation_url: URL of the ASNR radiation data website.
        initial_timeout: Initial timeout in milliseconds for page loading.
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
                # Start downloading the data
                start_downloading_data_playwright(page, get_radiation_data_filename(medium_name, start_date, end_date))

        # Close the browser
        browser.close()



def get_weather_data(
    data_raw_dir: str,
    meteofrance_weather_download_url: str,
    weather_data_filename: str
) -> str:
    """
    Download weather data from Météo-France and save it to the raw data directory.
    
    This function retrieves meteorological data from the Météo-France open data portal
    and saves it as a compressed CSV file in the specified directory.
    
    Args:
        data_raw_dir: Path to the raw data directory where the file will be saved.
        meteofrance_weather_download_url: URL to download the weather data from.
        weather_data_filename: Name of the file to save (including extension).
    
    Returns:
        str: Absolute path of the downloaded file.
    """
    return download_file_from_url(
        url=meteofrance_weather_download_url, 
        dest_folder=data_raw_dir,
        filename=weather_data_filename
    )


def get_municipality_data(
    villedereve_municipality_download_url: str,
    raw_data_dir: str,
    municipality_data_filename: str
) -> str:
    """
    Download municipality data from Ville de Rêve and save it to the raw data directory.
    
    This function retrieves French municipality information including names, coordinates,
    and population data, and saves it to the specified directory.
    
    Args:
        villedereve_municipality_download_url: URL to download the municipality data from.
        raw_data_dir: Path to the raw data directory where the file will be saved.
        municipality_data_filename: Name of the file to save (including extension).
    
    Returns:
        str: Absolute path of the downloaded file.
    """
    return download_file_from_url(
        villedereve_municipality_download_url,
        dest_folder=raw_data_dir,
        filename=municipality_data_filename
    )