import pandas as pd
import os
from datetime import datetime, date, timedelta
from src.utils import open_meteo_climate, ensure_data_dir
import warnings

warnings.filterwarnings("ignore")

def main() -> None:
    data_dir = ensure_data_dir("data")
    df_info = pd.DataFrame({"LAT": [41.0082], "LON": [28.9784], "ELEVATION": [30]})
    
    today = date.today()
    start_date, end_date = f"{today.year-5}-01-01", f"{today.year+5}-12-31"
    query_date = datetime.today().strftime("%Y-%m-%d %H:%M:%S")
    model_name = "MRI_AGCM3_2_S"

    data = open_meteo_climate(
        df_info, 
        url="https://climate-api.open-meteo.com/v1/climate", 
        model_params=["temperature_2m_mean", "wind_speed_10m_max"],
        model_names=model_name,
        start_date=start_date,
        end_date=end_date
    )

    all_records = []
    for item in data:
        lat, lon, el = item.get("latitude"), item.get("longitude"), item.get("elevation")
        daily = item.get("daily")
        times = daily.get("time")
        for key, vals in daily.items():
            if key == "time": continue
            for d_str, val in zip(times, vals):
                dt = datetime.strptime(d_str, "%Y-%m-%d") + timedelta(hours=3)
                all_records.append({
                    "LAT": lat, "LON": lon, "ELEVATION": el, "MODEL": model_name,
                    "PARAMETER_NAME": key, "PARAMETER_VALUE": val,
                    "TIME": dt, "QUERY_DATE": query_date
                })

    df_result = pd.DataFrame(all_records)
    file_path = os.path.join(data_dir, "climate_data.csv")
    df_result.to_csv(file_path, index=False)
    print(f"Climate data saved to {file_path}")

if __name__ == "__main__":
    main()