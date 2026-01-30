#!/usr/bin/env python3
"""
04_score_plot_only.py

PLOT-ONLY script:
- NO masking
- NO thresholding
- NO condition logic
- Only plots Composite_Score
- Only for the selected Turkey domain
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
IN_FILE = os.path.join("cache", "instability_mask.nc")  # already computed dataset
PLOT_DIR = os.path.join("plots", "tez")
SAVE_PLOTS = True


# ------------------------------------------------------------------
# Time selection (optional)
# ------------------------------------------------------------------
TIME_START = "2025-02-01"
TIME_END   = "2025-03-01"   # exclusive


# ------------------------------------------------------------------
# Domain (ONLY this region will be plotted)
# ------------------------------------------------------------------
BBOX = {
    "lat_min": 35.25,
    "lat_max": 45.00,
    "lon_min": 25.00,
    "lon_max": 34.75,
}


def _safe_time_str(dt64) -> str:
    try:
        return np.datetime_as_string(dt64, unit="h").replace(":", "")
    except Exception:
        return str(dt64).replace(":", "")


def crop_to_bbox(ds: xr.Dataset) -> xr.Dataset:
    """Crop dataset to bbox, handling descending/ascending latitude."""
    lat = ds.latitude
    if lat.values[0] > lat.values[-1]:
        ds = ds.sel(latitude=slice(BBOX["lat_max"], BBOX["lat_min"]))
    else:
        ds = ds.sel(latitude=slice(BBOX["lat_min"], BBOX["lat_max"]))

    ds = ds.sel(longitude=slice(BBOX["lon_min"], BBOX["lon_max"]))
    return ds


def plot_score_frame(ds: xr.Dataset, t_idx: int):
    os.makedirs(PLOT_DIR, exist_ok=True)

    data = ds.isel(time=t_idx)
    # score = data["Composite_Score"]
    score = np.full_like(data["Composite_Score"], np.nan, dtype=np.float32)

    fig = plt.figure(figsize=(12, 8))
    ax = plt.axes(projection=ccrs.PlateCarree())

    # ✅ Only requested domain
    ax.set_extent(
        [BBOX["lon_min"], BBOX["lon_max"], BBOX["lat_min"], BBOX["lat_max"]],
        crs=ccrs.PlateCarree(),
    )

    ax.add_feature(cfeature.COASTLINE, linewidth=0.8)
    ax.add_feature(cfeature.BORDERS, linestyle=":", linewidth=0.5)

    gl = ax.gridlines(draw_labels=True, linewidth=0.3, alpha=0.5)
    gl.top_labels = False
    gl.right_labels = False

    cf = ax.contourf(
        data.longitude,
        data.latitude,
        score,
        levels=np.arange(-0.5, 6.6, 1.0),  # assumes score range 0–6
        cmap="viridis",
        transform=ccrs.PlateCarree(),
    )

    cbar = plt.colorbar(cf, ax=ax)
    cbar.set_label("Composite Instability Score")

    ax.set_title(
        f"Composite Instability Score | {_safe_time_str(data.time.values)}",
        fontsize=12,
    )

    out_png = os.path.join(PLOT_DIR, f"Composite_Score_{t_idx:05d}.png")
    plt.savefig(out_png, dpi=150, bbox_inches="tight")
    plt.close(fig)


def main():
    if not os.path.exists(IN_FILE):
        raise FileNotFoundError(f"{IN_FILE} not found")

    ds = xr.open_dataset(IN_FILE)

    if "time" in ds.coords:
        ds = ds.sel(time=slice(TIME_START, TIME_END))

    ds = crop_to_bbox(ds)

    if "Composite_Score" not in ds:
        raise KeyError("Composite_Score not found in dataset")

    if SAVE_PLOTS:
        nT = ds.sizes.get("time", 1)
        for t in range(nT):
            plot_score_frame(ds, t)

    print("Done.")
    print(f"Plots saved in: {PLOT_DIR}")
    print(f"Domain used: {BBOX}")


if __name__ == "__main__":
    main()
