#!/usr/bin/env python3
"""
03_visualize.py

- Loads cache/derived_oct2025.nc
- Saves plots for ALL calculated atmospheric indexes
- Uses FIXED color scale per variable (stable over time)
- Output structure unchanged:
    plots/<VAR>/<VAR>_00000.png
"""

import os
import numpy as np
import xarray as xr
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import cartopy.crs as ccrs
import cartopy.feature as cfeature

INPUT_FILE = os.path.join("cache", "derived.nc")
PLOT_DIR = "plots"

# Color scaling configuration
VMIN_PCTL = 5
VMAX_PCTL = 95
N_LEVELS = 21


# ----------------------------
# Utility functions
# ----------------------------
def safe_time_str(dt64) -> str:
    try:
        return np.datetime_as_string(dt64, unit="h").replace(":", "")
    except Exception:
        return str(dt64).replace(":", "")


def compute_global_limits(ds: xr.Dataset, var_name: str):
    """
    Compute stable (vmin, vmax) for a variable using all time steps.
    Uses robust percentiles.
    """
    arr = ds[var_name].values
    finite = np.isfinite(arr)

    if not np.any(finite):
        return -1.0, 1.0

    vmin = float(np.nanpercentile(arr, VMIN_PCTL))
    vmax = float(np.nanpercentile(arr, VMAX_PCTL))

    if not np.isfinite(vmin) or not np.isfinite(vmax) or np.isclose(vmin, vmax):
        vmin = float(np.nanmin(arr))
        vmax = float(np.nanmax(arr))

    if not np.isfinite(vmin) or not np.isfinite(vmax) or np.isclose(vmin, vmax):
        vmin, vmax = -1.0, 1.0

    return vmin, vmax


# ----------------------------
# Plotting
# ----------------------------
def plot_and_save(ds, var_name, time_idx, vmin, vmax):
    out_dir = os.path.join(PLOT_DIR, var_name)
    os.makedirs(out_dir, exist_ok=True)

    data = ds.isel(time=time_idx)
    field = data[var_name]
    time_label = safe_time_str(data.time.values)

    fig = plt.figure(figsize=(12, 8))
    ax = plt.axes(projection=ccrs.PlateCarree())

    ax.add_feature(cfeature.COASTLINE, linewidth=0.8)
    ax.add_feature(cfeature.BORDERS, linestyle=":", linewidth=0.5)

    levels = np.linspace(vmin, vmax, N_LEVELS)

    cf = ax.contourf(
        data.longitude,
        data.latitude,
        field,
        levels=levels,
        cmap="turbo",
        extend="both",
        transform=ccrs.PlateCarree(),
    )

    units = field.attrs.get("units", "")
    cbar = plt.colorbar(cf, ax=ax, shrink=0.85)
    cbar.set_label(f"{var_name} [{units}]" if units else var_name)

    ax.set_title(f"{var_name} | {time_label}", fontsize=13)

    outfile = os.path.join(out_dir, f"{var_name}_{time_idx:05d}.png")
    plt.savefig(outfile, dpi=150, bbox_inches="tight")
    plt.close(fig)


# ----------------------------
# Main
# ----------------------------
def main():
    ds = xr.open_dataset(INPUT_FILE)

    variables = list(ds.data_vars)

    print("Dataset loaded.")
    print(f"Available calculated variables: {variables}")
    print(f"Total time steps: {len(ds.time)}")
    print("Computing stable color ranges per variable...")

    # --- Compute stable ranges ONCE ---
    color_limits = {}
    for var in variables:
        vmin, vmax = compute_global_limits(ds, var)
        color_limits[var] = (vmin, vmax)
        print(f"  {var:20s} → vmin={vmin:.2f}, vmax={vmax:.2f}")

    print("\nSaving plots with fixed color scales...")

    # --- Plot all frames ---
    for var in variables:
        vmin, vmax = color_limits[var]
        print(f"\n=== Variable: {var} ===")

        for t_idx in range(len(ds.time)):
            plot_and_save(ds, var, t_idx, vmin, vmax)

            if (t_idx + 1) % 10 == 0 or (t_idx + 1) == len(ds.time):
                print(f"  {t_idx+1}/{len(ds.time)}", end="\r")

        print(f"  Done: {var}")

    print("\nAll atmospheric index plots saved with stable color scales.")


if __name__ == "__main__":
    main()
