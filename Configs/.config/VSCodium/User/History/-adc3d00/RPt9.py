# app.py
from __future__ import annotations

from pathlib import Path

import xarray as xr

from src.io_era5 import open_grib, select_levels, standardize_coords
from src.cai import compute_cai_base
from src.tracking import track_cai_objects
from src.plotting import plot_cai_map, plot_track_density


DATA = Path("/home/spidy/Projects/Data/mto")  # change to your folder
SINGLE_LEVEL = Path("single_level")
PRESSURE_LEVELS = Path("pressure_levels")

def main():
    chunks2d = {"time": 48, "latitude": 200, "longitude": 200}  # tune to your machine

    # --- Surface fields (multi-year) ---
    ds_t2m = standardize_coords(open_grib([DATA / SINGLE_LEVEL / "era5_t2m_2023_2024_2025.grib"], chunks=chunks2d))
    ds_d2m = standardize_coords(open_grib([DATA / SINGLE_LEVEL / "era5_d2m_2023_2024_2025.grib"], chunks=chunks2d))
    ds_u10 = standardize_coords(open_grib([DATA / SINGLE_LEVEL / "era5_u10m_2023_2024_2025.grib"], chunks=chunks2d))
    ds_v10 = standardize_coords(open_grib([DATA / SINGLE_LEVEL / "era5_v10m_2023_2024_2025.grib"], chunks=chunks2d))

    # Variable names differ by cfgrib conventions; print(ds_t2m.data_vars) if needed
    t2m = next(iter(ds_t2m.data_vars.values()))
    d2m = next(iter(ds_d2m.data_vars.values()))
    u10 = next(iter(ds_u10.data_vars.values()))
    v10 = next(iter(ds_v10.data_vars.values()))

    # --- Pressure-level T for low-level lapse + cap ---
    # Your files are split by level groups. We'll open the 850/950/1000 set.
    t_pl_paths = [
        DATA / "era5_t_2023_850_950_1000_hPa.grib",
        DATA / "era5_t_2024_850_950_1000_hPa.grib",
        DATA / "era5_t_2025_850_950_1000_hPa.grib",
    ]
    ds_tpl = standardize_coords(open_grib(t_pl_paths, chunks=chunks2d, filter_by_keys={"typeOfLevel": "isobaricInhPa"}))
    ds_tpl = select_levels(ds_tpl, [850, 950])

    # Pressure-level winds at 850
    u_pl_paths = [
        DATA / "era5_u_2023_850_950_1000_hPa.grib",
        DATA / "era5_u_2024_850_950_1000_hPa.grib",
        DATA / "era5_u_2025_850_950_1000_hPa.grib",
    ]
    v_pl_paths = [
        DATA / "era5_v_2023_850_950_1000_hPa.grib",
        DATA / "era5_v_2024_850_950_1000_hPa.grib",
        DATA / "era5_v_2025_850_950_1000_hPa.grib",
    ]
    ds_upl = standardize_coords(open_grib(u_pl_paths, chunks=chunks2d, filter_by_keys={"typeOfLevel": "isobaricInhPa"}))
    ds_vpl = standardize_coords(open_grib(v_pl_paths, chunks=chunks2d, filter_by_keys={"typeOfLevel": "isobaricInhPa"}))

    # Identify variable names
    t_pl = next(iter(ds_tpl.data_vars.values()))
    u_pl = next(iter(ds_upl.data_vars.values()))
    v_pl = next(iter(ds_vpl.data_vars.values()))

    # Coordinate name for pressure levels
    pcoord = "isobaricInhPa" if "isobaricInhPa" in t_pl.coords else "level"

    t850 = t_pl.sel({pcoord: 850})
    t950 = t_pl.sel({pcoord: 950})
    u850 = u_pl.sel({pcoord: 850})
    v850 = v_pl.sel({pcoord: 850})

    # --- Align times (important!) ---
    # Use xarray align to ensure same time axis
    t2m_a, d2m_a, u10_a, v10_a, t950_a, t850_a, u850_a, v850_a = xr.align(
        t2m, d2m, u10, v10, t950, t850, u850, v850, join="inner"
    )

    # --- Compute CAI ---
    cai = compute_cai_base(
        t2m=t2m_a,
        d2m=d2m_a,
        u10=u10_a,
        v10=v10_a,
        t950=t950_a,
        t850=t850_a,
        u850=u850_a,
        v850=v850_a,
        norm_dim=("time",),
    )

    # Optional: save for reuse
    cai.to_dataset(name="CAI").to_netcdf(DATA / "cai_2023_2025.nc")

    # --- Tracking (example: one month subset for speed) ---
    cai_sub = cai.sel(time=slice("2024-06-01", "2024-06-07"))  # adjust
    tracks = track_cai_objects(cai_sub, threshold=0.7, min_area_cells=9, max_km_per_hour=80)

    # --- Plot an example timestep with tracks up to that time ---
    t_index = 12
    fig1 = plot_cai_map(
        cai_sub.isel(time=t_index),
        title=f"CAI + Tracks (up to t={t_index})",
        tracks=tracks,
        t_index=t_index,
    )
    fig1.savefig(DATA / "cai_tracks_example.png", dpi=150)

    fig2 = plot_track_density(cai_sub, tracks, title="Cu-object track density (subset)")
    fig2.savefig(DATA / "track_density.png", dpi=150)


if __name__ == "__main__":
    main()

