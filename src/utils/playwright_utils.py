import sys
import subprocess
import zipfile
import os
from typing import Callable
from playwright.sync_api import Page, TimeoutError as PlaywrightTimeoutError
from config import *


##############################
# Generic Playwright functions
##############################


def install_playwright_browsers() -> None:
    """
    Install browsers required by Playwright.
    
    This function should be called after installing Python dependencies (via requirements.txt).
    It installs the necessary browser binaries for Playwright automation.
    
    Raises:
        SystemExit: If Playwright is not installed or if browser installation fails.
    """
    try:
        # Check that Playwright is installed
        print("Installing browsers for Playwright...")
        subprocess.run(["playwright", "install"], check=True)
        print("✅ Browsers installed successfully.")
    except ImportError:
        print(
            "Error: Playwright is not installed."
            "Please run `pip install -r requirements.txt` first."
        )
        sys.exit(1)
    except subprocess.CalledProcessError as e:
        print(f"Error during browser installation: {e}")
        sys.exit(1)


def _safe_playwright_action(description: str, action: Callable[[], None]) -> None:
    """
    Execute a Playwright action with logging and error handling.
    
    Args:
        description: Description of the action being performed.
        action: Callable function that performs the Playwright action.
    """
    print(f"\n{description}...")
    try:
        action()
        print(f"✅ {description} successful.")
    except TimeoutError:
        print(f"⚠️ Timeout during: {description}")
    except Exception as e:
        print(f"⚠️ Error during {description}: {e}")


def _click_on_element(
    page: Page,
    container_selector: str,
    button_selector: str,
    description: str,
    timeout: int
) -> None:
    """
    Click on an element identified by a selector.

    Args:
        page: The Playwright Page object.
        container_selector: CSS selector of the element to wait for.
        button_selector: CSS selector of the button to click.
        description: Textual description of the action for logging.
        timeout: Maximum wait time in milliseconds.
    """
    def action() -> None:
        page.wait_for_selector(container_selector, timeout=timeout)
        button = page.locator(button_selector)
        button.click()
    _safe_playwright_action(description, action)


def _check_if_element_visible(
    page: Page, 
    selector: str, 
    timeout: int
) -> bool:
    """
    Check if an element is visible on the page.

    Args:
        page: The Playwright Page object.
        selector: CSS selector of the element.
        timeout: Maximum wait time in milliseconds.

    Returns:
        bool: True if the element is visible, False otherwise.
    """
    try:
        page.wait_for_selector(selector, state="visible", timeout=timeout)
        return True
    except PlaywrightTimeoutError:
        return False

def _select_dropdown_option(
    page: Page,
    container_selector: str,
    button_selector: str,
    option_list_selector: str,
    option_text: str,
    description: str,
    timeout: int
) -> None:
    """
    Select an option in a dropdown menu identified by its container.

    Args:
        page: The Playwright Page object.
        container_selector: CSS selector of the parent container (containing the menu).
        button_selector: CSS selector of the dropdown button to click.
        option_list_selector: CSS selector of the options list (appears after clicking).
        option_text: Exact text of the option to select.
        description: Textual description for logging.
        timeout: Maximum wait time in milliseconds.
    """
    def action() -> None:
        # Locate the menu container
        container = page.locator(container_selector)
        container.wait_for(state="visible", timeout=timeout)

        # Locate and interact with the dropdown button
        button = container.locator(button_selector)
        button.click()
        options_list = container.locator(option_list_selector)
        options_list.wait_for(state="visible", timeout=timeout)
        option = options_list.locator(f"li:has-text('{option_text}')")
        option.click()

    _safe_playwright_action(description, action)


def _fill_field(
    page: Page,
    container_selector: str,
    field_selector: str,
    value: str,
    description: str,
    timeout: int
) -> None:
    """
    Fill a form field with a given value.

    Args:
        page: The Playwright Page object.
        container_selector: CSS selector of the field container.
        field_selector: CSS selector of the field to fill.
        value: Value to enter in the field.
        description: Textual description of the action for logging.
        timeout: Maximum wait time in milliseconds.
    """
    def action() -> None:
        # Locate the container
        container = page.locator(container_selector)
        container.wait_for(state="visible", timeout=timeout)

        # Locate and interact with the field
        field = container.locator(field_selector)        
        field.click()
        field.fill("")  # Clear existing content
        field.fill(value)  # Fill with new value
        field.press("Escape")

    _safe_playwright_action(description, action)


def _extract_zip(
    zip_path: str, 
    extract_to_dir: str, 
    new_csv_name: str
) -> None:
    """
    Extract a ZIP file containing a single CSV, rename the extracted CSV, and delete the ZIP.

    Args:
        zip_path: Path to the ZIP file to extract.
        extract_to_dir: Destination directory.
        new_csv_name: New name for the final CSV file.
        
    Raises:
        FileNotFoundError: If no CSV file is found in the ZIP.
        ValueError: If multiple CSV files are found in the ZIP.
    """
    with zipfile.ZipFile(zip_path, 'r') as zip_ref:
        csv_files = [name for name in zip_ref.namelist() if name.lower().endswith(".csv")]

        if not csv_files:
            raise FileNotFoundError("⚠️ No CSV file found in the ZIP.")
        if len(csv_files) > 1:
            raise ValueError(f"⚠️ Multiple CSV files found in the ZIP: {csv_files}")

        csv_file_in_zip = csv_files[0]

        # Extract the CSV to the destination folder
        zip_ref.extract(csv_file_in_zip, path=extract_to_dir)

    # Build complete paths
    extracted_csv_path = os.path.join(extract_to_dir, csv_file_in_zip)
    new_csv_path = os.path.join(extract_to_dir, new_csv_name)

    # Rename the extracted CSV file
    os.rename(extracted_csv_path, new_csv_path)

    # Delete the ZIP file
    os.remove(zip_path)


def _click_on_download(
    page: Page,
    button_selector: str,
    csv_name: str,
    destination_dir: str,
    description: str,
    timeout: int
) -> None:
    """
    Click on a download button, save the file, extract it if it's a ZIP, and clean up.

    Args:
        page: The Playwright Page object.
        button_selector: CSS selector of the download button.
        csv_name: Name for the final CSV file.
        destination_dir: Directory where the file should be saved.
        description: Textual description of the action for logging.
    """
    def action() -> None:
        # Locate and click on the download button
        page.wait_for_selector(button_selector, timeout=timeout)
        with page.expect_download() as download_info:
            page.locator(button_selector).click()
        download = download_info.value

        # Path to save the downloaded file
        download_path = os.path.join(destination_dir, download.suggested_filename)
        
        # Save the downloaded ZIP file
        download.save_as(download_path)
        
        # Extract and rename the CSV, delete the ZIP
        new_csv_name = csv_name
        _extract_zip(download_path, destination_dir, new_csv_name)

    _safe_playwright_action(description, action)


########################################
# Business-specific Playwright functions
########################################

def close_modal(page: Page) -> None:
    """
    Close the informational modal dialog.
    
    Args:
        page: The Playwright Page object.
    """
    _click_on_element(
        page=page,
        container_selector=SELECTORS["modal"]["container"], 
        button_selector=SELECTORS["modal"]["button"], 
        description="Closing informational modal",
        timeout=TIMEOUT
    )


def select_collection_environment(page: Page, environment_text: str) -> None:
    """
    Select the collection environment from the dropdown menu.
    
    Args:
        page: The Playwright Page object.
        environment_text: Text of the environment option to select (e.g., "Sol", "Eau").
    """
    _select_dropdown_option(
        page=page,
        container_selector=SELECTORS["collection_environment"]["container"],
        button_selector=SELECTORS["collection_environment"]["button"],
        option_list_selector=SELECTORS["collection_environment"]["options"],
        option_text=environment_text,
        description=f"Selecting collection environment '{environment_text}'",
        timeout=TIMEOUT
    )


def fill_start_date(page: Page, date: str) -> None:
    """
    Fill the start date field for data selection.
    
    Args:
        page: The Playwright Page object.
        date: Start date string to enter.
    """
    _fill_field(
        page=page,
        container_selector=SELECTORS["dates"]["start"]["container"],
        field_selector=SELECTORS["dates"]["start"]["input"],
        value=date,
        description="Entering start date for selection",
        timeout=TIMEOUT
    )


def fill_end_date(page: Page, date: str) -> None:
    """
    Fill the end date field for data selection.
    
    Args:
        page: The Playwright Page object.
        date: End date string to enter.
    """
    _fill_field(
        page=page,
        container_selector=SELECTORS["dates"]["end"]["container"],
        field_selector=SELECTORS["dates"]["end"]["input"],
        value=date,
        description="Entering end date for selection",
        timeout=TIMEOUT
    )


def refuse_cookies(page: Page) -> None:
    """
    Refuse cookies if the cookie banner is visible.
    
    Args:
        page: The Playwright Page object.
    """
    if _check_if_element_visible(page, SELECTORS["cookies"]["banner"], TIMEOUT_REFUSE_COOKIES):
        _click_on_element(
            page=page,
            container_selector=SELECTORS["cookies"]["banner"],
            button_selector=SELECTORS["cookies"]["refuse"],
            description="Refusing cookies",
            timeout=TIMEOUT
        )
    else:
        print("ℹ️ Cookie banner absent/already closed.")


def click_show_results(page: Page) -> None:
    """
    Click on the 'Show results' button.
    
    Args:
        page: The Playwright Page object.
    """
    _click_on_element(
        page=page,
        container_selector=SELECTORS["results"]["container"],
        button_selector=SELECTORS["results"]["button"],
        description="Clicking on 'Show results'",
        timeout=TIMEOUT
    )


def click_download_tab(page: Page) -> None:
    """
    Click on the 'Download' tab.
    
    Args:
        page: The Playwright Page object.
    """
    _click_on_element(
        page=page,
        container_selector=SELECTORS["download"]["tab"]["container"],
        button_selector=SELECTORS["download"]["tab"]["button"],
        description="Clicking on 'Download' tab",
        timeout=TIMEOUT
    )


def start_downloading_data_playwright(page: Page, csv_name: str) -> None:
    """
    Start downloading data in CSV format.
    
    Args:
        page: The Playwright Page object.
        csv_name: Name for the downloaded CSV file.
    """
    _click_on_download(
        page=page,
        button_selector=SELECTORS["download"]["download_button"],
        csv_name=csv_name,
        destination_dir=DATA_RAW_DIR,
        description="Downloading data in CSV format",
        timeout=TIMEOUT
    )