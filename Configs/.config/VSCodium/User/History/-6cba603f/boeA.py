# -*- coding: utf-8 -*-
import os
import sys
import logging
from datetime import date, timedelta

# Add project root to path for module discovery
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src import logger
from src.utils import get_selected_powerplants, get_tgt, save_json
from src.services import EpiasTransparencyerServices

@logger
def fetch_and_save_grt(service, tgt, start, end, pp_info):
    """
    Isolated function for a single powerplant fetch. 
    The @logger decorator handles exceptions for each individual plant.
    """
    grt_id = pp_info.get("id")
    name = pp_info.get("name")
    
    if grt_id is None:
        logging.warning(f"Skipping: grt_id is missing for {name}")
        return

    # Call the service (now uses internal session and retries)
    response = service.grt(tgt, start, end, grt_id)
    
    # .json() is called safely here because the service handles raise_for_status()
    if response:
        save_json(response.json(), f"data/selected_powerplants_data/{name}_{grt_id}.json")
        logging.info(f"Saved data for: {name}")

def main() -> None:
    # 1. Setup Dates
    start_date = str(date.today() - timedelta(days=7))
    end_date = str(date.today() - timedelta(days=1))
    logging.info(f"Data Collection Range: {start_date} to {end_date}")

    # 2. Initialization
    tgt = get_tgt()
    if not tgt:
        logging.error("No TGT found. Run fetch_tgt.py first.")
        return

    service = EpiasTransparencyerServices()
    pps_list = get_selected_powerplants()
    os.makedirs("data/selected_powerplants_data/", exist_ok=True)

    # 3. Main Loop
    for index, pp_info in enumerate(pps_list):
        print(f"[{index:03d}] Processing: {pp_info.get('name')}")
        
        # We call the decorated function. If it fails, the loop continues.
        fetch_and_save_grt(service, tgt, start_date, end_date, pp_info)
        
        # Note: time.sleep(2) is removed because the retry strategy 
        # in services.py handles "politeness" and backoffs automatically.

if __name__ == "__main__":
    main()