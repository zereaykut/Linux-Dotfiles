import os
import sys
import pandas as pd
import requests
from pathlib import Path
from dotenv import load_dotenv
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
from src.exception import CustomException

load_dotenv()

ROOT_DIR = Path(__file__).parent.parent
DATA_DIR = ROOT_DIR / "data"

def get_env_variable(var_name: str) -> str:
    """Retrieves a variable from the environment."""
    value = os.getenv(var_name)
    if value is None:
        raise CustomException(f"Environment variable '{var_name}' is not set.", sys)
    return value

def get_request_session(retries=3, backoff_factor=0.3, status_forcelist=(500, 502, 504)):
    """Creates a requests session with a retry mechanism."""
    session = requests.Session()
    retry = Retry(
        total=retries,
        read=retries,
        connect=retries,
        backoff_factor=backoff_factor,
        status_forcelist=status_forcelist,
    )
    adapter = HTTPAdapter(max_retries=retry)
    session.mount('http://', adapter)
    session.mount('https://', adapter)
    return session

def fetch_api_data(url: str, headers: dict):
    """Fetches data from an API using the retry session."""
    try:
        session = get_request_session()
        response = session.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        raise CustomException(e, sys)

def save_to_csv(df: pd.DataFrame, folder: str, file_name: str) -> str:
    """Saves a DataFrame to the relative data directory."""
    try:
        target_dir = DATA_DIR / folder
        target_dir.mkdir(parents=True, exist_ok=True)
        
        save_path = target_dir / f"{file_name}.csv"
        file_exists = save_path.exists()
        
        df.to_csv(save_path, mode='a' if file_exists else 'w', 
                  header=not file_exists, index=False, encoding="utf-8-sig")
            
        return str(save_path)
    except Exception as e:
        raise CustomException(e, sys)