from datetime import datetime, timedelta
from src.utils import get_db_connection, get_info, open_meteo, del_dup_rows
import warnings

warnings.filterwarnings("ignore")

def main() -> None:
    # Get location information
    print("Fetching location info...")
    df_info = get_info()

    # Define Parameters
    query_date = datetime.today().strftime("%Y-%m-%d %H:%M:%S")
    query_date_1 = (datetime.today() - timedelta(days=15)).strftime("%Y-%m-%d %H:%M:%S")
    tilt, azimuth = None, None

    # Fetch Data from API
    print("Requesting Open-Meteo Forecast Data...")
    data = open_meteo(
        df_info, 
        url="https://api.open-meteo.com/v1/forecast", 
        model_params=[
            "temperature_2m", "relative_humidity_2m", "dew_point_2m", "apparent_temperature", 
            "precipitation_probability", "precipitation", "rain", "snowfall", "weather_code", 
            "pressure_msl", "surface_pressure", "cloud_cover", "wind_speed_10m", "shortwave_radiation"
        ],
        past_days=0,
        tilt=tilt,
        azimuth=azimuth,
    )

    # Prepare Data for Bulk Insert
    print("Processing data for storage...")
    insert_data = []
    for item in data:
        lat, lon, el = item.get("latitude"), item.get("longitude"), item.get("elevation")
        hourly = item.get("hourly")
        times = hourly.get("time")
        
        for key, vals in hourly.items():
            if key == "time": continue
            for time_str, val in zip(times, vals):
                # Standardize time to datetime object with 3-hour offset
                dt = datetime.strptime(time_str, "%Y-%m-%dT%H:%M") + timedelta(hours=3)
                insert_data.append((lat, lon, el, tilt, azimuth, val, key, dt, query_date))

    # Save to Database using Context Manager and Bulk Insert
    with get_db_connection("EKTM_HAM") as conn:
        cursor = conn.cursor()
        print(f"Inserting {len(insert_data)} records...")
        sql = """INSERT INTO [OPEN_METEO_FOR] ([LAT], [LON], [ELEVATION], [TILT], [AZIMUTH], [PARAMETER_VALUE], [PARAMETER_NAME], [TIME], [QUERY_DATE])
                 VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)"""
        cursor.executemany(sql, insert_data)
        
        print("Cleaning duplicate rows...")
        del_dup_rows("[EKTM_HAM].[dbo].[OPEN_METEO_FOR]", "[TIME], [LAT], [LON], [TILT], [AZIMUTH], [PARAMETER_NAME]", query_date_1, conn)

if __name__ == "__main__":
    main()