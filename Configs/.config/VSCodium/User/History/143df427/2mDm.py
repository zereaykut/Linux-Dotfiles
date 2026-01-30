import sys
import pandas as pd
import logging
from datetime import datetime, timedelta
from src.utils import get_env_variable, save_to_csv, fetch_api_data
from src.exception import CustomException

def main():
    try:
        start_date = (datetime.today() - timedelta(days=6)).strftime("%d-%m-%Y")
        end_date = datetime.today().strftime("%d-%m-%Y")
        
        api_key = get_env_variable("EVDS_API_KEY")

        url = (f"https://evds2.tcmb.gov.tr/service/evds/"
               f"series=TP.DK.USD.A-TP.DK.USD.S-TP.DK.EUR.A-TP.DK.EUR.S"
               f"&startDate={start_date}&endDate={end_date}&type=json")
        
        json_data = fetch_api_data(url, headers={"key": api_key})
        
        # 4. Process and Save
        if json_data and "items" in json_data:
            df = pd.DataFrame(json_data["items"])
            df = df.drop(columns=["UNIXTIME"], errors="ignore").fillna(method="ffill")
            df["QUERY_DATE"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

            if not df.empty:
                path = save_to_csv(df, "processed", "exchange_rates")
                logging.info(f"Data successfully appended to {path}")
        else:
            logging.warning("No data found in the API response.")

    except Exception as e:
        # Detailed error will be captured by CustomException
        raise CustomException(e, sys)

if __name__ == "__main__":
    main()