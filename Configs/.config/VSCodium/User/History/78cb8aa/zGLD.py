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

# Parcel-based indices are slow (LI/SI). Keep False for speed.
COMPUTE_PARCEL_INDICES = False


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
        print(f"Available: {list(ds.variables)}")
        sys.exit(1)

    has_t2m = "t2m" in ds
    has_u = "u" in ds
    has_v = "v" in ds
    has_u10m = "u10m" in ds
    has_v10m = "v10m" in ds

    miss_levels = _require_levels(ds, TD_LEVELS)
    if miss_levels:
        print(f"ERROR: missing pressure levels needed for indices: {miss_levels}")
        sys.exit(1)

    os.makedirs(CACHE_DIR, exist_ok=True)

    # ------------------------------------------------------------
    # 1) Compute dewpoint ONLY at needed levels (FAST)
    # ------------------------------------------------------------
    print("Computing Td from q at levels:", TD_LEVELS)

    # Select only 5 levels -> reduces memory & compute massively
    q_sel = ds["q"].sel(isobaricInhPa=TD_LEVELS).astype("float32").values * units("kg/kg")  # (time, 5, y, x)
    p_sel = ds["isobaricInhPa"].sel(isobaricInhPa=TD_LEVELS).astype("float32").values * units.hPa  # (5,)

    w = mpcalc.mixing_ratio_from_specific_humidity(q_sel)
    e = mpcalc.vapor_pressure(p_sel[None, :, None, None], w)
    td_sel = mpcalc.dewpoint(e).to("degC").m.astype(np.float32)  # (time, 5, y, x), °C

    # Level slices (time, y, x)
    Td_1000 = td_sel[:, 0]
    Td_950  = td_sel[:, 1]
    Td_850  = td_sel[:, 2]
    Td_700  = td_sel[:, 3]
    Td_500  = td_sel[:, 4]

    # ------------------------------------------------------------
    # 2) Load needed temperature levels once (vectorized)
    # ------------------------------------------------------------
    print("Loading T at key levels (vectorized)...")
    t1000 = (ds["t"].sel(isobaricInhPa=1000).values - 273.15).astype(np.float32)  # °C
    t950  = (ds["t"].sel(isobaricInhPa=950).values  - 273.15).astype(np.float32)
    t850  = (ds["t"].sel(isobaricInhPa=850).values  - 273.15).astype(np.float32)
    t700  = (ds["t"].sel(isobaricInhPa=700).values  - 273.15).astype(np.float32)
    t500  = (ds["t"].sel(isobaricInhPa=500).values  - 273.15).astype(np.float32)

    # Surface T for CAI
    if has_t2m:
        t_sfc_k = ds["t2m"].values.astype(np.float32)  # K
    else:
        t_sfc_k = (t1000 + 273.15).astype(np.float32)

    # ------------------------------------------------------------
    # 3) Vectorized indices (FAST)
    # ------------------------------------------------------------
    print("Computing vectorized indices...")

    # Dewpoint depression
    DD_850 = (t850 - Td_850).astype(np.float32)
    DD_700 = (t700 - Td_700).astype(np.float32)

    # CAPE proxy using mean dewpoint depression across 5 levels
    dd_mean = ((t1000 - Td_1000) + (t950 - Td_950) + (t850 - Td_850) + (t700 - Td_700) + (t500 - Td_500)) / 5.0
    CAPE_Proxy = (t1000 - t500 - MOISTURE_ALPHA * dd_mean).astype(np.float32)

    # CAI: (T2m - T500) + (Td850 - Td700)
    CAI = ((t_sfc_k - (t500 + 273.15)) + (Td_850 - Td_700)).astype(np.float32)

    # K Index: (T850 - T500) + Td850 - (T700 - Td700)
    K_Index = ((t850 - t500) + Td_850 - (t700 - Td_700)).astype(np.float32)

    # Total Totals: T850 + Td850 - 2*T500
    Total_Totals = (t850 + Td_850 - 2.0 * t500).astype(np.float32)

    # Lapse proxies (ΔT, not K/km)
    Lapse_1000_850 = (t1000 - t850).astype(np.float32)
    Lapse_850_500  = (t850 - t500).astype(np.float32)

    # Shear magnitudes (if u/v available)
    Shear_1000_850 = np.full_like(CAPE_Proxy, np.nan, dtype=np.float32)
    Shear_950_850  = np.full_like(CAPE_Proxy, np.nan, dtype=np.float32)

    if has_u and has_v:
        print("Computing shear (vectorized)...")
        # (time,y,x)
        u1000 = ds["u"].sel(isobaricInhPa=1000).values.astype(np.float32) if 1000 in ds["isobaricInhPa"].values else None
        v1000 = ds["v"].sel(isobaricInhPa=1000).values.astype(np.float32) if 1000 in ds["isobaricInhPa"].values else None
        u850  = ds["u"].sel(isobaricInhPa=850).values.astype(np.float32)
        v850  = ds["v"].sel(isobaricInhPa=850).values.astype(np.float32)

        if u1000 is not None and v1000 is not None:
            Shear_1000_850 = np.sqrt((u850 - u1000) ** 2 + (v850 - v1000) ** 2).astype(np.float32)

        # 950-850 only if 950 exists in u/v
        if 950 in ds["isobaricInhPa"].values:
            u950 = ds["u"].sel(isobaricInhPa=950).values.astype(np.float32)
            v950 = ds["v"].sel(isobaricInhPa=950).values.astype(np.float32)
            Shear_950_850 = np.sqrt((u850 - u950) ** 2 + (v850 - v950) ** 2).astype(np.float32)

    # ------------------------------------------------------------
    # 4) Convergence_10m (loop over time; still reasonably fast)
    # ------------------------------------------------------------
    Convergence_10m = np.full_like(CAPE_Proxy, np.nan, dtype=np.float32)
    if has_u10m and has_v10m:
        print("Computing 10m convergence (time loop)...")
        lon2d, lat2d = np.meshgrid(ds.longitude.values, ds.latitude.values)
        dx, dy = mpcalc.lat_lon_grid_deltas(lon2d, lat2d)

        u10_all = ds["u10m"].values.astype(np.float32)  # (time,y,x)
        v10_all = ds["v10m"].values.astype(np.float32)

        for t in range(ds.sizes["time"]):
            if (t + 1) % 10 == 0 or (t + 1) == ds.sizes["time"]:
                print(f"  divergence {t+1}/{ds.sizes['time']}", end="\r")

            u10 = u10_all[t] * units("m/s")
            v10 = v10_all[t] * units("m/s")
            div = mpcalc.divergence(u10, v10, dx=dx, dy=dy)  # 1/s
            Convergence_10m[t] = (-div).to("1/s").m.astype(np.float32)
        print()

    # ------------------------------------------------------------
    # 5) LI/SI placeholders (optional slow)
    # ------------------------------------------------------------
    Lifted_Index_500 = np.full_like(CAPE_Proxy, np.nan, dtype=np.float32)
    Showalter_Index = np.full_like(CAPE_Proxy, np.nan, dtype=np.float32)

    if COMPUTE_PARCEL_INDICES:
        # Keeping this disabled by default because it is the main runtime killer.
        # If you want: I can implement a "hotspot-only" LI/SI (mask-based) version.
        print("COMPUTE_PARCEL_INDICES=True (slow): not implemented in this fast build.")
        print("Use hotspot-only LI/SI if needed.")

    # ------------------------------------------------------------
    # 6) Save output
    # ------------------------------------------------------------
    print("Saving derived dataset...")

    ds_out = xr.Dataset(
        data_vars={
            "CAPE_Proxy": (("time", "latitude", "longitude"), CAPE_Proxy),
            "CAI": (("time", "latitude", "longitude"), CAI),
            "K_Index": (("time", "latitude", "longitude"), K_Index),
            "Total_Totals": (("time", "latitude", "longitude"), Total_Totals),
            "DD_850": (("time", "latitude", "longitude"), DD_850),
            "DD_700": (("time", "latitude", "longitude"), DD_700),
            "Lapse_1000_850": (("time", "latitude", "longitude"), Lapse_1000_850),
            "Lapse_850_500": (("time", "latitude", "longitude"), Lapse_850_500),
            "Shear_1000_850": (("time", "latitude", "longitude"), Shear_1000_850),
            "Shear_950_850": (("time", "latitude", "longitude"), Shear_950_850),
            
            "Convergence_10m": (("time", "latitude", "longitude"), Convergence_10m),
            "Lifted_Index_500": (("time", "latitude", "longitude"), Lifted_Index_500),
            "Showalter_Index": (("time", "latitude", "longitude"), Showalter_Index),

            # Td maps
            "Td_1000hPa": (("time", "latitude", "longitude"), Td_1000),
            "Td_950hPa":  (("time", "latitude", "longitude"), Td_950),
            "Td_850hPa":  (("time", "latitude", "longitude"), Td_850),
            "Td_700hPa":  (("time", "latitude", "longitude"), Td_700),
            "Td_500hPa":  (("time", "latitude", "longitude"), Td_500),
        },
        coords={"time": ds.time, "latitude": ds.latitude, "longitude": ds.longitude},
        attrs={
            "notes": (
                "FAST build: Td computed only at 1000/950/850/700/500 hPa; most indices vectorized. "
                "Convergence computed via -div(u10m,v10m). LI/SI left as NaN unless you implement hotspot-only."
            )
        },
    )

    enc = {v: {"zlib": True, "complevel": 1, "dtype": "float32"} for v in ds_out.data_vars}
    ds_out.to_netcdf(OUTPUT_FILE, encoding=enc)
    print(f"Saved → {OUTPUT_FILE}")


if __name__ == "__main__":
    main()
