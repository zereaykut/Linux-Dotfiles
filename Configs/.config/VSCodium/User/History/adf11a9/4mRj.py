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

# --- Thresholds (start sensible; tune after you inspect histograms) ---
# CAI is your proxy: (T2m - T500) + (Td850 - Td700)
CAI_THR = 10.0            # proxy units

# K-Index typical thunder threshold often ~30–35
KI_THR = 30.0             # degC-like units

# Convergence typical scale ~1e-5 to 1e-4 1/s depending on resolution
CONV_THR = 2.0e-5         # 1/s

# Decision: require at least 2/3 conditions
MIN_SCORE = 2


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

    for v in ["CAI", "K_Index", "Convergence_10m"]:
        if v not in ds.data_vars:
            raise KeyError(f"Missing variable '{v}' in derived file. Available: {list(ds.data_vars)}")

    cai = ds["CAI"]
    ki = ds["K_Index"]
    conv = ds["Convergence_10m"]

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
            "CAI_THR": CAI_THR,
            "KI_THR": KI_THR,
            "CONV_THR": CONV_THR,
            "MIN_SCORE": MIN_SCORE,
            "notes": "Composite instability mask using CAI, K_Index, and 10m convergence. Mask=score>=MIN_SCORE.",
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

