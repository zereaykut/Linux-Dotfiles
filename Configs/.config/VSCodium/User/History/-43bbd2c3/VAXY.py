import os
import logging
import requests
import pandas as pd
from datetime import datetime

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

class EpysClient:
    def __init__(self):
        # Paths
        self.base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        self.data_dir = os.path.join(self.base_dir, "data")
        self.cas_url = "https://cas.epias.com.tr/cas/v1/tickets"
        
        # Get Credentials from Environment Variables
        self.username = os.getenv("EPYS_USERNAME")
        self.password = os.getenv("EPYS_PASSWORD")
        self.org_name = os.getenv("EPYS_ORG_NAME", "Default_Org")

        if not self.username or not self.password:
            raise EnvironmentError("EPYS_USERNAME or EPYS_PASSWORD not found in environment.")

        if not os.path.exists(self.data_dir):
            os.makedirs(self.data_dir)

    def get_headers(self):
        """Authenticates using environment variables and returns TGT/ST."""
        try:
            # 1. Get TGT
            tgt_resp = requests.post(f"{self.cas_url}?format=text", 
                                     data={"username": self.username, "password": self.password},
                                     headers={"Content-Type": "application/x-www-form-urlencoded"}, 
                                     timeout=30)
            tgt_resp.raise_for_status()
            tgt = tgt_resp.text

            # 2. Get ST
            st_resp = requests.post(f"{self.cas_url}/{tgt}", 
                                    data={"service": "https://epys.epias.com.tr"},
                                    headers={"Content-Type": "application/x-www-form-urlencoded"}, 
                                    timeout=30)
            st_resp.raise_for_status()
            
            return {
                "TGT": tgt, "ST": st_resp.text,
                "Accept": "application/json", "Content-Type": "application/json"
            }
        except Exception as e:
            logging.error(f"Auth failed: {e}")
            return None

    def fetch_and_save(self, url, payload, filename):
        """Standardized fetch and CSV save logic."""
        headers = self.get_headers()
        if not headers: return

        try:
            response = requests.post(url, headers=headers, json=payload, timeout=60)
            response.raise_for_status()
            
            # API can return items in 'items' list or directly in 'content'
            body = response.json().get("body", {})
            content = body.get("content", {})
            items = content.get("items", content) if isinstance(content, dict) else content

            if items:
                df = pd.DataFrame(items)
                df['query_date'] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                df['org_name'] = self.org_name
                
                save_path = os.path.join(self.data_dir, f"{filename}.csv")
                header_needed = not os.path.exists(save_path)
                df.to_csv(save_path, mode='a', index=False, header=header_needed, encoding="utf-8-sig")
                logging.info(f"Saved {len(df)} rows to {filename}.csv")
            else:
                logging.warning(f"No data for {filename}")
        except Exception as e:
            logging.error(f"Fetch error for {filename}: {e}")