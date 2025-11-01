import os
from typing import Dict, Any
import pandas as pd
import numpy as np
import unidecode
from sklearn.neighbors import BallTree
from config import *
from src.utils.utils import *

def clean_all_data() -> None:
    """
    Clean and merge all datasets: radiation, municipality, and weather data.
    
    This function orchestrates the complete data cleaning pipeline:
    1. Loads raw data from CSV files
    2. Cleans each dataset individually
    3. Merges radiation data with geographic coordinates
    4. Associates weather data with radiation measurements
    5. Saves the final cleaned dataset
    """

    # Clear the clean data directory
    delete_files_in_directory(DATA_CLEANED_DIR)
    
    # Load raw data
    print("Loading radiation data...")
    radiation_df = concatenate_radiation_data(
        data_raw_dir=DATA_RAW_DIR,
        radiation_data_filename_pattern=RADIATION_DATA_FILENAME_PATTERN,
        config=RADIATION_DATA_CONFIG,
    )

    print("Loading municipality data...")
    mun_df = pd.read_csv(os.path.join(DATA_RAW_DIR, MUNICIPALITY_DATA_FILENAME), sep=",", low_memory=False)

    print("Loading weather data...")
    weather_df = pd.read_csv(os.path.join(DATA_RAW_DIR, WEATHER_DATA_FILENAME), sep=";")

    # Clean data
    print("Cleaning radiation data...")
    radiation_df = clean_radiation_data(radiation_df, RADIATION_DATA_CONFIG)

    print("Cleaning municipality data...")
    mun_df = clean_municipality_data(mun_df, MUNICIPALITY_DATA_CONFIG)

    print("Cleaning weather data...")
    weather_df = clean_weather_data(weather_df, WEATHER_DATA_CONFIG)

    # Merge data
    print("Associating data...")
    print("Geolocating radiation data...")
    radiation_geo = geolocate_radiation_data(
        radiation_df=radiation_df, 
        municipality_df=mun_df, 
        radiation_data_config=RADIATION_DATA_CONFIG, 
        municipality_data_config=MUNICIPALITY_DATA_CONFIG
    )
    print("Adding weather to radiation data...")
    final_df = associate_weather_to_radiation(
        radiation_df=radiation_geo,
        weather_df=weather_df,
        config_rad=RADIATION_DATA_CONFIG,
        config_weather=WEATHER_DATA_CONFIG,
        max_distance_m=50000  # 50 km
    )

    # Save cleaned data to CSV file
    print("Saving cleaned dataset...")
    final_df.to_csv(os.path.join(DATA_CLEANED_DIR, CLEANED_DATA_FILENAME), sep=";", index=False)
    

def concatenate_radiation_data(
    data_raw_dir: str,
    radiation_data_filename_pattern: str,
    config: Dict[str, Any],
) -> pd.DataFrame:
    """
    Concatenate multiple radiation data CSV files into a single DataFrame.
    
    This function uses a generic CSV concatenation utility to merge radiation
    measurement files from different periods and environments.

    Args:
        data_raw_dir: Directory containing the CSV files.
        radiation_data_filename_pattern: Filename pattern for file search.
        config: Configuration dictionary for radiation data processing.

    Returns:
        pd.DataFrame: Concatenated DataFrame of radiation data.
    """
    
    return concatenate_csv_files(
        data_raw_dir=data_raw_dir,
        filename_pattern=radiation_data_filename_pattern,
        medium_column_name=config["measurement_environment_column"],
        medium_mapping=config["medium"],
    )


def clean_radiation_data(radiation_df: pd.DataFrame, config: Dict[str, Any]) -> pd.DataFrame:
    """
    Clean radiation data by removing missing values, duplicates, and normalizing municipality names.
    
    Args:
        radiation_df: Raw radiation DataFrame.
        config: Configuration dictionary containing column names and processing rules.

    Returns:
        pd.DataFrame: Cleaned radiation DataFrame with normalized municipality names.
    """
    # Drop rows where specified columns are missing
    radiation_df = radiation_df.dropna(subset=config["dropna_columns"])

    # Remove duplicates
    radiation_df = radiation_df.drop_duplicates(
        subset=config["drop_duplicates_columns"],
        keep="first"
    )
    
    # Normalize municipality names (uppercase, remove accents)
    radiation_df[config["municipality_name"]] = (
        radiation_df[config["municipality_name"]]
        .str.upper()
        .apply(unidecode.unidecode)
    )
    radiation_df[config["municipality_name"]] = radiation_df[config["municipality_name"]].str.replace(r"^L'", "", regex=True)

    # Select columns to keep
    radiation_df = radiation_df[config["required_columns"]]

    return radiation_df


def clean_municipality_data(mun_df: pd.DataFrame, config: Dict[str, Any]) -> pd.DataFrame:
    """
    Clean municipality data by normalizing names and consolidating geographic coordinates.
    
    Args:
        mun_df: Raw municipality DataFrame.
        config: Configuration dictionary containing column names and processing rules.

    Returns:
        pd.DataFrame: Cleaned municipality DataFrame with standardized names and coordinates.
    """
    # Normalize municipality name: uppercase & without accents
    mun_df[config["name_column"]["cleaned"]] = (
        mun_df[config["name_column"]["primary"]]
        .str.upper()
        .apply(unidecode.unidecode)
    )

    # Harmonize names starting with "L'"
    mun_df[config["name_column"]["cleaned"]] = mun_df[config["name_column"]["cleaned"]].str.replace(r"^L'", "", regex=True)

    # Create latitude and longitude columns
    mun_df[config["latitude_columns"]["cleaned"]] = mun_df[config["latitude_columns"]["primary"]].fillna(
        mun_df[config["latitude_columns"]["fallback"]]
    )
    mun_df[config["longitude_columns"]["cleaned"]] = mun_df[config["longitude_columns"]["primary"]].fillna(
        mun_df[config["longitude_columns"]["fallback"]]
    )

    # Keep the most populated municipality per name
    mun_df = (
        mun_df.sort_values(config["population_column"], ascending=False)
              .drop_duplicates(subset=config["name_column"]["cleaned"], keep="first")
    )

    # Select relevant columns
    mun_df = mun_df[config["required_columns"]]
    return mun_df


def geolocate_radiation_data(
    radiation_df: pd.DataFrame,
    municipality_df: pd.DataFrame,
    radiation_data_config: Dict[str, Any],
    municipality_data_config: Dict[str, Any]
) -> pd.DataFrame:
    """
    Add geographic coordinates to radiation data by joining with municipality data.
    
    Args:
        radiation_df: Cleaned radiation DataFrame.
        municipality_df: Cleaned municipality DataFrame with coordinates.
        radiation_data_config: Configuration for radiation data columns.
        municipality_data_config: Configuration for municipality data columns.

    Returns:
        pd.DataFrame: Radiation DataFrame with latitude and longitude columns added.
    """
    
    # Jointure
    merged_df = merge_dataframes(
        left_df=radiation_df,
        right_df=municipality_df,
        left_key=radiation_data_config["municipality_name"],
        right_key=municipality_data_config["name_column"]["cleaned"],
        how="left"
    )

    latitude_name = municipality_data_config["latitude_columns"]["cleaned"]
    longitude_name = municipality_data_config["longitude_columns"]["cleaned"]
    date_column = radiation_data_config["date_start_column"]

    # Check - how many unmatched municipalities?
    missing = merged_df[latitude_name].isna().sum()
    total = merged_df.shape[0]

    # Remove rows without geographic coordinates
    merged_df = merged_df.dropna(subset=[latitude_name, longitude_name])
    
    # Drop the column used for joining
    merged_df = merged_df.drop(columns=[municipality_data_config["name_column"]["cleaned"]])
    
    # Convert date column to datetime
    merged_df[date_column] = pd.to_datetime(merged_df[date_column], errors="coerce")
    merged_df = merged_df.dropna(subset=[date_column])

    print(f"✅ Join completed. Kept: {total-missing}/{total} ({(total-missing)/total:.2%})")
    
    return merged_df


def clean_weather_data(weather_df: pd.DataFrame, config: Dict[str, Any]) -> pd.DataFrame:
    """
    Clean weather data by converting coordinates and formatting dates.
    
    This function processes meteorological data by:
    1. Selecting required columns
    2. Removing rows with missing essential data
    3. Converting Lambert coordinates to WGS84 (latitude/longitude)
    4. Formatting date columns
    
    Args:
        weather_df: Raw weather DataFrame.
        config: Configuration dictionary containing column names and processing rules.

    Returns:
        pd.DataFrame: Cleaned weather DataFrame with geographic coordinates and formatted dates.
    """
    # Select columns
    weather_df = weather_df[config["required_columns"]]

    # Remove rows where essential data is missing
    weather_df = weather_df.dropna(subset=config["dropna_columns"])

    # Multiply Lambert coordinates by 100
    weather_df[config["lambert"]["x"]] *= 100
    weather_df[config["lambert"]["y"]] *= 100

    # Convert Lambert coordinates to Latitude / Longitude (WGS84)
    weather_df = convert_lambert_to_wgs84(
        df=weather_df,
        x_col=config["lambert"]["x"],
        y_col=config["lambert"]["y"],
        lat_col=config["geo"]["lat"],
        lon_col=config["geo"]["lon"]
    )
    
    # Drop Lambert columns
    weather_df = weather_df.drop(columns=[config["lambert"]["x"], config["lambert"]["y"]])

    # Convert DATE to datetime (e.g., 20200101 -> 2020-01-01)
    weather_df[config["date_column"]] = pd.to_datetime(
        weather_df[config["date_column"]].astype(str),
        format="%Y%m%d",
        errors="coerce"
    )
    weather_df = weather_df.dropna(subset=[config["date_column"]])
        
    return weather_df


def associate_weather_to_radiation(
    radiation_df: pd.DataFrame,
    weather_df: pd.DataFrame,
    config_rad: Dict[str, Any],
    config_weather: Dict[str, Any],
    max_distance_m: float = 50000
) -> pd.DataFrame:
    """
    Associate weather data with radiation measurements based on date and geographic proximity.
    
    This function uses a BallTree spatial index with Haversine distance to find the nearest
    weather station for each radiation measurement on the same date, within a maximum distance.
    
    Args:
        radiation_df: Geolocated radiation DataFrame.
        weather_df: Cleaned weather DataFrame with coordinates.
        config_rad: Configuration for radiation data columns.
        config_weather: Configuration for weather data columns.
        max_distance_m: Maximum distance in meters for weather station association (default: 50000).

    Returns:
        pd.DataFrame: Merged DataFrame containing radiation measurements with associated weather data.
    """
    lat_rad = config_rad["latitude_columns"]["cleaned"]
    lon_rad = config_rad["longitude_columns"]["cleaned"]
    date_rad = config_rad["date_start_column"]

    lat_met = config_weather["geo"]["lat"]
    lon_met = config_weather["geo"]["lon"]
    date_met = config_weather["date_column"]
    snow_met = config_weather["snowfall_column"]
    rain_met = config_weather["rainfall_column"]
    
    dist_rad_met = config_rad["distance_to_nearest_weather_data"]

    # Earth radius for Haversine conversion
    R = 6371000

    # Add result columns
    result_rows = []

    # Group weather by date to avoid massive cross join
    weather_by_date = {
        d: df for d, df in weather_df.groupby(date_met)
    }
    
    # Optimized loop by date
    for day, subset_asnr in radiation_df.groupby(date_rad):

        if day not in weather_by_date:
            continue  # No station on this day

        subset_weather = weather_by_date[day]

        # Convert to radians
        weather_coords = np.vstack([
            np.radians(subset_weather[lat_met].values),
            np.radians(subset_weather[lon_met].values)
        ]).T

        radiation_coords = np.vstack([
            np.radians(subset_asnr[lat_rad].values),
            np.radians(subset_asnr[lon_rad].values)
        ]).T

        # BallTree Haversine
        tree = BallTree(weather_coords, metric='haversine')

        # Nearest neighbor query
        dist, ind = tree.query(radiation_coords, k=1)
        dist_m = dist[:, 0] * R

        # Filter by maximum distance
        mask = dist_m <= max_distance_m
        valid_idx = np.where(mask)[0]

        for i in valid_idx:
            weather_row = subset_weather.iloc[ind[i][0]]
            asnr_row = subset_asnr.iloc[i]

            result = asnr_row.to_dict()
            result.update({
                f"{date_met}_METEO": weather_row[date_met],
                snow_met: weather_row[snow_met],
                rain_met: weather_row[rain_met],
                dist_rad_met: dist_m[i],
            })
            result_rows.append(result)

    result_df = pd.DataFrame(result_rows)

    print(f"✅ Association completed. Kept: {len(result_df)}/{len(radiation_df)} ({len(result_df)/len(radiation_df):.2%})")

    return result_df