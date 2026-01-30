import os
import json
import logging
import requests
import pandas as pd
from datetime import datetime

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

class EpysClient:
    def __init__(self, credentials_path):
        self.cas_url = "https://cas.epias.com.tr/cas/v1/tickets"
        self.base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        self.data_dir = os.path.join(self.base_dir, "data")
        self.credentials = self._load_credentials(credentials_path)
        
        if not os.path.exists(self.data_dir):
            os.makedirs(self.data_dir)

    def _load_credentials(self, path):
        with open(path, "r", encoding="utf8") as f:
            return json.load(f)

    def get_headers(self, username, password, service_url="https://epys.epias.com.tr"):
        """Performs TGT and ST ticket acquisition."""
        try:
            # 1. Get TGT
            tgt_resp = requests.post(f"{self.cas_url}?format=text", 
                                     data={"username": username, "password": password},
                                     headers={"Content-Type": "application/x-www-form-urlencoded"}, 
                                     timeout=30)
            tgt_resp.raise_for_status()
            tgt = tgt_resp.text

            # 2. Get ST
            st_resp = requests.post(f"{self.cas_url}/{tgt}", 
                                    data={"service": service_url},
                                    headers={"Content-Type": "application/x-www-form-urlencoded"}, 
                                    timeout=30)
            st_resp.raise_for_status()
            
            return {
                "TGT": tgt,
                "ST": st_resp.text,
                "Accept": "application/json",
                "Content-Type": "application/json"
            }
        except Exception as e:
            logging.error(f"Authentication failed for {username}: {e}")
            return None

    def fetch_and_save(self, url, payload, headers, filename, org_name):
        """Fetches data from EPYS and saves to CSV in data/ directory."""
        try:
            response = requests.post(url, headers=headers, json=payload, timeout=60)
            if response.status_code == 200:
                data = response.json().get("body", {}).get("content", {}).get("items", [])
                if not data:
                    # Some endpoints return data in a different structure, check 'content' directly
                    data = response.json().get("body", {}).get("content", [])
                
                if data:
                    df = pd.DataFrame(data)
                    df['query_date'] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    df['org_name'] = org_name
                    
                    save_path = os.path.join(self.data_dir, f"{filename}.csv")
                    # Append mode logic
                    header_needed = not os.path.exists(save_path)
                    df.to_csv(save_path, mode='a', index=False, header=header_needed, encoding="utf-8-sig")
                    logging.info(f"Successfully saved {len(df)} rows to {filename}.csv")
                else:
                    logging.warning(f"No data returned for {filename} ({org_name})")
            else:
                logging.error(f"API Error {response.status_code}: {response.text}")
        except Exception as e:
            logging.error(f"Request failed for {filename}: {e}")