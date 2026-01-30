# -*- coding: utf-8 -*-
import os
import sys
import logging

# Add the project root to sys.path to allow importing from 'src'
# This calculates the path to the folder above 'scripts'
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.utils import save_json
from src.services import EpiasTransparencyerServices

def main() -> None:
    logging.info("Attempting to fetch new TGT from EPIAS...")
    
    try:
        # Calling the static method directly from the class
        response = EpiasTransparencyerServices.tgt()
        
        if response.status_code in [200, 201]:
            # The API returns the TGT inside a JSON object
            tgt_data = response.json()
            
            # Ensure the data directory exists relative to project root
            os.makedirs("data", exist_ok=True)
            
            save_json(tgt_data, "data/tgt.json")
            logging.info(f"TGT successfully updated. Status: {response.status_code}")
        else:
            logging.error(f"TGT fetch failed. Status: {response.status_code}, Detail: {response.text}")
            
    except Exception as e:
        logging.error(f"An unexpected error occurred: {e}")

if __name__ == "__main__":
    main()