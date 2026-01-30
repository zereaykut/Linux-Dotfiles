#!/usr/bin/env python3
"""
04_mask.py (Winter-optimized for Turkey, Feb 2025)

- Loads cache/derived.nc
- Filters to Feb 2025 (UTC)
- Optionally crops to Turkey region bbox
- Uses Convergence_850 if available (preferred), otherwise Convergence_10m
- Uses adaptive (percentile-based) thresholds tuned to February 2025
- Saves cache/instability_mask_feb2025.nc and plots/Composite_Instability_Mask/*.png
"""

import os
import numpy as np
import xarray as xr

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import cartopy.crs as ccrs
import cartopy.feature as cfeature


DERIVED_FILE = os.path.join("cache", "derived.nc")
OUT_MASK_FILE = os.path.join("cache", "instability_mask_feb2025.nc")

SAVE_PLOTS = True
PLOT_DIR = os.path.join("plots", "Composite_Instability_Mask")

# -----------------------------
# Time/region focus
# -----------------------------
# February 2025 (inclusive start, exclusive end)
TIME_START = "2025-02-01"
TIME_END   = "2025-03-01"

# Turkey-ish bounding box (adjust if you want)
CROP_TURKEY = True
TURKEY_BBOX = {
    "lat_min": 35.0,
    "lat_max": 43.5,
    "lon_min": 25.0,
    "lon_max": 46.5,
}

# -----------------------------
# Winter tuning knobs
# -----------------------------
# Use percentile thresholds computed ON THE FILTERED Feb-2025 subset
# These are good winter defaults:
# - CAI: lower than summer -> use ~70th percentile
# - KI: winter convection can occur with lower KI -> use ~65th percentile
# - Convergence: focus on strongest forcing -> use ~85th percentile
CAI_PCTL  = 70
KI_PCTL   = 65
CONV_PCTL = 85

# Require at least 2/3 signals (robust). If too sparse in winter, set to 1.
MIN_SCORE = 2

# Prevent trivial thresholds if fields are nearly constant
MIN_CONV_ABS = 1.0e-6  # 1/s
EPS = 1e-12


def _safe_time_str(dt64) -> str:
    try:
        return np.datetime_as_string(dt64, unit="h").replace(":", "")
    except Exception:
        return str(dt64).replace(":", "")


def _crop_to_bbox(ds: xr.Dataset) -> xr.Dataset:
    if not CROP_TURKEY:
        return ds

    lat_min = TURKEY_BBOX["lat_min"]
    lat_max = TURKEY_BBOX["lat_max"]
    lon_min = TURKEY_BBOX["lon_min"]
    lon_max = TURKEY_BBOX["lon_max"]

    # latitude may be descending in ERA5; handle both
    lat = ds["latitude"]
    if lat.values[0] > lat.values[-1]:
        ds = ds.sel(latitude=slice(lat_max, lat_min))
    else:
        ds = ds.sel(latitude=slice(lat_min, lat_max))

    # longitudes could be -180..180 or 0..360; assume your data is standard -180..180
    ds = ds.sel(longitude=slice(lon_min, lon_max))
    return ds


def _pctl_threshold(da: xr.DataArray, pctl: float) -> float:
    vals = da.values
    vals = vals[np.isfinite(vals)]
    if vals.size == 0:
        return np.nan
    return float(np.percentile(vals, pctl))


def plot_mask_frame(ds_mask: xr.Dataset, t_idx: int):
    os.makedirs(PLOT_DIR, exist_ok=True)

    data = ds_mask.isel(time=t_idx)
    mask = data["Composite_Mask"]
    score = data["Composite_Score"]

    time_str = _safe_time_str(data.time.values)

    fig = plt.figure(figsize=(12, 8))
    ax = plt.axes(projection=ccrs.PlateCarree())
    ax.add_feature(cfeature.COASTLINE, linewidth=0.8)
    ax.add_feature(cfeature.BORDERS, linestyle=":", linewidth=0.5)

    cf = ax.contourf(
        data.longitude,
        data.latitude,
        score,
        levels=[-0.5, 0.5, 1.5, 2.5, 3.5],
        cmap="viridis",
        transform=ccrs.PlateCarree(),
        extend="neither",
    )
    cbar = plt.colorbar(cf, ax=ax, shrink=0.85)
    cbar.set_label("Composite Score (0..3)")

    ax.contour(
        data.longitude,
        data.latitude,
        mask.astype(int),
        levels=[0.5],
        linewidths=1.2,
        colors="red",
        transform=ccrs.PlateCarree(),
    )

    ax.set_title(f"Turkey Winter Composite Mask | {time_str}", fontsize=13)

    out_png = os.path.join(PLOT_DIR, f"Composite_Instability_Mask_{t_idx:05d}.png")
    plt.savefig(out_png, dpi=150, bbox_inches="tight")
    plt.close(fig)


def main():
    if not os.path.exists(DERIVED_FILE):
        raise FileNotFoundError(f"Missing {DERIVED_FILE}. Run 02_thermo_calc.py first.")

    ds = xr.open_dataset(DERIVED_FILE)

    # --- Filter time to February 2025 ---
    if "time" not in ds.coords:
        raise KeyError("Dataset has no 'time' coordinate.")

    ds = ds.sel(time=slice(TIME_START, TIME_END))
    if ds.sizes.get("time", 0) == 0:
        raise ValueError(f"No timesteps found in range {TIME_START} .. {TIME_END}")

    # --- Crop to Turkey region ---
    ds = _crop_to_bbox(ds)

    # --- Required fields ---
    if "CAI" not in ds.data_vars or "K_Index" not in ds.data_vars:
        raise KeyError(f"Need CAI and K_Index in derived file. Available: {list(ds.data_vars)}")

    # Prefer Convergence_850 for winter (synoptic forcing / LLJ regions often show better at 850)
    conv_name = None
    if "Convergence_850" in ds.data_vars:
        conv_name = "Convergence_850"
    elif "Convergence_10m" in ds.data_vars:
        conv_name = "Convergence_10m"
    else:
        raise KeyError(
            "Need Convergence_850 or Convergence_10m in derived file. "
            f"Available: {list(ds.data_vars)}"
        )

    cai = ds["CAI"]
    ki = ds["K_Index"]
    conv = ds[conv_name]

    # --- Winter adaptive thresholds (percentile-based) ---
    cai_thr = _pctl_threshold(cai, CAI_PCTL)
    ki_thr = _pctl_threshold(ki, KI_PCTL)
    conv_thr = _pctl_threshold(conv, CONV_PCTL)

    # Safety floors (especially for convergence)
    if not np.isfinite(conv_thr):
        conv_thr = MIN_CONV_ABS
    conv_thr = max(conv_thr, MIN_CONV_ABS)

    if not np.isfinite(cai_thr):
        cai_thr = 0.0
    if not np.isfinite(ki_thr):
        ki_thr = 0.0

    print("=== Winter Feb-2025 thresholds (computed on filtered subset) ===")
    print(f"Time window: {TIME_START} .. {TIME_END}")
    print(f"Region crop: {CROP_TURKEY} {TURKEY_BBOX if CROP_TURKEY else ''}")
    print(f"Convergence var used: {conv_name}")
    print(f"CAI_THR  (p{CAI_PCTL})  = {cai_thr:.3f}")
    print(f"KI_THR   (p{KI_PCTL})   = {ki_thr:.3f}")
    print(f"CONV_THR (p{CONV_PCTL}) = {conv_thr:.6e} 1/s")
    print(f"MIN_SCORE = {MIN_SCORE}")

    # --- Conditions ---
    cond_cai = cai >= cai_thr
    cond_ki = ki >= ki_thr
    cond_conv = conv >= conv_thr

    # Score 0..3
    score = cond_cai.astype("int8") + cond_ki.astype("int8") + cond_conv.astype("int8")
    mask = score >= MIN_SCORE

    ds_out = xr.Dataset(
        data_vars={
            "Composite_Score": score.astype("int8"),
            "Composite_Mask": mask.astype("int8"),
            "Cond_CAI": cond_cai.astype("int8"),
            "Cond_KI": cond_ki.astype("int8"),
            "Cond_Convergence": cond_conv.astype("int8"),
        },
        coords={
            "time": ds["time"],
            "latitude": ds["latitude"],
            "longitude": ds["longitude"],
        },
        attrs={
            "TIME_START": TIME_START,
            "TIME_END": TIME_END,
            "CROP_TURKEY": str(CROP_TURKEY),
            "TURKEY_BBOX": str(TURKEY_BBOX),
            "CONVERGENCE_VAR": conv_name,
            "CAI_PCTL": CAI_PCTL,
            "KI_PCTL": KI_PCTL,
            "CONV_PCTL": CONV_PCTL,
            "CAI_THR": float(cai_thr),
            "KI_THR": float(ki_thr),
            "CONV_THR": float(conv_thr),
            "MIN_SCORE": MIN_SCORE,
            "notes": (
                "Winter-optimized composite mask for Turkey using Feb-2025 subset. "
                "Thresholds are percentile-based on the filtered subset. "
                "Mask = score>=MIN_SCORE."
            ),
        },
    )

    enc = {v: {"zlib": True, "complevel": 1} for v in ds_out.data_vars}
    ds_out.to_netcdf(OUT_MASK_FILE, encoding=enc)
    print(f"Saved composite mask netcdf → {OUT_MASK_FILE}")

    if SAVE_PLOTS:
        os.makedirs(PLOT_DIR, exist_ok=True)
        for t in range(ds_out.sizes["time"]):
            plot_mask_frame(ds_out, t)
            if (t + 1) % 10 == 0 or (t + 1) == ds_out.sizes["time"]:
                print(f"Plots: {t+1}/{ds_out.sizes['time']}", end="\r")
        print()


if __name__ == "__main__":
    main()
