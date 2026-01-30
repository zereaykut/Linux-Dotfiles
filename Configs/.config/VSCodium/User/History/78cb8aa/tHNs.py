#!/usr/bin/env python3
"""
02_thermo_calc.py

- Reads preprocessed ERA5 cache file (CACHE_FILE).
- Computes 3D dewpoint from specific humidity using a MetPy-version-safe method:
    q -> mixing ratio w -> vapor pressure e -> dewpoint Td
- Then runs either:
    FAST_MODE=True  -> K-Index (instant)
    FAST_MODE=False -> (currently) a fast CAPE proxy (lapse-rate style), plus placeholder arrays for CIN/LFC/EL

Notes / Fixes applied:
- Removed mpcalc.dewpoint_from_mixing_ratio (not available in your MetPy version).
- Corrected Td units in FULL mode: Td is in degC for dewpoint fields.
- FAST_MODE K-index block now uses derived Td from q (no reliance on ds['td'] existing).
"""

import os
import sys
import numpy as np
import xarray as xr
import metpy.calc as mpcalc
from metpy.units import units

CACHE_FILE = "cache_oct2025.nc"
OUTPUT_FILE = "derived_oct2025.nc"

# Set to False to calculate proxy fields (fast) or real CAPE (very slow if per-gridpoint).
# Set to True to calculate K-Index only (instant).
FAST_MODE = False


def calculate_single_point(p, T, Td):
    """
    Helper to calc CAPE/CIN/LFC/EL for a single vertical profile.
    Inputs:
      p  : 1D pressure profile with units (e.g., hPa)
      T  : 1D temperature profile with units (e.g., K)
      Td : 1D dewpoint profile with units (e.g., degC)

    Returns: CAPE(J/kg), CIN(J/kg), LFC_pressure(hPa), EL_pressure(hPa) as floats
    """
    try:
        # Surface-based parcel: use first level as "surface" of profile
        prof = mpcalc.parcel_profile(p, T[0], Td[0]).to("kelvin")

        cape, cin = mpcalc.cape_cin(p, T, Td, prof)

        lfc_p, _ = mpcalc.lfc(p, T, Td)
        el_p, _ = mpcalc.el(p, T, Td)

        # .m gives magnitude without units
        return float(cape.m), float(cin.m), float(lfc_p.m), float(el_p.m)
    except Exception:
        return np.nan, np.nan, np.nan, np.nan


def main():
    if not os.path.exists(CACHE_FILE):
        print(f"Run preprocessing first. Missing: {CACHE_FILE}")
        sys.exit(1)

    ds = xr.open_dataset(CACHE_FILE)

    # -----------------------------
    # Required variables check
    # -----------------------------
    required = ["t", "q", "isobaricInhPa"]
    missing = [v for v in required if v not in ds.variables and v not in ds.coords]
    if missing:
        print(f"Missing required fields in cache file: {missing}")
        print(f"Available variables: {list(ds.variables)}")
        sys.exit(1)

    # Optional (for FULL mode proxy)
    # sp, t2m, d2m recommended; if missing, we'll fall back to lowest model level
    has_sp = "sp" in ds.variables
    has_t2m = "t2m" in ds.variables
    has_d2m = "d2m" in ds.variables

    # -----------------------------
    # 1) Prepare pressure + Td_3d
    # -----------------------------
    print("Preparing 3D fields...")

    # Pressure levels (hPa), 1D
    pressure_1d = ds["isobaricInhPa"].values * units.hPa  # shape: (level,)

    # Specific humidity q: (time, level, lat, lon)
    q = ds["q"].values * units("kg/kg")

    # MetPy-safe dewpoint from mixing ratio:
    # q -> mixing ratio w -> vapor pressure e -> dewpoint Td
    w = mpcalc.mixing_ratio_from_specific_humidity(q)  # dimensionless
    p4 = pressure_1d[None, :, None, None]             # broadcast to 4D
    e = mpcalc.vapor_pressure(p4, w)                  # vapor pressure (same shape as q)
    td_3d = mpcalc.dewpoint(e).to("degC").m           # numpy array (time, level, lat, lon) in °C

    # Output dimensions
    dims = (ds.sizes["time"], ds.sizes["latitude"], ds.sizes["longitude"])
    cape_arr = np.full(dims, np.nan, dtype=np.float32)
    cin_arr = np.full(dims, np.nan, dtype=np.float32)
    lfc_arr = np.full(dims, np.nan, dtype=np.float32)
    el_arr = np.full(dims, np.nan, dtype=np.float32)

    times = ds["time"].values
    total = len(times)

    print(f"Starting calculations for {total} time steps...")

    # -----------------------------
    # 2) Loop over time
    # -----------------------------
    for t_idx in range(total):
        print(f"Step {t_idx+1}/{total}", end="\r")

        if FAST_MODE:
            # -----------------------------
            # FAST MODE: K-Index (vectorized)
            # K = (T850 - T500) + Td850 - (T700 - Td700)
            # We use Td from td_3d (computed from q) to avoid relying on ds['td'].
            # -----------------------------
            try:
                # Temperatures in °C
                t850 = ds["t"].isel(time=t_idx).sel(isobaricInhPa=850).values - 273.15
                t700 = ds["t"].isel(time=t_idx).sel(isobaricInhPa=700).values - 273.15
                t500 = ds["t"].isel(time=t_idx).sel(isobaricInhPa=500).values - 273.15

                # Dewpoints in °C (from td_3d)
                # Find indices for those levels (safe)
                levs = ds["isobaricInhPa"].values
                i850 = int(np.where(levs == 850)[0][0])
                i700 = int(np.where(levs == 700)[0][0])

                td850 = td_3d[t_idx, i850, :, :]
                td700 = td_3d[t_idx, i700, :, :]

                cape_arr[t_idx, :, :] = (t850 - t500) + td850 - (t700 - td700)
            except Exception:
                # Leave NaNs if something goes wrong
                pass

        else:
            # -----------------------------
            # FULL MODE (still fast): CAPE proxy / instability proxy
            # Your original code used (t_sfc - t_500) as a simple lapse proxy.
            # We'll keep that, but make it robust if sp/t2m/d2m are missing.
            # -----------------------------
            try:
                t500 = ds["t"].isel(time=t_idx).sel(isobaricInhPa=500).values  # K

                if has_t2m:
                    t_sfc = ds["t2m"].isel(time=t_idx).values  # K
                else:
                    # fallback: lowest pressure level temperature at each gridpoint
                    # (depends on ordering of isobaric levels; ERA5 often goes from 1000->1, but not guaranteed)
                    # We'll use the max pressure level as "lowest altitude"
                    levs = ds["isobaricInhPa"].values
                    i_sfc = int(np.argmax(levs))
                    t_sfc = ds["t"].isel(time=t_idx, isobaricInhPa=i_sfc).values  # K

                # Simple lapse-rate proxy (K): warmer surface vs colder mid-troposphere
                cape_arr[t_idx, :, :] = (t_sfc - t500).astype(np.float32)

                # cin_arr/lfc_arr/el_arr remain NaN unless you implement real CAPE below.
            except Exception:
                pass

            # ------------------------------------------------------------
            # OPTIONAL: REAL CAPE/CIN (VERY SLOW) - per gridpoint profiles
            # Uncomment and use carefully (consider subsetting / coarsening).
            # ------------------------------------------------------------
            # pressure_profile = pressure_1d  # (level,) with units
            # T_step = ds["t"].isel(time=t_idx).values * units.kelvin        # (level, lat, lon)
            # Td_step = td_3d[t_idx] * units.degC                            # (level, lat, lon)
            #
            # for y in range(T_step.shape[1]):
            #     for x in range(T_step.shape[2]):
            #         T_prof = T_step[:, y, x]
            #         Td_prof = Td_step[:, y, x]
            #
            #         # skip if missing
            #         if np.any(np.isnan(T_prof.m)) or np.any(np.isnan(Td_prof.m)):
            #             continue
            #
            #         cape, cin, lfc_p, el_p = calculate_single_point(pressure_profile, T_prof, Td_prof)
            #         cape_arr[t_idx, y, x] = cape
            #         cin_arr[t_idx, y, x] = cin
            #         lfc_arr[t_idx, y, x] = lfc_p
            #         el_arr[t_idx, y, x] = el_p

    print("\nCalculation Loop Complete.")

    # -----------------------------
    # 3) Save Results
    # -----------------------------
    ds_out = xr.Dataset(
        data_vars={
            "CAPE_Proxy": (("time", "latitude", "longitude"), cape_arr),
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
            "notes": "CAPE_Proxy is a fast instability proxy in FULL mode; set FAST_MODE=True for K-Index.",
        },
    )

    ds_out.to_netcdf(OUTPUT_FILE)
    print(f"Saved to {OUTPUT_FILE}")


if __name__ == "__main__":
    main()
