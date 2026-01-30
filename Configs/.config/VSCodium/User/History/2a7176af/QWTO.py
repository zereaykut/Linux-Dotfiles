import pandas as pd
import os
from datetime import datetime, date, timedelta
from src.utils import open_meteo_hist, ensure_data_dir
import warnings

warnings.filterwarnings("ignore")

def main() -> None:
    data_dir = ensure_data_dir("data")
    df_info = pd.DataFrame({"LAT": [41.0082], "LON": [28.9784], "ELEVATION": [30]})
    
    start_date = str(date.today() - timedelta(days=17))
    end_date = str(date.today() - timedelta(days=7))
    query_date = datetime.today().strftime("%Y-%m-%d %H:%M:%S")

    data = open_meteo_hist(
        df_info, 
        url="https://archive-api.open-meteo.com/v1/archive",
        model_params=["temperature_2m", "wind_speed_10m"],
        start_date=start_date,
        end_date=end_date,
    )

    all_records = []
    for item in data:
        lat, lon, el = item.get("latitude"), item.get("longitude"), item.get("elevation")
        hourly = item.get("hourly")
        times = hourly.get("time")
        for key, vals in hourly.items():
            if key == "time": continue
            for time_str, val in zip(times, vals):
                dt = datetime.strptime(time_str, "%Y-%m-%dT%H:%M") + timedelta(hours=3)
                all_records.append({
                    "LAT": lat, "LON": lon, "ELEVATION": el,
                    "PARAMETER_NAME": key, "PARAMETER_VALUE": val,
                    "TIME": dt, "QUERY_DATE": query_date
                })

    df_result = pd.DataFrame(all_records)
    file_path = os.path.join(data_dir, "historical_data.csv")
    df_result.to_csv(file_path, index=False)
    print(f"Historical data saved to {file_path}")

if __name__ == "__main__":
    main()