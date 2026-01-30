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

# Dewpoint levels you requested (hPa)
TD_LEVELS = [1000, 950, 850, 700, 500]

# Moisture weighting for CAPE proxy (tunable)
MOISTURE_ALPHA = 0.5


def _require_levels(ds, levels):
    levs = ds["isobaricInhPa"].values
    missing = [L for L in levels if L not in levs]
    return missing


def lfc_from_5level_profile(
    T1000_c, T950_c, T850_c, T700_c, T500_c,
    Td1000_c, Td950_c, Td850_c, Td700_c, Td500_c
) -> float:
    """
    Compute surface-based LFC pressure (hPa) for ONE gridpoint using 5 pressure levels.
    Returns np.nan if it cannot be computed or no LFC exists.
    """
    try:
        p = np.array([1000, 950, 850, 700, 500], dtype=np.float64) * units.hPa

        # MetPy expects temperature in K and Td in °C (or K), but we'll pass:
        T = (np.array([T1000_c, T950_c, T850_c, T700_c, T500_c], dtype=np.float64) * units.degC).to("kelvin")
        Td = np.array([Td1000_c, Td950_c, Td850_c, Td700_c, Td500_c], dtype=np.float64) * units.degC

        # Compute LFC
        lfc_p, _ = mpcalc.lfc(p, T, Td)
        return float(lfc_p.to("hPa").m)
    except Exception:
        return np.nan


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

    # ---- Check that levels exist in T/Q ----
    miss_t = _require_levels(ds, TD_LEVELS)
    if miss_t:
        print(f"Warning: Missing temperature levels: {miss_t}. LFC and Td fields may be NaN.")

    # --- Pressure and Td_3d (MetPy-version-safe) ---
    print("Preparing 3D dewpoint from q...")
    pressure_1d = ds["isobaricInhPa"].values * units.hPa  # (level,)
    q = ds["q"].values * units("kg/kg")                   # (time, level, lat, lon)

    w = mpcalc.mixing_ratio_from_specific_humidity(q)
    p4 = pressure_1d[None, :, None, None]                 # broadcast to 4D
    e = mpcalc.vapor_pressure(p4, w)
    td_3d = mpcalc.dewpoint(e).to("degC").m               # (time, level, lat, lon) in °C

    # Map pressure level -> index in isobaricInhPa dimension
    levs = ds["isobaricInhPa"].values
    lev_to_idx = {int(L): int(np.where(levs == L)[0][0]) for L in levs}

    miss_td = [L for L in TD_LEVELS if L not in lev_to_idx]
    if miss_td:
        print(f"Warning: Missing Td levels in dataset (isobaricInhPa): {miss_td}")

    dims = (ds.sizes["time"], ds.sizes["latitude"], ds.sizes["longitude"])

    # --- Outputs ---
    cape_proxy = np.full(dims, np.nan, dtype=np.float32)
    cai_arr = np.full(dims, np.nan, dtype=np.float32)

    shear_1000_850 = np.full(dims, np.nan, dtype=np.float32)
    shear_950_850 = np.full(dims, np.nan, dtype=np.float32)

    lapse_1000_850 = np.full(dims, np.nan, dtype=np.float32)
    lapse_850_500 = np.full(dims, np.nan, dtype=np.float32)

    # LFC output (hPa)
    lfc_arr = np.full(dims, np.nan, dtype=np.float32)

    # Keep placeholders (if you later compute them)
    cin_arr = np.full(dims, np.nan, dtype=np.float32)
    el_arr = np.full(dims, np.nan, dtype=np.float32)

    # Save Td levels too
    td_level_out = {L: np.full(dims, np.nan, dtype=np.float32) for L in TD_LEVELS}

    total = ds.sizes["time"]
    ny = ds.sizes["latitude"]
    nx = ds.sizes["longitude"]

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
        # CAPE Proxy (uses Td levels)
        # -------------------------------
        try:
            t1000_c = ds["t"].isel(time=t_idx).sel(isobaricInhPa=1000).values - 273.15
            t950_c  = ds["t"].isel(time=t_idx).sel(isobaricInhPa=950).values  - 273.15
            t850_c  = ds["t"].isel(time=t_idx).sel(isobaricInhPa=850).values  - 273.15
            t700_c  = ds["t"].isel(time=t_idx).sel(isobaricInhPa=700).values  - 273.15
            t500_c  = ds["t"].isel(time=t_idx).sel(isobaricInhPa=500).values  - 273.15

            if all(L in Td for L in TD_LEVELS):
                dd1000 = t1000_c - Td[1000]
                dd950  = t950_c  - Td[950]
                dd850  = t850_c  - Td[850]
                dd700  = t700_c  - Td[700]
                dd500  = t500_c  - Td[500]
                dd_mean = (dd1000 + dd950 + dd850 + dd700 + dd500) / 5.0

                cape_proxy[t_idx] = ((t1000_c - t500_c) - MOISTURE_ALPHA * dd_mean).astype(np.float32)
            else:
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
        # CAI (T2m - T500) + (Td850 - Td700)
        # -------------------------------
        try:
            if has_t2m:
                t_sfc = ds["t2m"].isel(time=t_idx).values  # K
            else:
                t_sfc = ds["t"].isel(time=t_idx).sel(isobaricInhPa=1000).values  # K fallback

            t500 = ds["t"].isel(time=t_idx).sel(isobaricInhPa=500).values  # K

            if 850 in Td and 700 in Td:
                cai = (t_sfc - t500) + (Td[850] - Td[700])
                cai_arr[t_idx] = cai.astype(np.float32)
        except Exception:
            pass

        # -------------------------------
        # Wind shear magnitudes (u/v at pressure levels)
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

        # -------------------------------
        # ✅ NEW: LFC calculation using Td at 1000/950/850/700/500
        # -------------------------------
        # This is per-gridpoint. With only 5 levels, it’s manageable but still a loop.
        try:
            # If any Td missing, skip
            if not all(L in Td for L in TD_LEVELS):
                continue

            # Temperatures in °C for each required level (2D arrays)
            T1000 = ds["t"].isel(time=t_idx).sel(isobaricInhPa=1000).values - 273.15
            T950  = ds["t"].isel(time=t_idx).sel(isobaricInhPa=950).values  - 273.15
            T850  = ds["t"].isel(time=t_idx).sel(isobaricInhPa=850).values  - 273.15
            T700  = ds["t"].isel(time=t_idx).sel(isobaricInhPa=700).values  - 273.15
            T500  = ds["t"].isel(time=t_idx).sel(isobaricInhPa=500).values  - 273.15

            Td1000 = Td[1000]
            Td950  = Td[950]
            Td850  = Td[850]
            Td700  = Td[700]
            Td500  = Td[500]

            # Loop over grid
            for j in range(ny):
                for i in range(nx):
                    # skip missing
                    if (
                        np.isnan(T1000[j, i]) or np.isnan(T950[j, i]) or np.isnan(T850[j, i]) or
                        np.isnan(T700[j, i]) or np.isnan(T500[j, i]) or
                        np.isnan(Td1000[j, i]) or np.isnan(Td950[j, i]) or np.isnan(Td850[j, i]) or
                        np.isnan(Td700[j, i]) or np.isnan(Td500[j, i])
                    ):
                        continue

                    lfc_p = lfc_from_5level_profile(
                        T1000[j, i], T950[j, i], T850[j, i], T700[j, i], T500[j, i],
                        Td1000[j, i], Td950[j, i], Td850[j, i], Td700[j, i], Td500[j, i],
                    )
                    lfc_arr[t_idx, j, i] = np.float32(lfc_p)

        except Exception:
            pass

    print("\nCalculation complete.")

    os.makedirs(CACHE_DIR, exist_ok=True)

    # Build output vars
    data_vars = {
        "CAPE_Proxy": (("time", "latitude", "longitude"), cape_proxy),
        "CAI": (("time", "latitude", "longitude"), cai_arr),
        "Shear_1000_850": (("time", "latitude", "longitude"), shear_1000_850),
        "Shear_950_850": (("time", "latitude", "longitude"), shear_950_850),
        "Lapse_1000_850": (("time", "latitude", "longitude"), lapse_1000_850),
        "Lapse_850_500": (("time", "latitude", "longitude"), lapse_850_500),
        "LFC": (("time", "latitude", "longitude"), lfc_arr),
        "CIN": (("time", "latitude", "longitude"), cin_arr),
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
                "LFC is computed as surface-based LFC pressure (hPa) using 5-level profiles "
                "(1000/950/850/700/500 hPa) and dewpoints derived from q. "
                "CAPE_Proxy uses dewpoint depression mean(T-Td) with alpha scaling. "
                "Lapse_* are ΔT proxies (K), not K/km (no geopotential heights provided). "
                "Shear_* are vector wind shear magnitudes between listed pressure levels."
            )
        },
    )

    encoding = {v: {"zlib": True, "complevel": 1, "dtype": "float32"} for v in ds_out.data_vars}
    ds_out.to_netcdf(OUTPUT_FILE, encoding=encoding)
    print(f"Saved derived dataset to {OUTPUT_FILE}")


if __name__ == "__main__":
    main()
