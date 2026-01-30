import os
import json
import logging
import requests
import pandas as pd
from typing import List, Dict, Any, Optional
from datetime import datetime
from urllib3.util import Retry
from requests.adapters import HTTPAdapter

# --- Configuration & Logging ---
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger_instance = logging.getLogger(__name__)

# --- API Handling with Retries ---
def get_api_session() -> requests.Session:
    """Creates a requests session with retry logic for API stability."""
    session = requests.Session()
    retries = Retry(total=5, backoff_factor=1, status_forcelist=[502, 503, 504])
    session.mount("https://", HTTPAdapter(max_retries=retries))
    return session

# --- Utility Functions ---
def ensure_data_dir(directory: str = "data") -> str:
    """Ensures the target data directory exists."""
    if not os.path.exists(directory):
        os.makedirs(directory)
    return directory

def save_json(data: Dict, loc: str) -> None:
    """Saves dictionary to JSON file."""
    with open(loc, "w", encoding="utf8") as f:
        json.dump(data, f, indent=4)

# --- Open-Meteo Specific API Functions ---
def _fetch_open_meteo(url: str, params: Dict[str, Any]) -> Dict:
    """Helper to fetch data from Open-Meteo with error handling."""
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