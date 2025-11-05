import sqlite3
import pandas as pd
from pathlib import Path
from typing import Optional, Dict

def get_db_connection(db_path: str) -> sqlite3.Connection:
    """
    Create and return a SQLite database connection.
    
    Args:
        db_path: Path to the SQLite database file.
    
    Returns:
        sqlite3.Connection: Database connection object.
    """
    Path(db_path).parent.mkdir(parents=True, exist_ok=True)
    return sqlite3.connect(db_path)


def save_dataframe_to_sqlite(
    df: pd.DataFrame,
    db_path: str,
    table_name: str
) -> None:
    """
    Save a pandas DataFrame to a SQLite database table.
    
    Args:
        df: DataFrame to save.
        db_path: Path to the SQLite database file.
        table_name: Name of the table to create/replace in the database.
    """
    # Connect to SQLite database
    conn = get_db_connection(db_path)
    
    try:
        # Save dataframe to SQLite (replace if table exists)
        df.to_sql(table_name, conn, if_exists='replace', index=False)
        print(f"Successfully saved {len(df)} rows to table '{table_name}' in {db_path}")
    finally:
        conn.close()


def save_csv_to_sqlite(
    csv_path: str,
    db_path: str,
    table_name: str,
    compression: Optional[str] = None,
    sep: str = ";",
) -> None:
    """
    Load a CSV file and save it to a SQLite database table.
    
    Args:
        csv_path: Path to the CSV file to load.
        db_path: Path to the SQLite database file.
        table_name: Name of the table to create/replace in the database.
        compression: Compression type for reading CSV (e.g., 'gzip', 'infer').
        sep: Delimiter to use for reading the CSV file. Default: ';'.
    """
    print("⏳ Saving to the database...")
    # Read the CSV file
    df = pd.read_csv(csv_path, compression=compression, sep=sep, low_memory=False)
        
    # Save using the dataframe function
    save_dataframe_to_sqlite(df, db_path, table_name)


def table_exists(db_path: str, table_name: str) -> bool:
    """
    Check if a table exists in the SQLite database.
    
    Args:
        db_path: Path to the SQLite database file.
        table_name: Name of the table to check.
    
    Returns:
        bool: True if table exists, False otherwise.
    """
    if not Path(db_path).exists():
        return False
    
    conn = get_db_connection(db_path)
    try:
        cursor = conn.cursor()
        cursor.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name=?",
            (table_name,)
        )
        return cursor.fetchone() is not None
    finally:
        conn.close()


def get_table_row_count(db_path: str, table_name: str) -> int:
    """
    Get the number of rows in a table.
    
    Args:
        db_path: Path to the SQLite database file.
        table_name: Name of the table.
    
    Returns:
        int: Number of rows in the table.
    """
    conn = get_db_connection(db_path)
    try:
        cursor = conn.cursor()
        cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
        return cursor.fetchone()[0]
    finally:
        conn.close()


def concatenate_radiation_tables_in_db(
    db_path: str,
    table_prefix: str,
    output_table_name: str,
    medium_column_name: str,
    medium_mapping: Dict[str, any]
) -> None:
    """
    Concatenate multiple radiation tables in SQLite database into a single table.
    
    This function finds all tables with the given prefix, adds a medium column
    to each, and concatenates them into a single output table.
    
    Args:
        db_path: Path to the SQLite database file.
        table_prefix: Prefix of radiation tables to concatenate (e.g., 'radiation_data').
        output_table_name: Name of the consolidated output table.
        medium_column_name: Name of the column to add for the collection medium.
        medium_mapping: Dictionary mapping medium names to their tags.
    """

    conn = get_db_connection(db_path)
    
    try:
        # Get all tables that match the prefix
        cursor = conn.cursor()
        cursor.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name LIKE ?",
            (f"{table_prefix}_%",)
        )
        tables = [row[0] for row in cursor.fetchall()]
        
        if not tables:
            print(f"No tables found with prefix '{table_prefix}'")
            return
        
        print(f"Found {len(tables)} radiation tables to concatenate")
        
        dfs = []
        for table_name in tables:
            # Read the table
            df = pd.read_sql(f"SELECT * FROM {table_name}", conn)
            
            # Extract medium name from table name
            # Format: radiation_data_{medium}_{start_date}_{end_date}
            parts = table_name.replace(f"{table_prefix}_", "").split("_")
            medium_name = parts[0]  # First part after prefix is the medium
            
            # Add "Collection medium" column based on detected medium
            if medium_name in medium_mapping:
                df[medium_column_name] = medium_mapping[medium_name]["tag"]
            else:
                df[medium_column_name] = medium_name  # Default case
            
            dfs.append(df)
        
        # Concatenate all dataframes
        concatenated_df = pd.concat(dfs, ignore_index=True)
        
        print(f"Concatenated {len(concatenated_df)} total rows from {len(tables)} tables")
        
    finally:
        conn.close()
    
    # Save the concatenated dataframe to a new table
    save_dataframe_to_sqlite(
        df=concatenated_df,
        db_path=db_path,
        table_name=output_table_name
    )
    
    print(f"Successfully created consolidated table '{output_table_name}'")