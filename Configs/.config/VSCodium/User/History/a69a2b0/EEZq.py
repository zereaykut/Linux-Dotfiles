# build_cache.py
from __future__ import annotations

from pathlib import Path

from src.zarr_build import build_zarr


def main():
    DATA = Path("/home/spidy/Projects/Data/mto")  # <- your GRIB folder

    CACHE = Path("./cache_zarr")    # <- output Zarr cache
    CACHE.mkdir(parents=True, exist_ok=True)

    # Zarr chunking (tune if needed)
    chunks = {"time": 96, "latitude": 200, "longitude": 200}

    # Optional but recommended: crop during build to save disk + speed all later steps
    # Adjust to your study domain (Turkey–Mediterranean example):
    subset = {"latitude": slice(45, 30), "longitude": slice(25, 45)}

    # -------------------------
    # Surface variables (all years)
    # -------------------------
    build_zarr(
        name="t2m",
        grib_paths=[DATA / "era5_t2m_2023_2024_2025.grib"],
        out_zarr=CACHE / "t2m.zarr",
        chunks=chunks,
        subset=subset,
    )
    build_zarr(
        name="d2m",
        grib_paths=[DATA / "era5_d2m_2023_2024_2025.grib"],
        out_zarr=CACHE / "d2m.zarr",
        chunks=chunks,
        subset=subset,
    )
    build_zarr(
        name="sp",
        grib_paths=[DATA / "era5_sp_2023_2024_2025.grib"],
        out_zarr=CACHE / "sp.zarr",
        chunks=chunks,
        subset=subset,
    )
    build_zarr(
        name="u10",
        grib_paths=[DATA / "era5_u10m_2023_2024_2025.grib"],
        out_zarr=CACHE / "u10.zarr",
        chunks=chunks,
        subset=subset,
    )
    build_zarr(
        name="v10",
        grib_paths=[DATA / "era5_v10m_2023_2024_2025.grib"],
        out_zarr=CACHE / "v10.zarr",
        chunks=chunks,
        subset=subset,
    )

    # -------------------------
    # Pressure-level temperature (T) per year
    # -------------------------
    # 2023 has extra upper levels (100/300/400) in your files
    build_zarr(
        name="t_pl_2023",
        grib_paths=[
            DATA / "era5_t_2023_850_950_1000_hPa.grib",
            DATA / "era5_t_2023_200_500_700_hPa.grib",
            DATA / "era5_t_2023_100_300_400_hPa.grib",
        ],
        out_zarr=CACHE / "t_pl_2023.zarr",
        chunks=chunks,
        filter_by_keys={"typeOfLevel": "isobaricInhPa"},
        subset=subset,
    )

    build_zarr(
        name="t_pl_2024",
        grib_paths=[
            DATA / "era5_t_2024_850_950_1000_hPa.grib",
            DATA / "era5_t_2024_200_500_700_hPa.grib",
        ],
        out_zarr=CACHE / "t_pl_2024.zarr",
        chunks=chunks,
        filter_by_keys={"typeOfLevel": "isobaricInhPa"},
        subset=subset,
    )

    build_zarr(
        name="t_pl_2025",
        grib_paths=[
            DATA / "era5_t_2025_850_950_1000_hPa.grib",
            DATA / "era5_t_2025_200_500_700_hPa.grib",
        ],
        out_zarr=CACHE / "t_pl_2025.zarr",
        chunks=chunks,
        filter_by_keys={"typeOfLevel": "isobaricInhPa"},
        subset=subset,
    )

    # -------------------------
    # Pressure-level specific humidity (q) per year
    # -------------------------
    build_zarr(
        name="q_pl_2023",
        grib_paths=[
            DATA / "era5_q_2023_850_950_1000_hPa.grib",
            DATA / "era5_q_2023_200_500_700_hPa.grib",
            DATA / "era5_q_2023_100_300_400_hPa.grib",
        ],
        out_zarr=CACHE / "q_pl_2023.zarr",
        chunks=chunks,
        filter_by_keys={"typeOfLevel": "isobaricInhPa"},
        subset=subset,
    )

    build_zarr(
        name="q_pl_2024",
        grib_paths=[
            DATA / "era5_q_2024_850_950_1000_hPa.grib",
            DATA / "era5_q_2024_200_500_700_hPa.grib",
        ],
        out_zarr=CACHE / "q_pl_2024.zarr",
        chunks=chunks,
        filter_by_keys={"typeOfLevel": "isobaricInhPa"},
        subset=subset,
    )

    build_zarr(
        name="q_pl_2025",
        grib_paths=[
            DATA / "era5_q_2025_850_950_1000_hPa.grib",
            DATA / "era5_q_2025_200_500_700_hPa.grib",
        ],
        out_zarr=CACHE / "q_pl_2025.zarr",
        chunks=chunks,
        filter_by_keys={"typeOfLevel": "isobaricInhPa"},
        subset=subset,
    )

    # -------------------------
    # Low-level wind on pressure levels (u, v) per year
    # (Only 850/950/1000 exist in your files)
    # -------------------------
    for year in (2023, 2024, 2025):
        build_zarr(
            name=f"u_pl_low_{year}",
            grib_paths=[DATA / f"era5_u_{year}_850_950_1000_hPa.grib"],
            out_zarr=CACHE / f"u_pl_low_{year}.zarr",
            chunks=chunks,
            filter_by_keys={"typeOfLevel": "isobaricInhPa"},
            subset=subset,
        )
        build_zarr(
            name=f"v_pl_low_{year}",
            grib_paths=[DATA / f"era5_v_{year}_850_950_1000_hPa.grib"],
            out_zarr=CACHE / f"v_pl_low_{year}.zarr",
            chunks=chunks,
            filter_by_keys={"typeOfLevel": "isobaricInhPa"},
            subset=subset,
        )

    print("\n✅ build_cache.py completed. Zarr stores are in:", CACHE.resolve())


if __name__ == "__main__":
    main()
