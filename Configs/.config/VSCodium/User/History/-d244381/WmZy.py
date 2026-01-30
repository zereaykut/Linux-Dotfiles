import os
import json
import logging
import pyodbc
import requests
from dotenv import load_dotenv
import pandas as pd
from typing import List, Dict, Any, Optional
from datetime import datetime
from contextlib import contextmanager
from urllib3.util import Retry
from requests.adapters import HTTPAdapter

# Load environment variables from .env file
load_dotenv()

# --- Configuration & Logging ---
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger_instance = logging.getLogger(__name__)

# --- Database Management ---

@contextmanager
def get_db_connection(db_name: str):
    """
    Context manager to handle SQL Server connections using environment variables.
    """
    # Retrieve credentials from environment
    server = os.getenv("DB_SERVER")
    user = os.getenv("DB_USER")
    password = os.getenv("DB_PASSWORD")

    if not all([server, user, password]):
        logger_instance.error("Database credentials missing in environment variables.")
        raise EnvironmentError("Ensure DB_SERVER, DB_USER, and DB_PASSWORD are set.")

    try:
        conn_str = (
            f"DRIVER={{SQL Server}};"
            f"SERVER={server};"
            f"DATABASE={db_name};"
            f"UID={user};"
            f"PWD={password};"
        )
        conn = pyodbc.connect(conn_str)
        # Enable fast_executemany for high-performance bulk inserts
        conn.fast_executemany = True 
        try:
            yield conn
        finally:
            conn.close()
    except pyodbc.Error as e:
        logger_instance.error(f"Database connection error: {e}")
        raise

# ... [Remaining utility and Open-Meteo functions stay the same] ...

# --- API Handling with Retries ---

def get_api_session() -> requests.Session:
    """
    Creates a requests session with automatic retry logic for connection errors.
    """
    session = requests.Session()
    retries = Retry(total=5, backoff_factor=1, status_forcelist=[502, 503, 504])
    session.mount("https://", HTTPAdapter(max_retries=retries))
    return session

# --- Utility Functions ---

def save_json(data: Dict, loc: str) -> None:
    """Saves dictionary to JSON file with proper indentation."""
    with open(loc, "w", encoding="utf8") as f:
        json.dump(data, f, indent=4)

def duplicates(df: pd.DataFrame, 
               cols: List[str] = ["DATE_TIME"], 
               sort_by: List[str] = ["DATE_TIME", "QUERY_DATE"], 
               drop_columns: List[str] = ["QUERY_DATE"]) -> pd.DataFrame:
    """Sorts and drops duplicates from a DataFrame."""
    return (df.sort_values(by=sort_by)
            .drop_duplicates(subset=cols, keep="last")
            .drop(columns=drop_columns))

def del_dup_rows(table: str, partition_by: str, query_date_1: str, conn: pyodbc.Connection) -> None:
    """
    Efficiently deletes duplicated rows using a Common Table Expression (CTE).
    """
    cursor = conn.cursor()
    sql = f"""
        WITH cte AS (
            SELECT {partition_by}, 
            ROW_NUMBER() OVER (PARTITION BY {partition_by} ORDER BY [QUERY_DATE] DESC) as row_num 
            FROM {table} 
            WHERE [QUERY_DATE] >= ?
        )
        DELETE FROM cte WHERE row_num > 1
    """
    cursor.execute(sql, (query_date_1,))
    conn.commit()

def log_to_db(query_date: str, error_statement: str, script_name: str, 
              response_status: int, source_name: str, start_date: str, 
              end_date: str, version: str, code_line_number: int, 
              conn: pyodbc.Connection) -> None:
    """
    Logs execution metadata and errors to the database.
    """
    cursor = conn.cursor()
    sql = """
        INSERT INTO [LOG_GET_DATA] 
        ([QUERY_DATE], [ERROR], [RESPONSE_STATUS], [SCRIPT_NAME], [SOURCE_NAME], [START_DATE], [END_DATE], [VERSION], [CODE_LINE_NUMBER]) 
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    """
    cursor.execute(sql, (query_date, error_statement, response_status, script_name, 
                         source_name, start_date, end_date, version, code_line_number))
    conn.commit()

def get_info() -> pd.DataFrame:
    """Fetches location metadata for Open-Meteo queries."""
    with get_db_connection("EKTM") as conn:
        query = "SELECT [LOCATION], [LAT], [LON], [ELEVATION], [AZIMUTH], [TYPE] FROM [EKTM].[dbo].[SABIT_OPEN_METEO_INFO]"
        return pd.read_sql(query, conn)

# --- Open-Meteo Specific API Functions ---

def _fetch_open_meteo(url: str, params: Dict[str, Any]) -> Dict:
    """Base helper to fetch data from Open-Meteo with error checking."""
    session = get_api_session()
    try:
        response = session.get(url, params=params, timeout=30)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        logger_instance.error(f"API Request failed: {e}")
        return {}

def open_meteo(df_info: pd.DataFrame, url: str, model_params: List[str], 
               past_days: int = 7, tilt: Optional[float] = None, 
               azimuth: Optional[float] = None) -> Dict:
    """Standard forecast API call."""
    params = {
        "latitude": df_info["LAT"].tolist(),
        "longitude": df_info["LON"].tolist(),
        "hourly": model_params,
        "wind_speed_unit": "ms",
        "past_days": past_days,
        "tilt": tilt,
        "azimuth": azimuth
    }
    return _fetch_open_meteo(url, params)

def open_meteo_hist(df_info: pd.DataFrame, url: str, model_params: List[str], 
                    start_date: str, end_date: str) -> Dict:
    """Archive API call for historical data."""
    params = {
        "latitude": df_info["LAT"].tolist(),
        "longitude": df_info["LON"].tolist(),
        "hourly": model_params,
        "wind_speed_unit": "ms",
        "start_date": start_date,
        "end_date": end_date,
    }
    return _fetch_open_meteo(url, params)

def open_meteo_climate(df_info: pd.DataFrame, url: str, model_params: List[str], 
                       model_names: str, start_date: str, end_date: str) -> Dict:
    """Climate API call."""
    params = {
        "latitude": df_info["LAT"].tolist(),
        "longitude": df_info["LON"].tolist(),
        "models": model_names,
        "daily": model_params,
        "wind_speed_unit": "ms",
        "start_date": start_date,
        "end_date": end_date,
    }
    return _fetch_open_meteo(url, params)