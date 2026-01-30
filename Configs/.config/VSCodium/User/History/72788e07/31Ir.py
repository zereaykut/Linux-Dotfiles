import os
import pandas as pd
from src.utils import data_downloader, extract_data, data_prep
from src.report import plot_generation_regplot, plot_dual_axis_ts, generate_pair_report


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

    df_generation = data_prep("data/generation_monthly_mean.csv", "Generation", "Date")

    df_projection = data_prep(f"data/extracted-projection-data/P_CMI5_ReMO_CM20_GHI_0000m_Euro_NUT0_S197101010130_E209912312230_INS_TIM_01m_NA-_cdf_org_01_RCP85_NA---_NA---.csv", skiprows=52)
    df = pd.merge(df_generation, df_projection, on=["Date"], how="outer")

    # --- Plot ---
    plot_generation_regplot(df, "TR", loc.split(".")[0], "data")
    plot_dual_axis_ts(df, "TR", loc.split(".")[0], "data")

    # --- Report ---


if __name__ == "__main__":
    main()
