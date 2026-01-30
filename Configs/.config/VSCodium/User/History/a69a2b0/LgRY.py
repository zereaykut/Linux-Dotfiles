from pathlib import Path
from src.zarr_build import build_zarr

DATA = Path("/home/spidy/Projects/Data/mto")  # change to your folder
SINGLE_LEVEL = Path("single_level")
PRESSURE_LEVELS = Path("pressure_levels")

CACHE = Path("./cache_zarr")

chunks = {"time": 96, "latitude": 200, "longitude": 200}

# OPTIONAL: Build Zarr already cropped to your study area (saves disk + time later)
subset = {"latitude": slice(45, 30), "longitude": slice(25, 45)}

build_zarr(
    name="t2m",
    grib_paths=[DATA/"era5_t2m_2023_2024_2025.grib"],
    out_zarr=CACHE/"t2m.zarr",
    chunks=chunks,
    subset=subset,
)

build_zarr(
    name="d2m",
    grib_paths=[DATA/"era5_d2m_2023_2024_2025.grib"],
    out_zarr=CACHE/"d2m.zarr",
    chunks=chunks,
    subset=subset,
)

build_zarr(
    name="u10",
    grib_paths=[DATA/"era5_u10m_2023_2024_2025.grib"],
    out_zarr=CACHE/"u10.zarr",
    chunks=chunks,
    subset=subset,
)

build_zarr(
    name="v10",
    grib_paths=[DATA/"era5_v10m_2023_2024_2025.grib"],
    out_zarr=CACHE/"v10.zarr",
    chunks=chunks,
    subset=subset,
)

# Pressure-level temperature (850/950/1000 group)
build_zarr(
    name="t_pl_low",
    grib_paths=[
        DATA/"era5_t_2023_850_950_1000_hPa.grib",
        DATA/"era5_t_2024_850_950_1000_hPa.grib",
        DATA/"era5_t_2025_850_950_1000_hPa.grib",
    ],
    out_zarr=CACHE/"t_pl_low.zarr",
    chunks=chunks,
    filter_by_keys={"typeOfLevel": "isobaricInhPa"},
    subset=subset,
)

build_zarr(
    name="u_pl_low",
    grib_paths=[
        DATA/"era5_u_2023_850_950_1000_hPa.grib",
        DATA/"era5_u_2024_850_950_1000_hPa.grib",
        DATA/"era5_u_2025_850_950_1000_hPa.grib",
    ],
    out_zarr=CACHE/"u_pl_low.zarr",
    chunks=chunks,
    filter_by_keys={"typeOfLevel": "isobaricInhPa"},
    subset=subset,
)

build_zarr(
    name="v_pl_low",
    grib_paths=[
        DATA/"era5_v_2023_850_950_1000_hPa.grib",
        DATA/"era5_v_2024_850_950_1000_hPa.grib",
        DATA/"era5_v_2025_850_950_1000_hPa.grib",
    ],
    out_zarr=CACHE/"v_pl_low.zarr",
    chunks=chunks,
    filter_by_keys={"typeOfLevel": "isobaricInhPa"},
    subset=subset,
)

