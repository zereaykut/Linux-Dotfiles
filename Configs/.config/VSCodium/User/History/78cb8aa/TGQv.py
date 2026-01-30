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

# Pressure levels (hPa) used for Td and parcel-based calculations
TD_LEVELS = [1000, 950, 850, 700, 500]  # hPa

# Moisture weighting for CAPE proxy (tunable)
MOISTURE_ALPHA = 0.5


def _require_levels(ds, levels):
    levs = ds["isobaricInhPa"].values
    return [L for L in levels if L not in levs]


def _safe_level_index_map(ds):
    levs = ds["isobaricInhPa"].values
    return {int(L): int(np.where(levs == L)[0][0]) for L in levs}


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
    has_u10m = "u10m" in ds.variables
    has_v10m = "v10m" in ds.variables

    # Check required thermo levels exist
    miss_t = _require_levels(ds, TD_LEVELS)
    if miss_t:
        print(f"Warning: Missing some temperature levels: {miss_t}. Some indexes will be NaN.")

    # --- Compute Td_3d from q (MetPy-version-safe) ---
    print("Preparing 3D dewpoint from q...")
    pressure_1d = ds["isobaricInhPa"].values * units.hPa  # (level,)
    q = ds["q"].values * units("kg/kg")                   # (time, level, lat, lon)

    w = mpcalc.mixing_ratio_from_specific_humidity(q)
    p4 = pressure_1d[None, :, None, None]                 # broadcast pressure to 4D
    e = mpcalc.vapor_pressure(p4, w)
    td_3d = mpcalc.dewpoint(e).to("degC").m               # (time, level, lat, lon), °C

    dims = (ds.sizes["time"], ds.sizes["latitude"], ds.sizes["longitude"])

    # --- Outputs (existing) ---
    cape_proxy = np.full(dims, np.nan, dtype=np.float32)
    cin_arr = np.full(dims, np.nan, dtype=np.float32)
    # lfc_arr = np.full(dims, np.nan, dtype=np.float32)
    el_arr = np.full(dims, np.nan, dtype=np.float32)

    cai_arr = np.full(dims, np.nan, dtype=np.float32)
    shear_1000_850 = np.full(dims, np.nan, dtype=np.float32)
    shear_950_850 = np.full(dims, np.nan, dtype=np.float32)
    lapse_1000_850 = np.full(dims, np.nan, dtype=np.float32)
    lapse_850_500 = np.full(dims, np.nan, dtype=np.float32)

    # --- NEW outputs requested ---
    k_index = np.full(dims, np.nan, dtype=np.float32)
    total_totals = np.full(dims, np.nan, dtype=np.float32)
    lifted_index_500 = np.full(dims, np.nan, dtype=np.float32)   # LI at 500 hPa from 1000 hPa parcel
    showalter_index = np.full(dims, np.nan, dtype=np.float32)    # SI at 500 hPa from 850 hPa parcel
    dd_850 = np.full(dims, np.nan, dtype=np.float32)
    dd_700 = np.full(dims, np.nan, dtype=np.float32)
    convergence_10m = np.full(dims, np.nan, dtype=np.float32)

    # Dewpoint outputs at requested levels (saved as additional vars)
    td_level_out = {L: np.full(dims, np.nan, dtype=np.float32) for L in TD_LEVELS}

    # Map pressure level -> index
    lev_to_idx = _safe_level_index_map(ds)
    miss_td = [L for L in TD_LEVELS if L not in lev_to_idx]
    if miss_td:
        print(f"Warning: Missing Td levels in dataset (isobaricInhPa): {miss_td}")

    # Precompute grid deltas for convergence (once)
    dx = dy = None
    if has_u10m and has_v10m:
        try:
            lats = ds["latitude"].values
            lons = ds["longitude"].values
            lon2d, lat2d = np.meshgrid(lons, lats)
            dx, dy = mpcalc.lat_lon_grid_deltas(lon2d, lat2d)  # meters, with units
        except Exception:
            dx = dy = None

    total_t = ds.sizes["time"]
    ny = ds.sizes["latitude"]
    nx = ds.sizes["longitude"]

    print(f"Starting calculations for {total_t} timesteps...")

    for t_idx in range(total_t):
        print(f"Step {t_idx+1}/{total_t}", end="\r")

        # --- Td at requested levels ---
        Td = {}
        for L in TD_LEVELS:
            iL = lev_to_idx.get(L)
            if iL is None:
                continue
            Td[L] = td_3d[t_idx, iL, :, :]  # °C (2D)
            td_level_out[L][t_idx] = Td[L].astype(np.float32)

        # --- Temperatures at key levels in °C (2D) ---
        try:
            t1000_c = ds["t"].isel(time=t_idx).sel(isobaricInhPa=1000).values - 273.15
            t950_c  = ds["t"].isel(time=t_idx).sel(isobaricInhPa=950).values  - 273.15
            t850_c  = ds["t"].isel(time=t_idx).sel(isobaricInhPa=850).values  - 273.15
            t700_c  = ds["t"].isel(time=t_idx).sel(isobaricInhPa=700).values  - 273.15
            t500_c  = ds["t"].isel(time=t_idx).sel(isobaricInhPa=500).values  - 273.15
        except Exception:
            # if core levels missing, skip most diagnostics for this time
            continue

        # --- CAPE Proxy using Td levels (as you already do) ---
        try:
            if all(L in Td for L in TD_LEVELS):
                dd1000 = t1000_c - Td[1000]
                dd950_ = t950_c  - Td[950]
                dd850_ = t850_c  - Td[850]
                dd700_ = t700_c  - Td[700]
                dd500_ = t500_c  - Td[500]

                dd_mean = (dd1000 + dd950_ + dd850_ + dd700_ + dd500_) / 5.0
                cape_proxy[t_idx] = ((t1000_c - t500_c) - MOISTURE_ALPHA * dd_mean).astype(np.float32)
            else:
                cape_proxy[t_idx] = (t1000_c - t500_c).astype(np.float32)
        except Exception:
            pass

        # --- Lapse proxies (ΔT) ---
        try:
            lapse_1000_850[t_idx] = ( (t1000_c + 273.15) - (t850_c + 273.15) ).astype(np.float32)  # K
        except Exception:
            pass
        try:
            lapse_850_500[t_idx] = ( (t850_c + 273.15) - (t500_c + 273.15) ).astype(np.float32)   # K
        except Exception:
            pass

        # --- CAI: (T2m - T500) + (Td850 - Td700) ---
        try:
            if has_t2m:
                t_sfc_k = ds["t2m"].isel(time=t_idx).values
            else:
                t_sfc_k = ds["t"].isel(time=t_idx).sel(isobaricInhPa=1000).values
            if 850 in Td and 700 in Td:
                cai_arr[t_idx] = ((t_sfc_k - (t500_c + 273.15)) + (Td[850] - Td[700])).astype(np.float32)
        except Exception:
            pass

        # --- Wind shear magnitudes (needs u/v at levels) ---
        if has_u and has_v:
            try:
                u1000 = ds["u"].isel(time=t_idx).sel(isobaricInhPa=1000).values
                v1000 = ds["v"].isel(time=t_idx).sel(isobaricInhPa=1000).values
                u850  = ds["u"].isel(time=t_idx).sel(isobaricInhPa=850).values
                v850  = ds["v"].isel(time=t_idx).sel(isobaricInhPa=850).values
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

        # ==========================================================
        # NEW: K Index, Total Totals, Dewpoint Depression (vectorized)
        # ==========================================================
        try:
            if (850 in Td) and (700 in Td):
                dd_850[t_idx] = (t850_c - Td[850]).astype(np.float32)
                dd_700[t_idx] = (t700_c - Td[700]).astype(np.float32)

            if (850 in Td) and (700 in Td):
                # K-Index: (T850 - T500) + Td850 - (T700 - Td700)
                k_index[t_idx] = ((t850_c - t500_c) + Td[850] - (t700_c - Td[700])).astype(np.float32)

            if 850 in Td:
                # Total Totals: (T850 - T500) + (Td850 - T500) = T850 + Td850 - 2*T500
                total_totals[t_idx] = (t850_c + Td[850] - 2.0 * t500_c).astype(np.float32)
        except Exception:
            pass

        # ==========================================================
        # NEW: Convergence_10m = -divergence(u10, v10)  (vectorized)
        # ==========================================================
        if has_u10m and has_v10m and (dx is not None) and (dy is not None):
            try:
                u10 = ds["u10m"].isel(time=t_idx).values * units("m/s")
                v10 = ds["v10m"].isel(time=t_idx).values * units("m/s")
                div = mpcalc.divergence(u10, v10, dx=dx, dy=dy)  # 1/s
                convergence_10m[t_idx] = (-div).to("1/s").m.astype(np.float32)
            except Exception:
                pass

        # ==========================================================
        # NEW: Lifted Index (500) + Showalter Index + LFC (per-column)
        # ==========================================================
        # LI: T500_env - Tparcel(1000->500)
        # SI: T500_env - Tparcel(850->500)
        # LFC: surface-based using 5 levels
        #
        # With only 5 levels, this is coarse but still useful for tracking.
        if all(L in Td for L in TD_LEVELS):
            p_prof = np.array([1000, 950, 850, 700, 500], dtype=np.float64) * units.hPa

            # For environmental T we pass Kelvin to MetPy
            # Build 3D (level, y, x) arrays quickly for the loop by referencing the 2D level arrays
            # (Converted inside loop for safety/clarity).
            for j in range(ny):
                for i in range(nx):
                    # Skip if any missing
                    if (
                        np.isnan(t1000_c[j, i]) or np.isnan(t950_c[j, i]) or np.isnan(t850_c[j, i]) or
                        np.isnan(t700_c[j, i]) or np.isnan(t500_c[j, i]) or
                        np.isnan(Td[1000][j, i]) or np.isnan(Td[950][j, i]) or np.isnan(Td[850][j, i]) or
                        np.isnan(Td[700][j, i]) or np.isnan(Td[500][j, i])
                    ):
                        continue

                    # Environmental profile
                    T_env = (np.array(
                        [t1000_c[j, i], t950_c[j, i], t850_c[j, i], t700_c[j, i], t500_c[j, i]],
                        dtype=np.float64
                    ) * units.degC).to("kelvin")

                    Td_env = np.array(
                        [Td[1000][j, i], Td[950][j, i], Td[850][j, i], Td[700][j, i], Td[500][j, i]],
                        dtype=np.float64
                    ) * units.degC

                    # ----- LFC (surface-based) -----
                    # try:
                    #     lfc_p, _ = mpcalc.lfc(p_prof, T_env, Td_env)
                    #     lfc_arr[t_idx, j, i] = np.float32(lfc_p.to("hPa").m)
                    # except Exception:
                    #     # keep NaN
                    #     pass

                    # ----- Lifted Index at 500 (parcel starts at 1000) -----
                    try:
                        T0 = (t1000_c[j, i] * units.degC).to("kelvin")
                        Td0 = Td[1000][j, i] * units.degC
                        prof1000 = mpcalc.parcel_profile(p_prof, T0, Td0).to("kelvin")
                        Tparcel500 = mpcalc.log_interpolate_1d(500.0 * units.hPa, p_prof, prof1000)
                        # LI = T500_env - Tparcel500
                        lifted_index_500[t_idx, j, i] = np.float32((T_env[-1] - Tparcel500).to("kelvin").m)
                    except Exception:
                        pass

                    # ----- Showalter Index (parcel starts at 850) -----
                    try:
                        T850 = (t850_c[j, i] * units.degC).to("kelvin")
                        Td850 = Td[850][j, i] * units.degC
                        prof850 = mpcalc.parcel_profile(p_prof, T850, Td850).to("kelvin")
                        Tparcel500_850 = mpcalc.log_interpolate_1d(500.0 * units.hPa, p_prof, prof850)
                        showalter_index[t_idx, j, i] = np.float32((T_env[-1] - Tparcel500_850).to("kelvin").m)
                    except Exception:
                        pass

    print("\nCalculation complete.")

    # --- Save ---
    os.makedirs(CACHE_DIR, exist_ok=True)

    data_vars = {
        # Existing/previous
        "CAPE_Proxy": (("time", "latitude", "longitude"), cape_proxy),
        "CAI": (("time", "latitude", "longitude"), cai_arr),
        "Shear_1000_850": (("time", "latitude", "longitude"), shear_1000_850),
        "Shear_950_850": (("time", "latitude", "longitude"), shear_950_850),
        "Lapse_1000_850": (("time", "latitude", "longitude"), lapse_1000_850),
        "Lapse_850_500": (("time", "latitude", "longitude"), lapse_850_500),
        "CIN": (("time", "latitude", "longitude"), cin_arr),
        # "LFC": (("time", "latitude", "longitude"), lfc_arr),
        "EL": (("time", "latitude", "longitude"), el_arr),

        # NEW requested
        "K_Index": (("time", "latitude", "longitude"), k_index),
        "Total_Totals": (("time", "latitude", "longitude"), total_totals),
        "Lifted_Index_500": (("time", "latitude", "longitude"), lifted_index_500),
        "Showalter_Index": (("time", "latitude", "longitude"), showalter_index),
        "DD_850": (("time", "latitude", "longitude"), dd_850),
        "DD_700": (("time", "latitude", "longitude"), dd_700),
        "Convergence_10m": (("time", "latitude", "longitude"), convergence_10m),
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
                "Added indices: K_Index, Total_Totals, Lifted_Index_500 (parcel from 1000 hPa), "
                "Showalter_Index (parcel from 850 hPa), DD_850/DD_700, Convergence_10m=-div(u10m,v10m). "
                "Td fields are derived from q using MetPy vapor_pressure + dewpoint. "
                "Parcel-based indices use 5 pressure levels (1000/950/850/700/500) so results are coarse. "
                "Lapse_* are ΔT proxies (K), not K/km (no geopotential heights provided)."
            )
        },
    )

    encoding = {v: {"zlib": True, "complevel": 1, "dtype": "float32"} for v in ds_out.data_vars}
    ds_out.to_netcdf(OUTPUT_FILE, encoding=encoding)
    print(f"Saved derived dataset to {OUTPUT_FILE}")


if __name__ == "__main__":
    main()
