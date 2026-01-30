import os
import sys
import logging

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.utils import save_json
from src.services import EpiasTransparencyerServices

def main() -> None:
    logging.info("Attempting to fetch new TGT from EPIAS...")
    
    try:
        response = EpiasTransparencyerServices.tgt()
        
        if response.status_code in [200, 201]:
            tgt_data = response.json()
            
            os.makedirs("data", exist_ok=True)
            
            save_json(tgt_data, "data/tgt.json")
            logging.info(f"TGT successfully updated. Status: {response.status_code}")
        else:
            logging.error(f"TGT fetch failed. Status: {response.status_code}, Detail: {response.text}")
            
    except Exception as e:
        logging.error(f"An unexpected error occurred: {e}")

if __name__ == "__main__":
    main()