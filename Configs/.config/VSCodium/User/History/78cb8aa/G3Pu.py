#!/usr/bin/env python3
import os
import sys
import numpy as np
import xarray as xr
import metpy.calc as mpcalc
from metpy.units import units

CACHE_DIR = "cache"
CACHE_FILE = os.path.join(CACHE_DIR, "cache_oct2025.nc")
OUTPUT_FILE = os.path.join(CACHE_DIR, "derived_oct2025.nc")

FAST_MODE = False  # keep your switch if you want later


def _require_levels(ds, levels):
    levs = ds["isobaricInhPa"].values
    missing = [L for L in levels if L not in levs]
    return missing


def main():
    if not os.path.exists(CACHE_FILE):
        print(f"Run preprocessing first. Missing: {CACHE_FILE}")
        sys.exit(1)

    ds = xr.open_dataset(CACHE_FILE)

    required = ["t", "q", "isobaricInhPa", "latitude", "longitude", "time"]
    missing_vars = [v for v in required if (v not in ds.variables and v not in ds.coords)]
    if missing_vars:
        print(f"Missing required fields in cache: {missing_vars}")
        print(f"Available: {list(ds.variables)}")
        sys.exit(1)

    # Optional but strongly recommended for CAI
    has_t2m = "t2m" in ds.variables
    has_d2m = "d2m" in ds.variables
    has_u10m = "u10m" in ds.variables
    has_v10m = "v10m" in ds.variables
    has_u = "u" in ds.variables
    has_v = "v" in ds.variables

    # --- Pressure and Td_3d (MetPy-version-safe) ---
    print("Preparing 3D dewpoint from q...")
    pressure_1d = ds["isobaricInhPa"].values * units.hPa  # (level,)
    q = ds["q"].values * units("kg/kg")                   # (time, level, lat, lon)

    w = mpcalc.mixing_ratio_from_specific_humidity(q)
    p4 = pressure_1d[None, :, None, None]
    e = mpcalc.vapor_pressure(p4, w)
    td_3d = mpcalc.dewpoint(e).to("degC").m  # (time, level, lat, lon)

    dims = (ds.sizes["time"], ds.sizes["latitude"], ds.sizes["longitude"])

    # --- Base outputs (existing) ---
    cape_proxy = np.full(dims, np.nan, dtype=np.float32)
    cin_arr = np.full(dims, np.nan, dtype=np.float32)
    lfc_arr = np.full(dims, np.nan, dtype=np.float32)
    el_arr = np.full(dims, np.nan, dtype=np.float32)

    # --- New outputs ---
    cai_arr = np.full(dims, np.nan, dtype=np.float32)

    shear_1000_850 = np.full(dims, np.nan, dtype=np.float32)
    shear_950_850 = np.full(dims, np.nan, dtype=np.float32)

    lapse_1000_850 = np.full(dims, np.nan, dtype=np.float32)  # K difference proxy
    lapse_850_500 = np.full(dims, np.nan, dtype=np.float32)   # K difference proxy

    # Check required thermo levels exist in T/Q
    needed_t_levels = [500, 700, 850, 1000]
    miss_t = _require_levels(ds, needed_t_levels)
    if miss_t:
        print(f"Warning: missing some temperature levels: {miss_t}. Some indexes will be NaN.")

    # For dewpoint levels (from q), you have 500/700/850/1000 across split files — good.
    levs = ds["isobaricInhPa"].values
    lev_to_idx = {int(L): int(np.where(levs == L)[0][0]) for L in levs}

    total = ds.sizes["time"]
    print(f"Starting calculations for {total} timesteps...")

    for t_idx in range(total):
        print(f"Step {t_idx+1}/{total}", end="\r")

        # ---- CAPE proxy (keep your original idea but consistent) ----
        try:
            t500 = ds["t"].isel(time=t_idx).sel(isobaricInhPa=500).values  # K
            if has_t2m:
                t_sfc = ds["t2m"].isel(time=t_idx).values  # K
            else:
                # fallback: 1000 hPa if present
                t_sfc = ds["t"].isel(time=t_idx).sel(isobaricInhPa=1000).values
            cape_proxy[t_idx] = (t_sfc - t500).astype(np.float32)
        except Exception:
            pass

        # ---- Lapse-rate proxies (ΔT between levels, not per-km because no heights) ----
        try:
            t1000 = ds["t"].isel(time=t_idx).sel(isobaricInhPa=1000).values
            t850 = ds["t"].isel(time=t_idx).sel(isobaricInhPa=850).values
            lapse_1000_850[t_idx] = (t1000 - t850).astype(np.float32)  # K
        except Exception:
            pass

        try:
            t850 = ds["t"].isel(time=t_idx).sel(isobaricInhPa=850).values
            t500 = ds["t"].isel(time=t_idx).sel(isobaricInhPa=500).values
            lapse_850_500[t_idx] = (t850 - t500).astype(np.float32)  # K
        except Exception:
            pass

        # ---- CAI (Cloud Activity Index) ----
        # Robust convective proxy using:
        #  (T2m - T500) + (Td850 - Td700)
        # This uses only data you have (T2m + T at 500, Td from q at 850/700).
        try:
            if has_t2m:
                t_sfc = ds["t2m"].isel(time=t_idx).values  # K
            else:
                t_sfc = ds["t"].isel(time=t_idx).sel(isobaricInhPa=1000).values  # K fallback

            t500 = ds["t"].isel(time=t_idx).sel(isobaricInhPa=500).values  # K

            i850 = lev_to_idx.get(850)
            i700 = lev_to_idx.get(700)

            if i850 is not None and i700 is not None:
                td850 = td_3d[t_idx, i850, :, :]  # °C
                td700 = td_3d[t_idx, i700, :, :]  # °C

                cai = (t_sfc - t500) + (td850 - td700)  # mixed units but stable proxy
                cai_arr[t_idx] = cai.astype(np.float32)
        except Exception:
            pass

        # ---- Wind shear magnitudes (requires u/v at pressure levels) ----
        # Your available u/v aloft: 850/950/1000 hPa (per your file list).
        if has_u and has_v:
            try:
                u1000 = ds["u"].isel(time=t_idx).sel(isobaricInhPa=1000).values
                v1000 = ds["v"].isel(time=t_idx).sel(isobaricInhPa=1000).values
                u850 = ds["u"].isel(time=t_idx).sel(isobaricInhPa=850).values
                v850 = ds["v"].isel(time=t_idx).sel(isobaricInhPa=850).values
                shear_1000_850[t_idx] = np.sqrt((u850 - u1000) ** 2 + (v850 - v1000) ** 2).astype(np.float32)
            except Exception:
                pass

            try:
                u950 = ds["u"].isel(time=t_idx).sel(isobaricInhPa=950).values
                v950 = ds["v"].isel(time=t_idx).sel(isobaricInhPa=950).values
                u850 = ds["u"].isel(time=t_idx).sel(isobaricInhPa=850).values
                v850 = ds["v"].isel(time=t_idx).sel(isobaricInhPa=850).values
                shear_950_850[t_idx] = np.sqrt((u850 - u950) ** 2 + (v850 - v950) ** 2).astype(np.float32)
            except Exception:
                pass

    print("\nCalculation complete.")

    # --- Save ---
    os.makedirs(CACHE_DIR, exist_ok=True)

    ds_out = xr.Dataset(
        data_vars={
            "CAPE_Proxy": (("time", "latitude", "longitude"), cape_proxy),
            "CAI": (("time", "latitude", "longitude"), cai_arr),
            "Shear_1000_850": (("time", "latitude", "longitude"), shear_1000_850),
            "Shear_950_850": (("time", "latitude", "longitude"), shear_950_850),
            "Lapse_1000_850": (("time", "latitude", "longitude"), lapse_1000_850),
            "Lapse_850_500": (("time", "latitude", "longitude"), lapse_850_500),
            "CIN": (("time", "latitude", "longitude"), cin_arr),
            "LFC": (("time", "latitude", "longitude"), lfc_arr),
            "EL": (("time", "latitude", "longitude"), el_arr),
        },
        coords={
            "time": ds["time"],
            "latitude": ds["latitude"],
            "longitude": ds["longitude"],
        },
        attrs={
            "notes": (
                "Indexes are proxy-style and computed using available ERA5 fields. "
                "Lapse_* are temperature-difference proxies (K), not K/km (no geopotential heights provided). "
                "Shear_* are vector wind shear magnitudes between listed pressure levels."
            )
        },
    )

    # Light compression
    encoding = {v: {"zlib": True, "complevel": 1, "dtype": "float32"} for v in ds_out.data_vars}
    ds_out.to_netcdf(OUTPUT_FILE, encoding=encoding)
    print(f"Saved derived dataset to {OUTPUT_FILE}")


if __name__ == "__main__":
    main()
