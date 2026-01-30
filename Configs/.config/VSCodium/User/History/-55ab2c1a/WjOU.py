import xarray as xr
import matplotlib.pyplot as plt
import cartopy.crs as ccrs
import cartopy.feature as cfeature
import numpy as np

INPUT_FILE = 'derived_oct2025.nc'

def plot_frame(ds, time_idx):
    data = ds.isel(time=time_idx)
    time_label = str(data.time.values)[:16]
    
    # Setup plot
    fig = plt.figure(figsize=(12, 8))
    ax = plt.axes(projection=ccrs.PlateCarree())
    ax.add_feature(cfeature.COASTLINE)
    ax.add_feature(cfeature.BORDERS, linestyle=':')

    # 1. Plot Stability (CAI/K-Index) filled contours
    # High K-Index (>30) implies convection potential
    cai = data['Stability_Index_CAI']
    mesh = ax.contourf(data.longitude, data.latitude, cai, 
                       levels=np.arange(10, 45, 2), 
                       cmap='turbo', transform=ccrs.PlateCarree(), extend='both')
    
    plt.colorbar(mesh, orientation='vertical', label='Stability Index (CAI/K-Index) [High=Unstable]')

    # 2. Plot Shear vectors (barbs)
    # Subsample to avoid clutter (skip every 5th point)
    skip = 5
    ax.barbs(data.longitude[::skip], data.latitude[::skip], 
             data.u10m[::skip, ::skip] if 'u10m' in data else 0, # Placeholder if u10m not in derived
             data.v10m[::skip, ::skip] if 'v10m' in data else 0,
             length=5, color='black', alpha=0.5)

    plt.title(f"Cloud Tracking Parameters: {time_label}")
    plt.show()

def main():
    ds = xr.open_dataset(INPUT_FILE)
    
    print("Dataset loaded. Select a time index to plot.")
    print(f"Total time steps: {len(ds.time)}")
    
    # Plot the first time step as example
    plot_frame(ds, 0)
    
    # Plot a step from summer (likely more convection)
    if len(ds.time) > 200:
        plot_frame(ds, 200)

if __name__ == "__main__":
    main()
