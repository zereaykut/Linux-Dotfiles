#!/usr/bin/env python3
"""
04_mask.py

Composite Cu mask using:
  - CAI
  - Convergence_mean
  - Convergence_10m
  - DD_LowMean_1000_850   (LOW values are favorable)
  - Vorticity_mean
  - Vorticity_10m

Mask logic:
  - Score = sum of satisfied conditions (0..6)
  - Mask = Score >= MIN_SCORE

Thresholds are percentile-based and computed on the filtered subset.
For vorticity, we use the magnitude |ζ| since both cyclonic and anticyclonic
shear zones may support convective triggering depending on regime.

(If you prefer cyclonic-only: replace abs(vort) with vort.)
"""

import os
import numpy as np
import xarray as xr

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import cartopy.crs as ccrs
import cartopy.feature as cfeature


# ------------------------------------------------------------------
# I/O
# ------------------------------------------------------------------
DERIVED_FILE = os.path.join("cache", "derived.nc")
OUT_MASK_FILE = os.path.join("cache", "instability_mask.nc")

SAVE_PLOTS = True
PLOT_DIR = os.path.join("plots", "tez")  # bumped version


# ------------------------------------------------------------------
# Time / region
# ------------------------------------------------------------------
TIME_START = "2025-02-01"
TIME_END   = "2025-03-01"   # exclusive

CROP_TURKEY = True
TURKEY_BBOX = {
    "lat_min": 35.25,
    "lat_max": 45,
    "lon_min": 25,
    "lon_max": 34.75,
}


# ------------------------------------------------------------------
# Percentile thresholds
# ------------------------------------------------------------------
CAI_PCTL = 70

CONVMEAN_PCTL = 85
CONV10M_PCTL  = 85

# Dewpoint depression: LOW values favorable → use LOW percentile
DD_LOW_PCTL = 30

# Vorticity: use magnitude |ζ| (HIGH values favorable)
VORTMEAN_PCTL = 85
VORT10M_PCTL  = 85

# Require at least N of signals
# (Now we have 6 signals total)
MIN_SCORE = 4

# Safety floors
MIN_CONV_ABS = 1.0e-6   # 1/s
MIN_VORT_ABS = 1.0e-6   # 1/s
MAX_DD_ABS   = 25.0     # K (safety cap)


# ------------------------------------------------------------------
def _safe_time_str(dt64) -> str:
    try:
        return np.datetime_as_string(dt64, unit="h").replace(":", "")
    except Exception:
        return str(dt64).replace(":", "")


def _crop_to_bbox(ds: xr.Dataset) -> xr.Dataset:
    if not CROP_TURKEY:
        return ds

    lat = ds.latitude
    if lat.values[0] > lat.values[-1]:
        ds = ds.sel(latitude=slice(TURKEY_BBOX["lat_max"], TURKEY_BBOX["lat_min"]))
    else:
        ds = ds.sel(latitude=slice(TURKEY_BBOX["lat_min"], TURKEY_BBOX["lat_max"]))

    ds = ds.sel(
        longitude=slice(TURKEY_BBOX["lon_min"], TURKEY_BBOX["lon_max"])
    )
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
    score = data["Composite_Score"]
    mask = data["Composite_Mask"]

    fig = plt.figure(figsize=(12, 8))
    ax = plt.axes(projection=ccrs.PlateCarree())
    ax.add_feature(cfeature.COASTLINE, linewidth=0.8)
    ax.add_feature(cfeature.BORDERS, linestyle=":", linewidth=0.5)

    cf = ax.contourf(
        data.longitude,
        data.latitude,
        score,
        levels=np.arange(-0.5, 6.6, 1.0),  # 0..6
        cmap="viridis",
        transform=ccrs.PlateCarree(),
    )
    plt.colorbar(cf, ax=ax, label="Composite Score (0–6)")

    ax.contour(
        data.longitude,
        data.latitude,
        mask.astype(int),
        levels=[0.5],
        colors="red",
        linewidths=1.2,
        transform=ccrs.PlateCarree(),
    )

    ax.set_title(
        f"Cu Composite Mask | {_safe_time_str(data.time.values)}",
        fontsize=12,
    )

    out_png = os.path.join(PLOT_DIR, f"Composite_Mask_{t_idx:05d}.png")
    plt.savefig(out_png, dpi=150, bbox_inches="tight")
    plt.close(fig)


# ------------------------------------------------------------------
def main():
    if not os.path.exists(DERIVED_FILE):
        raise FileNotFoundError(f"{DERIVED_FILE} not found")

    ds = xr.open_dataset(DERIVED_FILE)
    ds = ds.sel(time=slice(TIME_START, TIME_END))
    ds = _crop_to_bbox(ds)

    required = [
        "CAI",
        "Convergence_mean",
        "Convergence_10m",
        "DD_LowMean_1000_850",
        "Vorticity_mean",
        "Vorticity_10m",
    ]
    missing = [v for v in required if v not in ds]
    if missing:
        raise KeyError(f"Missing required variables: {missing}")

    cai = ds["CAI"]
    convm = ds["Convergence_mean"]
    conv10 = ds["Convergence_10m"]
    dd_low = ds["DD_LowMean_1000_850"]

    vortm = ds["Vorticity_mean"]
    vort10 = ds["Vorticity_10m"]

    # Use magnitude for robustness
    vortm_abs = np.abs(vortm)
    vort10_abs = np.abs(vort10)

    # ------------------------------------------------------------------
    # Thresholds
    # ------------------------------------------------------------------
    cai_thr = _pctl_threshold(cai, CAI_PCTL)
    convm_thr = max(_pctl_threshold(convm, CONVMEAN_PCTL), MIN_CONV_ABS)
    conv10_thr = max(_pctl_threshold(conv10, CONV10M_PCTL), MIN_CONV_ABS)

    dd_thr = _pctl_threshold(dd_low, DD_LOW_PCTL)
    if not np.isfinite(dd_thr):
        dd_thr = MAX_DD_ABS
    dd_thr = min(dd_thr, MAX_DD_ABS)

    vortm_thr = max(_pctl_threshold(vortm_abs, VORTMEAN_PCTL), MIN_VORT_ABS)
    vort10_thr = max(_pctl_threshold(vort10_abs, VORT10M_PCTL), MIN_VORT_ABS)

    print("=== Composite mask thresholds ===")
    print(f"CAI ≥ {cai_thr:.3f}")
    print(f"Convergence_mean ≥ {convm_thr:.2e} 1/s")
    print(f"Convergence_10m  ≥ {conv10_thr:.2e} 1/s")
    print(f"|Vorticity_mean| ≥ {vortm_thr:.2e} 1/s")
    print(f"|Vorticity_10m|  ≥ {vort10_thr:.2e} 1/s")
    print(f"DD_LowMean_1000_850 ≤ {dd_thr:.2f} K")
    print(f"MIN_SCORE = {MIN_SCORE} (out of 6)")

    # ------------------------------------------------------------------
    # Conditions
    # ------------------------------------------------------------------
    cond_cai = cai >= cai_thr
    cond_convm = convm >= convm_thr
    cond_conv10 = conv10 >= conv10_thr
    cond_vortm = vortm_abs >= vortm_thr
    cond_vort10 = vort10_abs >= vort10_thr
    cond_dd = dd_low <= dd_thr

    score = (
        cond_cai.astype("int8")
        + cond_convm.astype("int8")
        + cond_conv10.astype("int8")
        + cond_vortm.astype("int8")
        + cond_vort10.astype("int8")
        + cond_dd.astype("int8")
    )

    mask = score >= MIN_SCORE

    ds_out = xr.Dataset(
        {
            "Composite_Score": score,
            "Composite_Mask": mask.astype("int8"),
            "Cond_CAI": cond_cai.astype("int8"),
            "Cond_Convergence_mean": cond_convm.astype("int8"),
            "Cond_Convergence_10m": cond_conv10.astype("int8"),
            "Cond_Vorticity_mean": cond_vortm.astype("int8"),
            "Cond_Vorticity_10m": cond_vort10.astype("int8"),
            "Cond_DD_LowMean_1000_850": cond_dd.astype("int8"),
        },
        coords=ds.coords,
        attrs={
            "CAI_PCTL": CAI_PCTL,
            "CONVMEAN_PCTL": CONVMEAN_PCTL,
            "CONV10M_PCTL": CONV10M_PCTL,
            "VORTMEAN_PCTL": VORTMEAN_PCTL,
            "VORT10M_PCTL": VORT10M_PCTL,
            "DD_LOW_PCTL": DD_LOW_PCTL,
            "MIN_SCORE": MIN_SCORE,
            "notes": (
                "Composite Cu mask using CAI + Convergence_mean + Convergence_10m + "
                "|Vorticity_mean| + |Vorticity_10m| + DD_LowMean_1000_850 (low values favorable). "
                "Vorticity uses magnitude to be sign-robust."
            ),
        },
    )

    ds_out.to_netcdf(OUT_MASK_FILE)
    print(f"Saved → {OUT_MASK_FILE}")

    if SAVE_PLOTS:
        for t in range(ds_out.sizes["time"]):
            plot_mask_frame(ds_out, t)


if __name__ == "__main__":
    main()
