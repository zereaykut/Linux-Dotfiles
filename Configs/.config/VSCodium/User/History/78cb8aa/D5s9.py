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

TD_LEVELS = [1000, 950, 850, 700, 500]  # hPa
MOISTURE_ALPHA = 0.5


def _require_levels(ds, levels):
    levs = ds["isobaricInhPa"].values
    return [L for L in levels if L not in levs]


def main():
    if not os.path.exists(CACHE_FILE):
        print(f"Run preprocessing first. Missing: {CACHE_FILE}")
        sys.exit(1)

    ds = xr.open_dataset(CACHE_FILE)

    required = ["t", "q", "isobaricInhPa", "latitude", "longitude", "time"]
    missing_vars = [v for v in required if (v not in ds.variables and v not in ds.coords)]
    if missing_vars:
        print(f"Missing required fields: {missing_vars}")
        sys.exit(1)

    has_t2m = "t2m" in ds
    has_u = "u" in ds
    has_v = "v" in ds
    has_u10m = "u10m" in ds
    has_v10m = "v10m" in ds

    miss_levels = _require_levels(ds, TD_LEVELS)
    if miss_levels:
        print(f"Warning: missing pressure levels: {miss_levels}")

    # -----------------------------
    # Dewpoint from q
    # -----------------------------
    print("Computing dewpoint from specific humidity...")
    p_lev = ds["isobaricInhPa"].values * units.hPa
    q = ds["q"].values * units("kg/kg")

    w = mpcalc.mixing_ratio_from_specific_humidity(q)
    p4 = p_lev[None, :, None, None]
    e = mpcalc.vapor_pressure(p4, w)
    td_3d = mpcalc.dewpoint(e).to("degC").m

    levs = ds["isobaricInhPa"].values
    lev_to_idx = {int(L): int(np.where(levs == L)[0][0]) for L in levs}

    dims = (ds.sizes["time"], ds.sizes["latitude"], ds.sizes["longitude"])

    # -----------------------------
    # Output arrays
    # -----------------------------
    cape_proxy = np.full(dims, np.nan, np.float32)
    cai = np.full(dims, np.nan, np.float32)

    k_index = np.full(dims, np.nan, np.float32)
    total_totals = np.full(dims, np.nan, np.float32)
    lifted_index_500 = np.full(dims, np.nan, np.float32)
    showalter_index = np.full(dims, np.nan, np.float32)

    dd_850 = np.full(dims, np.nan, np.float32)
    dd_700 = np.full(dims, np.nan, np.float32)

    lapse_1000_850 = np.full(dims, np.nan, np.float32)
    lapse_850_500 = np.full(dims, np.nan, np.float32)

    shear_1000_850 = np.full(dims, np.nan, np.float32)
    shear_950_850 = np.full(dims, np.nan, np.float32)

    convergence_10m = np.full(dims, np.nan, np.float32)

    td_out = {L: np.full(dims, np.nan, np.float32) for L in TD_LEVELS}

    # grid deltas for convergence
    dx = dy = None
    if has_u10m and has_v10m:
        lon2d, lat2d = np.meshgrid(ds.longitude.values, ds.latitude.values)
        dx, dy = mpcalc.lat_lon_grid_deltas(lon2d, lat2d)

    print("Starting calculations...")
    for t in range(ds.sizes["time"]):
        print(f"Time {t+1}/{ds.sizes['time']}", end="\r")

        Td = {}
        for L in TD_LEVELS:
            Td[L] = td_3d[t, lev_to_idx[L]]
            td_out[L][t] = Td[L]

        t1000 = ds["t"].isel(time=t).sel(isobaricInhPa=1000).values - 273.15
        t950  = ds["t"].isel(time=t).sel(isobaricInhPa=950).values - 273.15
        t850  = ds["t"].isel(time=t).sel(isobaricInhPa=850).values - 273.15
        t700  = ds["t"].isel(time=t).sel(isobaricInhPa=700).values - 273.15
        t500  = ds["t"].isel(time=t).sel(isobaricInhPa=500).values - 273.15

        # Dewpoint depression
        dd_850[t] = t850 - Td[850]
        dd_700[t] = t700 - Td[700]

        # CAPE proxy
        dd_mean = (t1000 - Td[1000] + t950 - Td[950] + t850 - Td[850] + t700 - Td[700] + t500 - Td[500]) / 5
        cape_proxy[t] = (t1000 - t500 - MOISTURE_ALPHA * dd_mean)

        # CAI
        t_sfc = ds["t2m"].isel(time=t).values if has_t2m else (t1000 + 273.15)
        cai[t] = (t_sfc - (t500 + 273.15)) + (Td[850] - Td[700])

        # K Index
        k_index[t] = (t850 - t500) + Td[850] - (t700 - Td[700])

        # Total Totals
        total_totals[t] = t850 + Td[850] - 2 * t500

        # Lapse proxies
        lapse_1000_850[t] = (t1000 - t850)
        lapse_850_500[t] = (t850 - t500)

        # Shear
        if has_u and has_v:
            u1000 = ds["u"].isel(time=t).sel(isobaricInhPa=1000).values
            v1000 = ds["v"].isel(time=t).sel(isobaricInhPa=1000).values
            u850 = ds["u"].isel(time=t).sel(isobaricInhPa=850).values
            v850 = ds["v"].isel(time=t).sel(isobaricInhPa=850).values
            shear_1000_850[t] = np.sqrt((u850 - u1000) ** 2 + (v850 - v1000) ** 2)

        # Convergence
        if has_u10m and has_v10m and dx is not None:
            u10 = ds["u10m"].isel(time=t).values * units("m/s")
            v10 = ds["v10m"].isel(time=t).values * units("m/s")
            div = mpcalc.divergence(u10, v10, dx=dx, dy=dy)
            convergence_10m[t] = (-div).to("1/s").m

    print("\nSaving derived dataset...")

    data_vars = {
        "CAPE_Proxy": (("time", "latitude", "longitude"), cape_proxy),
        "CAI": (("time", "latitude", "longitude"), cai),
        "K_Index": (("time", "latitude", "longitude"), k_index),
        "Total_Totals": (("time", "latitude", "longitude"), total_totals),
        "Lifted_Index_500": (("time", "latitude", "longitude"), lifted_index_500),
        "Showalter_Index": (("time", "latitude", "longitude"), showalter_index),
        "DD_850": (("time", "latitude", "longitude"), dd_850),
        "DD_700": (("time", "latitude", "longitude"), dd_700),
        "Lapse_1000_850": (("time", "latitude", "longitude"), lapse_1000_850),
        "Lapse_850_500": (("time", "latitude", "longitude"), lapse_850_500),
        "Shear_1000_850": (("time", "latitude", "longitude"), shear_1000_850),
        "Shear_950_850": (("time", "latitude", "longitude"), shear_950_850),
        "Convergence_10m": (("time", "latitude", "longitude"), convergence_10m),
    }

    for L in TD_LEVELS:
        data_vars[f"Td_{L}hPa"] = (("time", "latitude", "longitude"), td_out[L])

    ds_out = xr.Dataset(
        data_vars=data_vars,
        coords={"time": ds.time, "latitude": ds.latitude, "longitude": ds.longitude},
        attrs={"notes": "LFC and EL removed. Dataset optimized for convective instability tracking."},
    )

    enc = {v: {"zlib": True, "complevel": 1, "dtype": "float32"} for v in ds_out.data_vars}
    ds_out.to_netcdf(OUTPUT_FILE, encoding=enc)
    print(f"Saved → {OUTPUT_FILE}")


if __name__ == "__main__":
    main()
