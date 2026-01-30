import os
import logging
import functools
import requests
from datetime import date
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
LOG_DIR = PROJECT_ROOT / "logs"

LOG_DIR.mkdir(parents=True, exist_ok=True)

log_filename = LOG_DIR / f"{date.today()}.log"

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(log_filename, encoding='utf-8'),
        logging.StreamHandler()
    ]
)

def logger(func):
    """
    A robust decorator that logs function entry, exit, and any exceptions.
    """
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        func_name = func.__name__
        logging.info(f">>> Starting execution: {func_name}")
        
        try:
            result = func(*args, **kwargs)
            logging.info(f"<<< Successfully finished: {func_name}")
            return result
            
        except requests.exceptions.HTTPError as e:
            logging.error(f"HTTP Error in {func_name}: {e.response.status_code} - {e.response.text}")
        except requests.exceptions.ConnectionError:
            logging.error(f"Connection Error in {func_name}: Could not connect to EPIAS servers.")
        except requests.exceptions.Timeout:
            logging.error(f"Timeout Error in {func_name}: The request timed out.")
        except Exception as e:
            logging.error(f"Unexpected error in {func_name}: {str(e)}", exc_info=True)
            
        return None
    return wrapper