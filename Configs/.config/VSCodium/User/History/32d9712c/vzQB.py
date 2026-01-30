#!/usr/bin/env python3
"""
04_mask.py

- Loads cache/derived.nc
- Filters to a target period (default: Feb 2025 UTC)
- Optionally crops to Turkey bbox
- Uses ONLY:
    * CAI
    * Convergence_mean
    * Convergence_10m
  to create a composite mask field.

- Uses adaptive (percentile-based) thresholds computed on the filtered subset.
- Builds a composite score (0..3) and mask = score >= MIN_SCORE
- Saves cache/instability_mask.nc and plots/Composite_Mask/*.png
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
OUT_MASK_FILE = os.path.join("cache", "instability_mask.nc")

SAVE_PLOTS = True
PLOT_DIR = os.path.join("plots", "Composite_Mask_04.1")

# -----------------------------
# Time/region focus
# -----------------------------
TIME_START = "2025-02-01"
TIME_END   = "2025-03-01"   # exclusive end

CROP_TURKEY = True
TURKEY_BBOX = {
    "lat_min": 25,
    "lat_max": 45,
    "lon_min": 20,
    "lon_max": 50,
}

# -----------------------------
# Threshold tuning (percentiles)
# -----------------------------
# CAI in winter tends to be lower than summer -> ~70th pct is reasonable
CAI_PCTL = 70

# Convergence: focus on strongest forcing -> ~85th pct
CONVMEAN_PCTL = 85
CONV10M_PCTL  = 85

# Require at least 2/3 signals (robust)
MIN_SCORE = 2

# Safety floors (avoid trivial/zero thresholds)
MIN_CONV_ABS = 1.0e-6  # 1/s


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

    ax.set_title(f"Composite Mask (CAI + Convergence_mean + Convergence_10m) | {time_str}", fontsize=12)

    out_png = os.path.join(PLOT_DIR, f"Composite_Mask_{t_idx:05d}.png")
    plt.savefig(out_png, dpi=150, bbox_inches="tight")
    plt.close(fig)


def main():
    if not os.path.exists(DERIVED_FILE):
        raise FileNotFoundError(f"Missing {DERIVED_FILE}. Run 02_thermo_calc.py first.")

    ds = xr.open_dataset(DERIVED_FILE)

    if "time" not in ds.coords:
        raise KeyError("Dataset has no 'time' coordinate.")

    # --- Filter time ---
    ds = ds.sel(time=slice(TIME_START, TIME_END))
    if ds.sizes.get("time", 0) == 0:
        raise ValueError(f"No timesteps found in range {TIME_START} .. {TIME_END}")

    # --- Crop region ---
    ds = _crop_to_bbox(ds)

    # --- Required fields ---
    required = ["CAI", "Convergence_mean", "Convergence_10m"]
    missing = [v for v in required if v not in ds.data_vars]
    if missing:
        raise KeyError(f"Missing required vars: {missing}. Available: {list(ds.data_vars)}")

    cai = ds["CAI"]
    conv_mean = ds["Convergence_mean"]
    conv_10m = ds["Convergence_10m"]

    # --- Adaptive thresholds (computed on filtered subset) ---
    cai_thr = _pctl_threshold(cai, CAI_PCTL)
    convm_thr = _pctl_threshold(conv_mean, CONVMEAN_PCTL)
    conv10_thr = _pctl_threshold(conv_10m, CONV10M_PCTL)

    # Safety floors
    if not np.isfinite(cai_thr):
        cai_thr = 0.0

    if not np.isfinite(convm_thr):
        convm_thr = MIN_CONV_ABS
    convm_thr = max(convm_thr, MIN_CONV_ABS)

    if not np.isfinite(conv10_thr):
        conv10_thr = MIN_CONV_ABS
    conv10_thr = max(conv10_thr, MIN_CONV_ABS)

    print("=== Composite Mask thresholds (computed on filtered subset) ===")
    print(f"Time window: {TIME_START} .. {TIME_END}")
    print(f"Region crop: {CROP_TURKEY} {TURKEY_BBOX if CROP_TURKEY else ''}")
    print(f"CAI_THR         (p{CAI_PCTL})      = {cai_thr:.3f}")
    print(f"ConvMean_THR    (p{CONVMEAN_PCTL}) = {convm_thr:.6e} 1/s")
    print(f"Conv10m_THR     (p{CONV10M_PCTL})  = {conv10_thr:.6e} 1/s")
    print(f"MIN_SCORE = {MIN_SCORE}")

    # --- Conditions ---
    cond_cai = cai >= cai_thr
    cond_convm = conv_mean >= convm_thr
    cond_conv10 = conv_10m >= conv10_thr

    # Score 0..3
    score = cond_cai.astype("int8") + cond_convm.astype("int8") + cond_conv10.astype("int8")
    mask = score >= MIN_SCORE

    ds_out = xr.Dataset(
        data_vars={
            "Composite_Score": score.astype("int8"),
            "Composite_Mask": mask.astype("int8"),
            "Cond_CAI": cond_cai.astype("int8"),
            "Cond_Convergence_mean": cond_convm.astype("int8"),
            "Cond_Convergence_10m": cond_conv10.astype("int8"),
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
            "CAI_PCTL": CAI_PCTL,
            "CONVMEAN_PCTL": CONVMEAN_PCTL,
            "CONV10M_PCTL": CONV10M_PCTL,
            "CAI_THR": float(cai_thr),
            "CONVMEAN_THR": float(convm_thr),
            "CONV10M_THR": float(conv10_thr),
            "MIN_SCORE": MIN_SCORE,
            "notes": (
                "Composite mask uses only CAI + Convergence_mean + Convergence_10m. "
                "Thresholds are percentile-based on the filtered subset. "
                "Composite_Score ranges 0..3. Mask = score >= MIN_SCORE."
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
