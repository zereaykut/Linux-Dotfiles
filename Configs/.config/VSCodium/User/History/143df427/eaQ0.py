# evds_exchange_data_to_csv.py
import sys
import requests
import pandas as pd
import logging
from datetime import datetime, timedelta
from src.utils import get_env_variable, save_to_csv
from src.exception import CustomException

def main():
    try:
        start_date = (datetime.today() - timedelta(days=6)).strftime("%d-%m-%Y")
        end_date = datetime.today().strftime("%d-%m-%Y")
        
        api_key = get_env_variable("EVDS_API_KEY")

        url = f"https://evds2.tcmb.gov.tr/service/evds/series=TP.DK.USD.A-TP.DK.USD.S-TP.DK.EUR.A-TP.DK.EUR.S&startDate={start_date}&endDate={end_date}&type=json"
        response = requests.get(url, headers={"key": api_key})
        
        if response.status_code in [200, 201]:
            df = pd.DataFrame(response.json()["items"])
            df = df.drop(columns=["UNIXTIME"], errors="ignore").fillna(method="ffill")
            df["QUERY_DATE"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

            if not df.empty:
                # 4. Save to CSV in data/processed/
                path = save_to_csv(df, "processed", "exchange_rates")
                logging.info(f"Data successfully appended to {path}")
        else:
            logging.error(f"API Error: {response.status_code}")

    except Exception as e:
        # Re-raise as CustomException to ensure detailed logging
        raise CustomException(e, sys)

if __name__ == "__main__":
    main()