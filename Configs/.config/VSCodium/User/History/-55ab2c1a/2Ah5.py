import xarray as xr
import matplotlib.pyplot as plt
import cartopy.crs as ccrs
import cartopy.feature as cfeature
import numpy as np

INPUT_FILE = "derived_oct2025.nc"

# Prefer this variable name if present; fall back to CAPE_Proxy
PRIMARY_STABILITY_VARS = ["Stability_Index_CAI", "K_Index", "CAPE_Proxy"]

def pick_stability_var(ds: xr.Dataset) -> str:
    for v in PRIMARY_STABILITY_VARS:
        if v in ds.data_vars:
            return v
    raise KeyError(
        f"None of the expected stability variables exist. "
        f"Looked for: {PRIMARY_STABILITY_VARS}. "
        f"Available data_vars: {list(ds.data_vars)}"
    )

def plot_frame(ds, time_idx: int):
    data = ds.isel(time=time_idx)
    time_label = str(data.time.values)[:16]

    stab_var = pick_stability_var(ds)
    cai = data[stab_var]

    # Setup plot
    fig = plt.figure(figsize=(12, 8))
    ax = plt.axes(projection=ccrs.PlateCarree())
    ax.add_feature(cfeature.COASTLINE)
    ax.add_feature(cfeature.BORDERS, linestyle=":")

    # Choose plotting levels based on variable
    # - If it's CAPE_Proxy (a lapse-rate proxy in K), values could be negative/positive
    # - If it's K-index, typical range ~ 0..50+
    if stab_var.lower().startswith("cape_proxy") or stab_var == "CAPE_Proxy":
        vmin = float(np.nanpercentile(cai.values, 5))
        vmax = float(np.nanpercentile(cai.values, 95))
        # avoid degenerate levels
        if not np.isfinite(vmin) or not np.isfinite(vmax) or np.isclose(vmin, vmax):
            vmin, vmax = -10.0, 10.0
        levels = np.linspace(vmin, vmax, 21)
        cbar_label = f"{stab_var} [proxy units]"
    else:
        levels = np.arange(10, 45, 2)
        cbar_label = f"{stab_var} [Higher = more unstable]"

    # 1) Filled contours
    mesh = ax.contourf(
        data.longitude,
        data.latitude,
        cai,
        levels=levels,
        cmap="turbo",
        transform=ccrs.PlateCarree(),
        extend="both",
    )
    plt.colorbar(mesh, orientation="vertical", label=cbar_label)

    # 2) Optional wind barbs if present
    # Your derived file likely does NOT include u10m/v10m (your current thermo output doesn't save them).
    if ("u10m" in data.data_vars) and ("v10m" in data.data_vars):
        skip = 5
        ax.barbs(
            data.longitude.values[::skip],
            data.latitude.values[::skip],
            data["u10m"].values[::skip, ::skip],
            data["v10m"].values[::skip, ::skip],
            length=5,
            color="black",
            alpha=0.5,
            transform=ccrs.PlateCarree(),
        )

    plt.title(f"Cloud Tracking Parameters ({stab_var}): {time_label}")
    plt.show()

def main():
    ds = xr.open_dataset(INPUT_FILE)

    print("Dataset loaded. Select a time index to plot.")
    print(f"Total time steps: {len(ds.time)}")
    print(f"Available variables: {list(ds.data_vars)}")

    # Plot the first time step as example
    plot_frame(ds, 0)

    # Example additional frame if long enough
    if len(ds.time) > 200:
        plot_frame(ds, 200)

if __name__ == "__main__":
    main()
