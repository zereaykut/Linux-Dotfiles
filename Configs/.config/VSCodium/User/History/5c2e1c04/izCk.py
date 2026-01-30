#!/usr/bin/env python3
"""
04_mask_plot_only.py

PLOT-ONLY script:
- No data processing, no thresholding, no mask logic.
- Only loads an already-produced dataset (e.g., instability_mask.nc),
  crops to the desired bbox, and plots ONLY that domain.

Expected variables in the input file:
  - Composite_Score
  - Composite_Mask

Output:
  - PNG frames under plots/tez/
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
IN_MASK_FILE = os.path.join("cache", "instability_mask.nc")  # already produced
PLOT_DIR = os.path.join("plots", "tez")
SAVE_PLOTS = True


# ------------------------------------------------------------------
# Time selection (optional)
# ------------------------------------------------------------------
TIME_START = "2025-02-01"
TIME_END   = "2025-03-01"   # exclusive (optional)


# ------------------------------------------------------------------
# Domain (YOUR requested bbox)
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
    if "latitude" not in ds.coords or "longitude" not in ds.coords:
        raise KeyError("Dataset must have 'latitude' and 'longitude' coordinates.")

    lat = ds.latitude
    if lat.values[0] > lat.values[-1]:
        ds = ds.sel(latitude=slice(BBOX["lat_max"], BBOX["lat_min"]))
    else:
        ds = ds.sel(latitude=slice(BBOX["lat_min"], BBOX["lat_max"]))

    ds = ds.sel(longitude=slice(BBOX["lon_min"], BBOX["lon_max"]))
    return ds


def plot_frame(ds_plot: xr.Dataset, t_idx: int) -> None:
    os.makedirs(PLOT_DIR, exist_ok=True)

    data = ds_plot.isel(time=t_idx)
    score = data["Composite_Score"]
    mask = data["Composite_Mask"]

    fig = plt.figure(figsize=(12, 8))
    ax = plt.axes(projection=ccrs.PlateCarree())

    # ✅ Plot ONLY bbox extent
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
        levels=np.arange(-0.5, 6.6, 1.0),  # assumes score 0..6
        cmap="viridis",
        transform=ccrs.PlateCarree(),
    )
    plt.colorbar(cf, ax=ax, label="Composite Score")

    ax.contour(
        data.longitude,
        data.latitude,
        mask.astype(int),
        levels=[0.5],
        colors="red",
        linewidths=1.2,
        transform=ccrs.PlateCarree(),
    )

    ax.set_title(f"Composite Mask | {_safe_time_str(data.time.values)}", fontsize=12)

    out_png = os.path.join(PLOT_DIR, f"Composite_Mask_{t_idx:05d}.png")
    plt.savefig(out_png, dpi=150, bbox_inches="tight")
    plt.close(fig)


def main():
    if not os.path.exists(IN_MASK_FILE):
        raise FileNotFoundError(f"{IN_MASK_FILE} not found (expected precomputed output).")

    ds = xr.open_dataset(IN_MASK_FILE)

    # Optional time filtering
    if "time" in ds.coords:
        ds = ds.sel(time=slice(TIME_START, TIME_END))

    # Crop to bbox
    ds = crop_to_bbox(ds)

    # Check required vars
    for v in ["Composite_Score", "Composite_Mask"]:
        if v not in ds:
            raise KeyError(f"Missing variable '{v}' in {IN_MASK_FILE}")

    if SAVE_PLOTS:
        nT = ds.sizes.get("time", 1)
        for t in range(nT):
            plot_frame(ds, t)

    print(f"Done. Plots saved under: {PLOT_DIR}")
    print(f"Extent used: {BBOX}")


if __name__ == "__main__":
    main()
