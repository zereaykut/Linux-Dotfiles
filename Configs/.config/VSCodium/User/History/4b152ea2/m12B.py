import os
import sys
import pandas as pd
from pathlib import Path
from dotenv import load_dotenv
from src.exception import CustomException

load_dotenv()

ROOT_DIR = Path(__file__).parent.parent

DATA_DIR = ROOT_DIR / "data"

def get_env_variable(var_name: str) -> str:
    """Retrieves a variable from the environment."""
    value = os.getenv(var_name)
    if value is None:
        error_msg = f"Environment variable '{var_name}' is not set."
        raise CustomException(error_msg, sys)
    return value

def save_to_csv(df: pd.DataFrame, folder: str, file_name: str) -> str:
    """Saves a DataFrame to the data directory relative to the script."""
    try:
        # This will create project_root/data/processed/
        target_dir = DATA_DIR / folder
        target_dir.mkdir(parents=True, exist_ok=True)
        
        save_path = target_dir / f"{file_name}.csv"
        
        file_exists = save_path.exists()
        df.to_csv(save_path, mode='a' if file_exists else 'w', 
                  header=not file_exists, index=False, encoding="utf-8-sig")
            
        return str(save_path)
    except Exception as e:
        raise CustomException(e, sys)