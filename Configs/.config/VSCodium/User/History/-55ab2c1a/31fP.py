#!/usr/bin/env python3
"""
03_visualize.py

- Loads derived_oct2025.nc
- Plots CAPE_Proxy (or other stability fields if added later)
- Saves figures into ./plots directory (no GUI required)
"""

import os
import numpy as np
import xarray as xr
import matplotlib
matplotlib.use("Agg")  # force non-interactive backend
import matplotlib.pyplot as plt
import cartopy.crs as ccrs
import cartopy.feature as cfeature

INPUT_FILE = "derived_oct2025.nc"
PLOT_DIR = "plots"

STABILITY_PRIORITY = ["Stability_Index_CAI", "K_Index", "CAPE_Proxy"]


def pick_stability_var(ds: xr.Dataset) -> str:
    for v in STABILITY_PRIORITY:
        if v in ds.data_vars:
            return v
    raise KeyError(
        f"No stability variable found. Tried {STABILITY_PRIORITY}, "
        f"available: {list(ds.data_vars)}"
    )


def plot_frame(ds: xr.Dataset, time_idx: int):
    os.makedirs(PLOT_DIR, exist_ok=True)

    stab_var = pick_stability_var(ds)
    data = ds.isel(time=time_idx)
    field = data[stab_var]

    time_str = np.datetime_as_string(data.time.values, unit="h")

    fig = plt.figure(figsize=(12, 8))
    ax = plt.axes(projection=ccrs.PlateCarree())

    ax.add_feature(cfeature.COASTLINE, linewidth=0.8)
    ax.add_feature(cfeature.BORDERS, linestyle=":", linewidth=0.5)
    ax.set_title(f"{stab_var} | {time_str}", fontsize=13)

    # Robust color limits
    vmin = np.nanpercentile(field.values, 5)
    vmax = np.nanpercentile(field.values, 95)

    if not np.isfinite(vmin) or not np.isfinite(vmax) or np.isclose(vmin, vmax):
        vmin, vmax = -10, 10

    levels = np.linspace(vmin, vmax, 21)

    cf = ax.contourf(
        data.longitude,
        data.latitude,
        field,
        levels=levels,
        cmap="turbo",
        extend="both",
        transform=ccrs.PlateCarree(),
    )

    cbar = plt.colorbar(cf, ax=ax, shrink=0.85)
    cbar.set_label(f"{stab_var} (proxy units)")

    outfile = f"{PLOT_DIR}/{stab_var}_{time_idx:04d}.png"
    plt.savefig(outfile, dpi=150, bbox_inches="tight")
    plt.close(fig)

    print(f"Saved: {outfile}")


def main():
    ds = xr.open_dataset(INPUT_FILE)

    print("Dataset loaded.")
    print(f"Available variables: {list(ds.data_vars)}")
    print(f"Total time steps: {len(ds.time)}")

    # Example: save first 10 frames
    for t in range(min(10, len(ds.time))):
        plot_frame(ds, t)


if __name__ == "__main__":
    main()
