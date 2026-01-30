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

# Dewpoint levels you requested
TD_LEVELS = [1000, 950, 850, 700, 500]  # hPa

# Moisture weighting for CAPE proxy (tunable)
MOISTURE_ALPHA = 0.5


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

    has_t2m = "t2m" in ds.variables
    has_u = "u" in ds.variables
    has_v = "v" in ds.variables

    # --- Pressure and Td_3d (MetPy-version-safe) ---
    print("Preparing 3D dewpoint from q...")
    pressure_1d = ds["isobaricInhPa"].values * units.hPa  # (level,)
    q = ds["q"].values * units("kg/kg")                   # (time, level, lat, lon)

    w = mpcalc.mixing_ratio_from_specific_humidity(q)
    p4 = pressure_1d[None, :, None, None]                 # broadcast pressure to 4D
    e = mpcalc.vapor_pressure(p4, w)
    td_3d = mpcalc.dewpoint(e).to("degC").m               # (time, level, lat, lon) in °C

    dims = (ds.sizes["time"], ds.sizes["latitude"], ds.sizes["longitude"])

    # --- Outputs ---
    cape_proxy = np.full(dims, np.nan, dtype=np.float32)
    cin_arr = np.full(dims, np.nan, dtype=np.float32)
    lfc_arr = np.full(dims, np.nan, dtype=np.float32)
    el_arr = np.full(dims, np.nan, dtype=np.float32)

    cai_arr = np.full(dims, np.nan, dtype=np.float32)
    shear_1000_850 = np.full(dims, np.nan, dtype=np.float32)
    shear_950_850 = np.full(dims, np.nan, dtype=np.float32)
    lapse_1000_850 = np.full(dims, np.nan, dtype=np.float32)
    lapse_850_500 = np.full(dims, np.nan, dtype=np.float32)

    # NEW: dewpoint at requested levels (saved as additional vars)
    td_level_out = {L: np.full(dims, np.nan, dtype=np.float32) for L in TD_LEVELS}

    # Map pressure level -> index in isobaricInhPa dimension
    levs = ds["isobaricInhPa"].values
    lev_to_idx = {int(L): int(np.where(levs == L)[0][0]) for L in levs}

    # Warn if any requested Td levels are missing
    miss_td = [L for L in TD_LEVELS if L not in lev_to_idx]
    if miss_td:
        print(f"Warning: Missing Td levels in dataset (isobaricInhPa): {miss_td}")

    # Check required thermo levels exist in temperature
    needed_t_levels = [500, 700, 850, 950, 1000]
    miss_t = _require_levels(ds, needed_t_levels)
    if miss_t:
        print(f"Warning: Missing some temperature levels: {miss_t}. Some indexes will be NaN.")

    total = ds.sizes["time"]
    print(f"Starting calculations for {total} timesteps...")

    for t_idx in range(total):
        print(f"Step {t_idx+1}/{total}", end="\r")

        # -------------------------------
        # Extract Td at requested levels
        # -------------------------------
        Td = {}
        for L in TD_LEVELS:
            iL = lev_to_idx.get(L)
            if iL is None:
                continue
            Td[L] = td_3d[t_idx, iL, :, :]  # °C
            td_level_out[L][t_idx] = Td[L].astype(np.float32)

        # -------------------------------
        # CAPE Proxy (now uses Td levels)
        # -------------------------------
        # Use (T1000 - T500) minus moisture penalty from mean dewpoint depression
        # DD = T(°C) - Td(°C). Lower DD = more moisture.
        try:
            # Temperatures (K) -> convert to °C for DD
            t1000_c = ds["t"].isel(time=t_idx).sel(isobaricInhPa=1000).values - 273.15
            t950_c  = ds["t"].isel(time=t_idx).sel(isobaricInhPa=950).values  - 273.15
            t850_c  = ds["t"].isel(time=t_idx).sel(isobaricInhPa=850).values  - 273.15
            t700_c  = ds["t"].isel(time=t_idx).sel(isobaricInhPa=700).values  - 273.15
            t500_c  = ds["t"].isel(time=t_idx).sel(isobaricInhPa=500).values  - 273.15

            # Need Td at those levels (skip if any missing)
            if all(L in Td for L in TD_LEVELS):
                dd1000 = t1000_c - Td[1000]
                dd950  = t950_c  - Td[950]
                dd850  = t850_c  - Td[850]
                dd700  = t700_c  - Td[700]
                dd500  = t500_c  - Td[500]

                dd_mean = (dd1000 + dd950 + dd850 + dd700 + dd500) / 5.0

                # Instability term (°C) plus moisture effect (subtract dryness)
                cape_proxy[t_idx] = ((t1000_c - t500_c) - MOISTURE_ALPHA * dd_mean).astype(np.float32)
            else:
                # fallback (no Td available for all levels)
                cape_proxy[t_idx] = (t1000_c - t500_c).astype(np.float32)
        except Exception:
            pass

        # -------------------------------
        # Lapse-rate proxies (ΔT between levels)
        # -------------------------------
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

        # -------------------------------
        # CAI (kept, but now can also use Td fields consistently)
        # (T2m - T500) + (Td850 - Td700)
        # -------------------------------
        try:
            if has_t2m:
                t_sfc = ds["t2m"].isel(time=t_idx).values  # K
            else:
                t_sfc = ds["t"].isel(time=t_idx).sel(isobaricInhPa=1000).values  # K fallback

            t500 = ds["t"].isel(time=t_idx).sel(isobaricInhPa=500).values  # K

            if 850 in Td and 700 in Td:
                cai = (t_sfc - t500) + (Td[850] - Td[700])  # proxy
                cai_arr[t_idx] = cai.astype(np.float32)
        except Exception:
            pass

        # -------------------------------
        # Wind shear magnitudes (requires u/v at pressure levels)
        # -------------------------------
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

    data_vars = {
        "CAPE_Proxy": (("time", "latitude", "longitude"), cape_proxy),
        "CAI": (("time", "latitude", "longitude"), cai_arr),
        "Shear_1000_850": (("time", "latitude", "longitude"), shear_1000_850),
        "Shear_950_850": (("time", "latitude", "longitude"), shear_950_850),
        "Lapse_1000_850": (("time", "latitude", "longitude"), lapse_1000_850),
        "Lapse_850_500": (("time", "latitude", "longitude"), lapse_850_500),
        "CIN": (("time", "latitude", "longitude"), cin_arr),
        "LFC": (("time", "latitude", "longitude"), lfc_arr),
        "EL": (("time", "latitude", "longitude"), el_arr),
    }

    # Add Td level outputs
    for L in TD_LEVELS:
        data_vars[f"Td_{L}hPa"] = (("time", "latitude", "longitude"), td_level_out[L])

    ds_out = xr.Dataset(
        data_vars=data_vars,
        coords={
            "time": ds["time"],
            "latitude": ds["latitude"],
            "longitude": ds["longitude"],
        },
        attrs={
            "notes": (
                "CAPE_Proxy uses Td at 1000/950/850/700/500 hPa via dewpoint depression: "
                "CAPE_Proxy = (T1000-T500) - alpha*mean(T-Td). "
                "Lapse_* are temperature-difference proxies (K), not K/km (no geopotential heights provided). "
                "Shear_* are vector wind shear magnitudes between listed pressure levels."
            )
        },
    )

    encoding = {v: {"zlib": True, "complevel": 1, "dtype": "float32"} for v in ds_out.data_vars}
    ds_out.to_netcdf(OUTPUT_FILE, encoding=encoding)
    print(f"Saved derived dataset to {OUTPUT_FILE}")


if __name__ == "__main__":
    main()
