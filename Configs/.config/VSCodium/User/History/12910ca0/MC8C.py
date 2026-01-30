import pandas as pd
from datetime import datetime, timedelta
from src.utils import open_meteo
import warnings

warnings.filterwarnings("ignore")

def main() -> None:
    # Dummy info for demonstration (Replace with your actual coordinates)
    df_info = pd.DataFrame({
        "LAT": [41.0082], "LON": [28.9784], "ELEVATION": [30]
    })

    query_date = datetime.today().strftime("%Y-%m-%d %H:%M:%S")
    
    print("Requesting Forecast Data...")
    data = open_meteo(
        df_info, 
        url="https://api.open-meteo.com/v1/forecast", 
        model_params=["temperature_2m", "wind_speed_10m", "shortwave_radiation"],
        past_days=0
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

    # Save to CSV for analysis
    df_result = pd.DataFrame(all_records)
    df_result.to_csv("forecast_data.csv", index=False)
    print(f"Saved {len(df_result)} records to forecast_data.csv")

if __name__ == "__main__":
    main()