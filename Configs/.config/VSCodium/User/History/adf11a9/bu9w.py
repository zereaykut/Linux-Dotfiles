#!/usr/bin/env python3
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

# Plots (optional)
SAVE_PLOTS = True
PLOT_DIR = os.path.join("plots", "Composite_Instability_Mask")

# -----------------------------
# WINTER PARAMETER OPTIMIZATION
# (No domain cropping)
# -----------------------------
CALIBRATE_THRESHOLDS = False

# Calibrate using February 2025 only
CAL_START = "2025-02-01"
CAL_END = "2025-03-01"   # exclusive end

# Winter-tuned percentiles (good defaults for Turkey winter)
# - CAI & KI weaker in winter than summer, so use moderate percentiles
# - Convergence is important in winter forcing, so use higher percentile
CAI_PCTL = 70
KI_PCTL = 65
CONV_PCTL = 85

# Require at least 2/3 signals. If too sparse in winter, set to 1.
MIN_SCORE = 2

# Safety floor for convergence threshold (1/s)
MIN_CONV_ABS = 1.0e-6


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

    time_str = np.datetime_as_string(data.time.values, unit="h").replace(":", "")

    fig = plt.figure(figsize=(12, 8))
    ax = plt.axes(projection=ccrs.PlateCarree())
    ax.add_feature(cfeature.COASTLINE, linewidth=0.8)
    ax.add_feature(cfeature.BORDERS, linestyle=":", linewidth=0.5)

    # plot score as background (0..3)
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

    # overlay mask contour
    ax.contour(
        data.longitude,
        data.latitude,
        mask.astype(int),
        levels=[0.5],
        linewidths=1.2,
        colors="red",
        transform=ccrs.PlateCarree(),
    )

    ax.set_title(f"Composite Instability (Score & Mask) | {time_str}", fontsize=13)

    out_png = os.path.join(PLOT_DIR, f"Composite_Instability_Mask_{t_idx:05d}.png")
    plt.savefig(out_png, dpi=150, bbox_inches="tight")
    plt.close(fig)
    print(f"Saved: {out_png}")


def main():
    if not os.path.exists(DERIVED_FILE):
        raise FileNotFoundError(f"Missing {DERIVED_FILE}. Run 02_thermo_calc.py first.")

    ds = xr.open_dataset(DERIVED_FILE)

    # Prefer 850 hPa convergence (winter forcing), fallback to 10m if not present
    if "Convergence_850" in ds.data_vars:
        conv_name = "Convergence_850"
    elif "Convergence_10m" in ds.data_vars:
        conv_name = "Convergence_10m"
    else:
        raise KeyError(
            "Missing convergence field. Need 'Convergence_850' or 'Convergence_10m'. "
            f"Available: {list(ds.data_vars)}"
        )

    for v in ["CAI", "K_Index", conv_name]:
        if v not in ds.data_vars:
            raise KeyError(f"Missing variable '{v}' in derived file. Available: {list(ds.data_vars)}")

    cai = ds["CAI"]
    ki = ds["K_Index"]
    conv = ds[conv_name]

    # -----------------------------
    # Calibrate thresholds (Feb 2025)
    # -----------------------------
    if CALIBRATE_THRESHOLDS:
        if "time" not in ds.coords:
            raise KeyError("Dataset has no 'time' coordinate. Cannot calibrate thresholds.")

        ds_cal = ds.sel(time=slice(CAL_START, CAL_END))
        if ds_cal.sizes.get("time", 0) == 0:
            raise ValueError(f"No timesteps in calibration window {CAL_START}..{CAL_END}")

        CAI_THR = _pctl_threshold(ds_cal["CAI"], CAI_PCTL)
        KI_THR = _pctl_threshold(ds_cal["K_Index"], KI_PCTL)
        CONV_THR = _pctl_threshold(ds_cal[conv_name], CONV_PCTL)

        if not np.isfinite(CAI_THR):
            CAI_THR = 0.0
        if not np.isfinite(KI_THR):
            KI_THR = 0.0
        if not np.isfinite(CONV_THR):
            CONV_THR = MIN_CONV_ABS
        CONV_THR = max(CONV_THR, MIN_CONV_ABS)

        print("=== Winter-optimized thresholds (calibrated on Feb 2025; no domain crop) ===")
        print(f"Calibration window: {CAL_START} .. {CAL_END}")
        print(f"Convergence variable: {conv_name}")
        print(f"CAI_THR  (p{CAI_PCTL})  = {CAI_THR:.3f}")
        print(f"KI_THR   (p{KI_PCTL})   = {KI_THR:.3f}")
        print(f"CONV_THR (p{CONV_PCTL}) = {CONV_THR:.6e} 1/s")
        print(f"MIN_SCORE = {MIN_SCORE}")

    else:
        # Fallback (original “generic” thresholds)
        CAI_THR = 10.0
        KI_THR = 30.0
        CONV_THR = 2.0e-5

    # Conditions
    cond_cai = cai >= CAI_THR
    cond_ki = ki >= KI_THR
    cond_conv = conv >= CONV_THR

    # Score 0..3
    score = cond_cai.astype("int8") + cond_ki.astype("int8") + cond_conv.astype("int8")

    # Composite mask
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
            "CONVERGENCE_VAR": conv_name,
            "CALIBRATE_THRESHOLDS": CALIBRATE_THRESHOLDS,
            "CAL_START": CAL_START,
            "CAL_END": CAL_END,
            "CAI_PCTL": CAI_PCTL,
            "KI_PCTL": KI_PCTL,
            "CONV_PCTL": CONV_PCTL,
            "CAI_THR": float(CAI_THR),
            "KI_THR": float(KI_THR),
            "CONV_THR": float(CONV_THR),
            "MIN_SCORE": MIN_SCORE,
            "notes": (
                "Composite instability mask using CAI, K_Index, and convergence. "
                "Thresholds optimized by calibrating on February 2025 distribution. "
                "No domain cropping applied. Mask=score>=MIN_SCORE."
            ),
        },
    )

    enc = {v: {"zlib": True, "complevel": 1} for v in ds_out.data_vars}
    ds_out.to_netcdf(OUT_MASK_FILE, encoding=enc)
    print(f"Saved composite mask netcdf → {OUT_MASK_FILE}")

    if SAVE_PLOTS:
        for t in range(ds_out.sizes["time"]):
            plot_mask_frame(ds_out, t)


if __name__ == "__main__":
    main()
