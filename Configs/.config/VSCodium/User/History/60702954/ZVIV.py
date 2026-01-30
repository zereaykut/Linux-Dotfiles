# -*- coding: utf-8 -*-
import os
import sys
import logging

# 1. Path Management: Allows running from root while script is in scripts/
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src import logger
from src.utils import save_json, get_tgt
from src.services import EpiasTransparencyerServices

@logger
def fetch_and_save_all_powerplants(service, tgt):
    """
    Calls the EPIAS service and saves the full list to data/powerplants_info.json.
    The @logger decorator captures any API or connection errors automatically.
    """
    response = service.info_powerplant_list(tgt)
    
    # Since _post() in services.py now calls raise_for_status(),
    # if we reach this line, the request was successful.
    if response:
        save_json(response.json(), "data/powerplants_info.json")
        logging.info("Powerplant info list successfully updated in data folder.")

def main() -> None:
    # 2. Get the session ticket
    tgt = get_tgt()
    if not tgt:
        logging.error("TGT not found. Please run fetch_tgt.py first.")
        return

    # 3. Initialize the service (equipped with session and retries)
    service = EpiasTransparencyerServices()
    
    # Ensure data directory exists
    os.makedirs("data", exist_ok=True)

    # 4. Execute the fetch
    fetch_and_save_all_powerplants(service, tgt)

if __name__ == "__main__":
    main()