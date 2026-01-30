# 🌤️ Open-Meteo Data Pipeline

A robust Python data pipeline designed to retrieve, process, and store meteorological data using the [Open-Meteo API](https://open-meteo.com/). This project provides modular scripts for fetching **Forecasts**, **Historical Archives**, and **Climate Projections**, formatting them into clean CSV datasets for analysis.

## 🚀 Features

- **Multi-Domain Data Retrieval**:
  - **Forecasts**: 7-day hourly forecast (Temperature, Wind Speed, Solar Radiation).
  - **Historical**: Hourly archive data retrieval for past dates.
  - **Climate Models**: Long-term daily climate projections (e.g., MRI_AGCM3_2_S).
- **Error Handling**: Implements retry logic (backoff strategies) for stable API requests.
- **Data Standardization**: Automatically processes JSON responses into structured Pandas DataFrames.
- **Timezone Handling**: Adjusts UTC timestamps to local time (UTC+3).

## 📂 Project Structure

```bash
.
├── get_climate_data.py    # Script for long-term climate model projections
├── get_forecast_data.py   # Script for short-term hourly weather forecasts
├── get_historical_data.py # Script for retrospective historical weather data
├── README.md              # Project documentation
└── src
    ├── __init__.py
    └── utils.py           # Core utilities: API wrappers, retry logic, file handling