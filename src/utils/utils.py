from typing import List, Dict, Any, Optional, Tuple
from pyproj import Transformer
import os
import urllib.request
import gzip
import shutil
import glob
import pandas as pd
from tqdm import tqdm


def download_file_from_url(
    url: str, 
    dest_folder: str, 
    filename: Optional[str] = None,
    chunk_size: int = 8192
) -> str:
    """
    Download a file from the given URL and save it to the destination folder.
    
    If the file is a .gz archive, it is automatically decompressed to .csv.
    
    Args:
        url: URL of the file to download.
        dest_folder: Destination folder.
        filename: Output filename. If None, uses the name from the URL.
        chunk_size: Size of chunks to read at a time (default: 8192 bytes).
        
    Returns:
        str: Absolute path of the downloaded (or decompressed if .gz) file.
        
    Raises:
        Exception: If download fails or file cannot be written.
    """

    # Create folder if it doesn't exist
    os.makedirs(dest_folder, exist_ok=True)

    # Determine filename
    if filename is None:
        filename = os.path.basename(url) or "downloaded_file"

    file_path = os.path.join(dest_folder, filename)

    try:
        print(f"Downloading {filename}...")

        with urllib.request.urlopen(url) as response:
            # Estimated size
            content_length = response.headers.get("Content-Length")
            if content_length:
                expected_size = int(content_length)
                print(f"Estimated size: {expected_size / (1024**2):.2f} MB")
            print("⏳ Please wait, downloading in progress...")

            # Initialize progress bar
            progress_bar = tqdm(
                total=expected_size,
                unit='B',
                unit_scale=True,
                desc=filename
            )

            # Download file with progress bar
            with open(file_path, "wb") as out_file:
                while True:
                    chunk = response.read(chunk_size)
                    if not chunk:
                        break
                    out_file.write(chunk)
                    progress_bar.update(len(chunk))

            progress_bar.close()

        actual_size = os.path.getsize(file_path)
        print(f"✅ File downloaded: {file_path} ({actual_size / (1024**2):.2f} MB)")

        # Automatic decompression if .gz
        if file_path.endswith(".gz"):
            decompressed_path = file_path[:-3]  # Remove .gz extension
            print(f"⏳ Decompressing gzip file to {decompressed_path}...")
            with gzip.open(file_path, "rb") as f_in:
                with open(decompressed_path, "wb") as f_out:
                    shutil.copyfileobj(f_in, f_out)
            print("✅ File decompressed successfully.")
            #os.remove(file_path)  # Optional: remove the .gz file
            file_path = decompressed_path

    except Exception as e:
        print(f"⚠️ Error during download: {e}")
        raise

    return os.path.abspath(file_path)


def merge_dataframes(
    left_df: pd.DataFrame,
    right_df: pd.DataFrame,
    left_key: str,
    right_key: str,
    how: str = "left",
    suffixes: Tuple[str, str] = ("", "_right")
) -> pd.DataFrame:
    """
    Merge two DataFrames on specified keys.
    
    This is a wrapper around pandas merge() to provide a consistent interface
    for joining datasets throughout the application.
    
    Args:
        left_df: Left DataFrame to merge.
        right_df: Right DataFrame to merge.
        left_key: Column name to join on in the left DataFrame.
        right_key: Column name to join on in the right DataFrame.
        how: Type of merge ('left', 'right', 'outer', 'inner'). Default: 'left'.
        suffixes: Suffixes to apply to overlapping column names. Default: ('', '_right').
    
    Returns:
        pd.DataFrame: Merged DataFrame.
    """
    merged = left_df.merge(
        right_df,
        left_on=left_key,
        right_on=right_key,
        how=how,
        suffixes=suffixes
    )
    return merged


def concatenate_csv_files(
    data_raw_dir: str,
    filename_pattern: str,
    medium_column_name: str,
    medium_mapping: Optional[Dict[str, Any]] = None,
    delimiter: str = ";"
) -> pd.DataFrame:
    """
    Generic function to concatenate multiple CSV files into a single DataFrame.
    
    This function reads all CSV files matching the given pattern, adds a column
    indicating the collection medium (extracted from filename), and concatenates
    them into a single DataFrame.
    
    Args:
        data_raw_dir: Directory containing the CSV files.
        filename_pattern: Filename pattern for file search (e.g., 'asnr_*_radiation_data_*.csv').
        medium_column_name: Name of the column to add for the collection medium.
        medium_mapping: Optional dictionary mapping medium names to their tags.
        delimiter: Delimiter used in CSV files. Default: ';'.
    
    Returns:
        pd.DataFrame: Concatenated DataFrame with all data and medium column added.
    """
    
    # Get all matching files
    files = glob.glob(os.path.join(data_raw_dir, filename_pattern))
    dfs = []
    for file in files:
        # Extract medium name from filename
        file_name = os.path.basename(file)
        medium_name = file_name.split("_")[1]  # E.g., "asnr_soil_radiation_data_..." -> "soil"
        # Load CSV file
        df = pd.read_csv(file, delimiter=delimiter)
        # Add "Collection medium" column based on detected medium
        if medium_mapping and medium_name in medium_mapping:
            df[medium_column_name] = medium_mapping[medium_name]["tag"]
        else:
            df[medium_column_name] = medium_name  # Default case
        dfs.append(df)
    # Final combination
    return pd.concat(dfs, ignore_index=True)


def convert_lambert_to_wgs84(
    df: pd.DataFrame,
    x_col: str,
    y_col: str,
    lat_col: str,
    lon_col: str
) -> pd.DataFrame:
    """
    Convert Lambert II extended coordinates to WGS84 (latitude/longitude).
    
    This function performs a vectorized coordinate transformation from the French
    NTF Lambert II extended projection (EPSG:27572) to the WGS84 geographic
    coordinate system (EPSG:4326).
    
    Args:
        df: DataFrame containing Lambert coordinates.
        x_col: Name of the column containing Lambert X coordinates.
        y_col: Name of the column containing Lambert Y coordinates.
        lat_col: Name of the output column for latitude.
        lon_col: Name of the output column for longitude.
    
    Returns:
        pd.DataFrame: DataFrame with added latitude and longitude columns.
    """
    # Conversion NTF Lambert II extended -> WGS84 (vectorized)
    transformer = Transformer.from_crs("EPSG:27572", "EPSG:4326", always_xy=True)

    df[lon_col], df[lat_col] = transformer.transform(
        df[x_col].values,
        df[y_col].values
    )

    return df


def delete_files_in_directory(directory_path: str) -> None:
    """
    Deletes all files in the specified directory.

    Args:
        directory_path (str): Absolute or relative path to the directory.

    Raises:
        Exception: If any error occurs (e.g., directory not found, permission denied, etc.).
    """
    try:
        # Check if the path exists and is a directory
        if not os.path.isdir(directory_path):
            raise Exception(f"The path '{directory_path}' is not a valid directory.")

        # Iterate over all items in the directory
        for item in os.listdir(directory_path):
            item_path = os.path.join(directory_path, item)

            # Check if the item is a file (not a subdirectory)
            if os.path.isfile(item_path):
                os.remove(item_path)
                print(f"Deleted file: {item_path}")

        print(f"All files in the directory '{directory_path}' have been deleted.")

    except Exception as e:
        print(f"⚠️ An error occurred: {e}")
        raise


def rename_columns(df: pd.DataFrame, old_names: List[str], new_names: List[str]) -> pd.DataFrame:
    """
    Renames specified columns in a pandas DataFrame.

    Args:
        df (pd.DataFrame): The DataFrame whose columns are to be renamed.
        old_names (List[str]): List of current column names to be renamed.
        new_names (List[str]): List of new column names (must be the same length as `old_names`).

    Returns:
        pd.DataFrame: The DataFrame with renamed columns.

    Raises:
        ValueError: If `old_names` and `new_names` have different lengths.
    """
    if len(old_names) != len(new_names):
        raise ValueError("`old_names` and `new_names` must have the same length.")

    # Create a mapping dictionary from old names to new names
    rename_dict: Dict[str, str] = dict(zip(old_names, new_names))

    # Rename the columns
    df = df.rename(columns=rename_dict)

    return df

def delete_files_in_directory(directory_path: str) -> None:
    """
    Deletes all files in the specified directory.

    Args:
        directory_path (str): Path to the directory whose files will be deleted.

    Returns:
        None: This function does not return a value.
    """
    os.makedirs(directory_path, exist_ok=True)
    for item in os.listdir(directory_path):
        p = os.path.join(directory_path, item)
        if os.path.isfile(p):
            os.remove(p)
    print(f"All files in the directory '{directory_path}' have been deleted.")

def remove_outliers(df: pd.DataFrame, column: str, threshold: float = 1000.0) -> pd.DataFrame:
    """
    Removes outliers from a DataFrame column using the IQR (Interquartile Range) method.

    Args:
        df (pd.DataFrame): Input DataFrame containing the data.
        column (str): Name of the column from which outliers will be removed.
        threshold (float, optional): Threshold for outlier detection.

    Returns:
        pd.DataFrame: DataFrame with outliers removed from the specified column.
    """
    Q1 = df[column].quantile(0.25)
    Q3 = df[column].quantile(0.75)
    IQR = Q3 - Q1
    lower_bound = Q1 - threshold * IQR
    upper_bound = Q3 + threshold * IQR
    return df[(df[column] >= lower_bound) & (df[column] <= upper_bound)]