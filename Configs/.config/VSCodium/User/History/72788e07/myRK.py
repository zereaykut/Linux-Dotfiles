import os
import pandas as pd
from src.utils import data_downloader, extract_data, data_prep
from src.report import plot_generation_regplot, plot_dual_axis_ts, generate_pair_report
from src.model import model_data, model_lr, model_rf


def main() -> None:
    # --- Data Download ---
    request = {
        "variable": [
            "wind_speed_at_100m",
            "wind_speed_at_10m",
            "surface_downwelling_shortwave_radiation",
            "2m_air_temperature",
            "total_precipitation",
            "electricity_demand",
            "hydro_power_generation_reservoirs",
            "hydro_power_generation_rivers",
        ],
        "spatial_aggregation": "country_level",  # country_level, sub_country_level, j
        "energy_product_type": ["energy"],
        "temporal_aggregation": "monthly",
        "experiment": ["rcp_4_5", "rcp_8_5"],
        "rcm": "regcm4",
        "gcm": ["hadgem2_es"],
    }
    # to setup cdsapi: https://cds.climate.copernicus.eu/how-to-api
    # data_downloader(request)

    # --- Data Extract ---
    # extract_data("data/projection-data.zip", "data/extracted-projection-data")

    # --- Data Prep ---
    data_list = os.listdir("data/extracted-projection-data")
    filename = data_list[1]

    df_generation = data_prep("data/generation_monthly_mean.csv", "Generation", "Date")

    df_projection = data_prep(f"data/extracted-projection-data/{filename}", skiprows=52)
    df = pd.merge(df_generation, df_projection, on=["Date"], how="inner")

    # --- Plot ---
    plot_generation_regplot(df, "TR", "Deneme")
    plot_dual_axis_ts(df, "TR", "Deneme")

    # --- Report ---
    generate_pair_report(df, "TR", "Deneme")



    # --- Model Test ---
    model_lr(df_model, "Generation", train_start="2023-01-01", train_end="2024-12-31", pred_start="2025-01-01", pred_end="2025-12-31", test=True)
    model_lrf(df_model, "Generation", train_start="2023-01-01", train_end="2024-12-31", pred_start="2025-01-01", pred_end="2025-12-31", test=True)

    # --- Model Prediction ---
    model_lr(df_model, "Generation", train_start="2023-01-01", train_end="2025-12-31", pred_start="2028-01-01", pred_end="2028-12-31")
    model_lrf(df_model, "Generation", train_start="2023-01-01", train_end="2025-12-31", pred_start="2028-01-01", pred_end="2028-12-31")


if __name__ == "__main__":
    main()
