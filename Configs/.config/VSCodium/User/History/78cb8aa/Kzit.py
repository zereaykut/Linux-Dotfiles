#!/usr/bin/env python3
import os
import sys
import numpy as np
import xarray as xr
import metpy.calc as mpcalc
from metpy.units import units

CACHE_DIR = "cache"
CACHE_FILE = os.path.join(CACHE_DIR, "cache.nc")
OUTPUT_FILE = os.path.join(CACHE_DIR, "derived.nc")

TD_LEVELS = [1000, 950, 850, 700, 500]  # hPa
MOISTURE_ALPHA = 0.5

# Parcel-based indices are slow (LI/SI). Keep False for speed.
COMPUTE_PARCEL_INDICES = False


def _require_levels(ds, levels):
    levs = ds["isobaricInhPa"].values
    return [L for L in levels if L not in levs]


def _has_level(ds, level: int) -> bool:
    try:
        return level in ds["isobaricInhPa"].values
    except Exception:
        return False


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
    has_u10 = "u10" in ds
    has_v10 = "v10" in ds

    miss_levels = _require_levels(ds, TD_LEVELS)
    if miss_levels:
        print(f"ERROR: missing pressure levels needed for indices: {miss_levels}")
        sys.exit(1)

    os.makedirs(CACHE_DIR, exist_ok=True)

    # ------------------------------------------------------------
    # Compute dewpoint ONLY at needed levels (FAST)
    # ------------------------------------------------------------
    print("Computing Td from q at levels:", TD_LEVELS)

    q_sel = ds["q"].sel(isobaricInhPa=TD_LEVELS).astype("float32").values * units("kg/kg")  # (time, 5, y, x)
    p_sel = ds["isobaricInhPa"].sel(isobaricInhPa=TD_LEVELS).astype("float32").values * units.hPa  # (5,)

    w = mpcalc.mixing_ratio_from_specific_humidity(q_sel)
    e = mpcalc.vapor_pressure(p_sel[None, :, None, None], w)
    td_sel = mpcalc.dewpoint(e).to("degC").m.astype(np.float32)  # (time, 5, y, x), °C

    Td_1000 = td_sel[:, 0]
    Td_950  = td_sel[:, 1]
    Td_850  = td_sel[:, 2]
    Td_700  = td_sel[:, 3]
    Td_500  = td_sel[:, 4]

    # ------------------------------------------------------------
    # Load needed temperature levels once (vectorized)
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
    # Vectorized indices (FAST)
    # ------------------------------------------------------------
    print("Computing vectorized indices...")

    DD_850 = (t850 - Td_850).astype(np.float32)
    DD_700 = (t700 - Td_700).astype(np.float32)
    DD_950 = (t950 - Td_950).astype(np.float32)
    DD_1000 = (t1000 - Td_1000).astype(np.float32)
    DD_LowMean_1000_850 = ((DD_1000 + DD_950 + DD_850) / 3.0).astype(np.float32)

    dd_mean = ((t1000 - Td_1000) + (t950 - Td_950) + (t850 - Td_850) + (t700 - Td_700) + (t500 - Td_500)) / 5.0
    CAPE_Proxy = (t1000 - t500 - MOISTURE_ALPHA * dd_mean).astype(np.float32)

    CAI = ((t_sfc_k - (t500 + 273.15)) + (Td_850 - Td_700)).astype(np.float32)
    K_Index = ((t850 - t500) + Td_850 - (t700 - Td_700)).astype(np.float32)
    Total_Totals = (t850 + Td_850 - 2.0 * t500).astype(np.float32)

    Lapse_1000_850 = (t1000 - t850).astype(np.float32)
    Lapse_850_500  = (t850 - t500).astype(np.float32)

    Shear_1000_850 = np.full_like(CAPE_Proxy, np.nan, dtype=np.float32)
    Shear_950_850  = np.full_like(CAPE_Proxy, np.nan, dtype=np.float32)

    # Pre-load u850/v850 for convergence_850 and shear (if exists)
    u850_all = v850_all = None
    if has_u and has_v:
        u850_all = ds["u"].sel(isobaricInhPa=850).values.astype(np.float32)
        v850_all = ds["v"].sel(isobaricInhPa=850).values.astype(np.float32)

        print("Computing shear (vectorized)...")
        u1000 = ds["u"].sel(isobaricInhPa=1000).values.astype(np.float32) if _has_level(ds, 1000) else None
        v1000 = ds["v"].sel(isobaricInhPa=1000).values.astype(np.float32) if _has_level(ds, 1000) else None

        if u1000 is not None and v1000 is not None:
            Shear_1000_850 = np.sqrt((u850_all - u1000) ** 2 + (v850_all - v1000) ** 2).astype(np.float32)

        if _has_level(ds, 950):
            u950 = ds["u"].sel(isobaricInhPa=950).values.astype(np.float32)
            v950 = ds["v"].sel(isobaricInhPa=950).values.astype(np.float32)
            Shear_950_850 = np.sqrt((u850_all - u950) ** 2 + (v850_all - v950) ** 2).astype(np.float32)

    # ------------------------------------------------------------
    # Convergence calculations (time loop)
    # ------------------------------------------------------------
    lon2d, lat2d = np.meshgrid(ds.longitude.values, ds.latitude.values)
    dx, dy = mpcalc.lat_lon_grid_deltas(lon2d, lat2d)

    # Convergence_10m
    Convergence_10m = np.full_like(CAPE_Proxy, np.nan, dtype=np.float32)
    if has_u10 and has_v10:
        print("Computing 10m convergence (time loop)...")
        u10_all = ds["u10"].values.astype(np.float32)  # (time,y,x)
        v10_all = ds["v10"].values.astype(np.float32)

        for t in range(ds.sizes["time"]):
            if (t + 1) % 10 == 0 or (t + 1) == ds.sizes["time"]:
                print(f"  divergence10 {t+1}/{ds.sizes['time']}", end="\r")

            u10 = u10_all[t] * units("m/s")
            v10 = v10_all[t] * units("m/s")
            div = mpcalc.divergence(u10, v10, dx=dx, dy=dy)  # 1/s
            Convergence_10m[t] = (-div).to("1/s").m.astype(np.float32)
        print()

    # Helper to compute convergence at a pressure level
    def compute_convergence_level(level_hpa: int):
        out = np.full_like(CAPE_Proxy, np.nan, dtype=np.float32)
        if not (has_u and has_v):
            return out

        if not _has_level(ds, level_hpa):
            print(f"WARNING: isobaric level {level_hpa} hPa not found in dataset. Convergence_{level_hpa} will be NaN.")
            return out

        u_all = ds["u"].sel(isobaricInhPa=level_hpa).values.astype(np.float32)
        v_all = ds["v"].sel(isobaricInhPa=level_hpa).values.astype(np.float32)

        print(f"Computing {level_hpa} hPa convergence (time loop)...")
        for t in range(ds.sizes["time"]):
            if (t + 1) % 10 == 0 or (t + 1) == ds.sizes["time"]:
                print(f"  divergence{level_hpa} {t+1}/{ds.sizes['time']}", end="\r")

            u = u_all[t] * units("m/s")
            v = v_all[t] * units("m/s")
            div = mpcalc.divergence(u, v, dx=dx, dy=dy)  # 1/s
            out[t] = (-div).to("1/s").m.astype(np.float32)
        print()
        return out

    # Convergence at pressure levels
    Convergence_850  = compute_convergence_level(850)   # already requested earlier
    Convergence_1000 = compute_convergence_level(1000)
    Convergence_950  = compute_convergence_level(950)

    # ------------------------------------------------------------
    # LI/SI placeholders (optional slow)
    # ------------------------------------------------------------
    Lifted_Index_500 = np.full_like(CAPE_Proxy, np.nan, dtype=np.float32)
    
    # --- Fast Showalter Proxy (layer-averaged) ---
    # Layer mean dewpoint depression (1000-950-850)

    # Environmental term (500-850), °C
    DeltaT_500_850 = (t500 - t850).astype(np.float32)

    # Weight for dryness term (tune for winter Turkey)
    SI_PROXY_ALPHA = 0.6

    # Proxy: more negative => more unstable
    Showalter_Proxy_LayerAvg = (DeltaT_500_850 + SI_PROXY_ALPHA * DD_LowMean_1000_850).astype(np.float32)


    if COMPUTE_PARCEL_INDICES:
        print("COMPUTE_PARCEL_INDICES=True (slow): not implemented in this fast build.")
        print("Use hotspot-only LI/SI if needed.")

    # ------------------------------------------------------------
    # Save output
    # ------------------------------------------------------------
    print("Saving derived dataset...")

    ds_out = xr.Dataset(
        data_vars={
            "CAPE_Proxy": (("time", "latitude", "longitude"), CAPE_Proxy),
            "CAI": (("time", "latitude", "longitude"), CAI),
            "K_Index": (("time", "latitude", "longitude"), K_Index),
            "Total_Totals": (("time", "latitude", "longitude"), Total_Totals),
            "DD_1000": (("time", "latitude", "longitude"), DD_1000),
            "DD_850": (("time", "latitude", "longitude"), DD_850),
            "DD_700": (("time", "latitude", "longitude"), DD_700),
            "DD_950": (("time", "latitude", "longitude"), DD_950),
            "DD_LowMean_1000_850": (("time", "latitude", "longitude"), DD_LowMean_1000_850),

            "Lapse_1000_850": (("time", "latitude", "longitude"), Lapse_1000_850),
            "Lapse_850_500": (("time", "latitude", "longitude"), Lapse_850_500),
            "Shear_1000_850": (("time", "latitude", "longitude"), Shear_1000_850),
            "Shear_950_850": (("time", "latitude", "longitude"), Shear_950_850),

            "Convergence_10m": (("time", "latitude", "longitude"), Convergence_10m),
            "Convergence_850": (("time", "latitude", "longitude"), Convergence_850),
            "Convergence_1000": (("time", "latitude", "longitude"), Convergence_1000),
            "Convergence_950": (("time", "latitude", "longitude"), Convergence_950),

            "Lifted_Index_500": (("time", "latitude", "longitude"), Lifted_Index_500),
            "Showalter_Proxy_LayerAvg": (("time", "latitude", "longitude"), Showalter_Proxy_LayerAvg),

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
                "Convergence computed as -div(u,v) at 1000/950/850 hPa (if level exists) and at 10m if u10/v10 exist."
            )
        },
    )

    enc = {v: {"zlib": True, "complevel": 1, "dtype": "float32"} for v in ds_out.data_vars}
    ds_out.to_netcdf(OUTPUT_FILE, encoding=enc)
    print(f"Saved → {OUTPUT_FILE}")


if __name__ == "__main__":
    main()
