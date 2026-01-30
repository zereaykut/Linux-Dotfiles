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

# ------------------------------------------------------------
# Winter optimization: FEBRUARY 2025 threshold calibration
# (We DO NOT crop domain. Only use Feb-2025 subset to set thresholds.)
# ------------------------------------------------------------
CALIBRATE_FOR_FEB_2025 = True
FEB_START = "2025-02-01"
FEB_END = "2025-03-01"  # exclusive end

# Use percentile thresholds computed from Feb-2025 distribution.
# Winter: instability signals are weaker than summer, but forcing (convergence) matters more.
CAI_PCTL = 70     # lower than summer fixed 10; adapts to winter distribution
KI_PCTL = 65      # winter convection can occur with lower KI
CONV_PCTL = 85    # focus on strongest convergence forcing

# Decision: require at least 2/3 conditions (robust). If too sparse, set MIN_SCORE=1.
MIN_SCORE = 2

# Safety floor for convergence thresholds (1/s)
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

    # --- choose convergence field (prefer 850 for winter if present) ---
    conv_var = None
    if "Convergence_850" in ds.data_vars:
        conv_var = "Convergence_850"
    elif "Convergence_10m" in ds.data_vars:
        conv_var = "Convergence_10m"
    else:
        raise KeyError(
            "Need Convergence_850 or Convergence_10m in derived file. "
            f"Available: {list(ds.data_vars)}"
        )

    for v in ["CAI", "K_Index", conv_var]:
        if v not in ds.data_vars:
            raise KeyError(f"Missing variable '{v}' in derived file. Available: {list(ds.data_vars)}")

    cai = ds["CAI"]
    ki = ds["K_Index"]
    conv = ds[conv_var]

    # ------------------------------------------------------------
    # Winter-tuned thresholds (Feb 2025 calibration only)
    # ------------------------------------------------------------
    if CALIBRATE_FOR_FEB_2025:
        if "time" not in ds.coords:
            raise KeyError("Dataset has no 'time' coordinate, cannot calibrate for Feb 2025.")

        ds_feb = ds.sel(time=slice(FEB_START, FEB_END))
        if ds_feb.sizes.get("time", 0) == 0:
            raise ValueError(f"No timesteps found in Feb 2025 range {FEB_START}..{FEB_END}")

        cai_thr = _pctl_threshold(ds_feb["CAI"], CAI_PCTL)
        ki_thr = _pctl_threshold(ds_feb["K_Index"], KI_PCTL)
        conv_thr = _pctl_threshold(ds_feb[conv_var], CONV_PCTL)

        # Safety floors
        if not np.isfinite(cai_thr):
            cai_thr = 0.0
        if not np.isfinite(ki_thr):
            ki_thr = 0.0
        if not np.isfinite(conv_thr):
            conv_thr = MIN_CONV_ABS
        conv_thr = max(conv_thr, MIN_CONV_ABS)

        print("=== Feb 2025 winter-calibrated thresholds (no domain crop) ===")
        print(f"Calibrated on time window: {FEB_START} .. {FEB_END}")
        print(f"Convergence variable used: {conv_var}")
        print(f"CAI_THR  = p{CAI_PCTL}  -> {cai_thr:.3f}")
        print(f"KI_THR   = p{KI_PCTL}  -> {ki_thr:.3f}")
        print(f"CONV_THR = p{CONV_PCTL} -> {conv_thr:.6e} 1/s")
        print(f"MIN_SCORE = {MIN_SCORE}")

    else:
        # Fallback to your old static thresholds (not recommended for winter)
        cai_thr = 10.0
        ki_thr = 30.0
        conv_thr = 2.0e-5

    # Conditions
    cond_cai = cai >= cai_thr
    cond_ki = ki >= ki_thr
    cond_conv = conv >= conv_thr

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
            "CALIBRATE_FOR_FEB_2025": CALIBRATE_FOR_FEB_2025,
            "FEB_START": FEB_START,
            "FEB_END": FEB_END,
            "CONVERGENCE_VAR": conv_var,
            "CAI_PCTL": CAI_PCTL,
            "KI_PCTL": KI_PCTL,
            "CONV_PCTL": CONV_PCTL,
            "CAI_THR": float(cai_thr),
            "KI_THR": float(ki_thr),
            "CONV_THR": float(conv_thr),
            "MIN_SCORE": MIN_SCORE,
            "notes": (
                "Composite instability mask using CAI, K_Index, and convergence. "
                "Thresholds calibrated using Feb-2025 distribution (winter-tuned). "
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
