# -*- coding: utf-8 -*-
import os
import sys
import logging

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
    
    if response:
        save_json(response.json(), "data/powerplants_info.json")
        logging.info("Powerplant info list successfully updated in data folder.")

def main() -> None:
    tgt = get_tgt()
    if not tgt:
        logging.error("TGT not found. Please run fetch_tgt.py first.")
        return

    service = EpiasTransparencyerServices()
    
    os.makedirs("data", exist_ok=True)

    fetch_and_save_all_powerplants(service, tgt)

if __name__ == "__main__":
    main()