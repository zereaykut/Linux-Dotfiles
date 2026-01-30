import xarray as xr
import glob
import os
import numpy as np

# --- Configuration ---
INPUT_DIR = '/home/spidy/Projects/Data/mto/'  # Directory containing your .grib files
CACHE_FILE = 'cache_data.nc'
TARGET_HOURS = [0, 6, 12, 18]  # The daily 6h range you requested

def preprocess_grib(ds):
    """Standardize coordinates for merging."""
    # Rename vertical coordinate to a common name if needed (isobaricInhPa is standard in cfgrib)
    # Ensure time, latitude, longitude are consistent
    return ds

def load_and_merge_levels(var_prefix, years):
    """
    Loads split-level files (e.g., 100-400, 200-700) and concatenates them 
    along the vertical axis (isobaricInhPa).
    """
    full_ds_list = []
    
    for year in years:
        # Pattern match for specific variable and year, ignoring the level suffix part for now
        # We look for all files matching the variable and year
        pattern = os.path.join(INPUT_DIR, f"{var_prefix}_{year}_*_hPa.grib")
        files = glob.glob(pattern)
        
        if not files:
            print(f"Warning: No files found for {var_prefix} {year}")
            continue
            
        # Load all level chunks for this variable/year
        level_chunks = []
        for f in files:
            print(f"Loading {f}...")
            # chunks={} enables dask (lazy loading)
            ds = xr.open_dataset(f, engine='cfgrib', chunks={'time': 24})
            level_chunks.append(ds)
        
        # Merge the level chunks for this year (concatenating along pressure levels)
        if level_chunks:
            year_ds = xr.merge(level_chunks)
            full_ds_list.append(year_ds)

    if not full_ds_list:
        return None
        
    # Concatenate all years along time
    combined = xr.concat(full_ds_list, dim='time')
    return combined.sortby('time').sortby('isobaricInhPa')

def main():
    if os.path.exists(CACHE_FILE):
        print(f"Cache found at {CACHE_FILE}. Delete it if you want to rebuild.")
        return

    print("--- Starting Preprocessing ---")
    years = ['2023', '2024', '2025']

    # 1. Load 3D Variables (Pressure Levels)
    # We explicitly merge the weird level splits here
    print("Processing Humidity (q)...")
    ds_q = load_and_merge_levels('era5_q', years)
    
    print("Processing Temperature (t)...")
    ds_t = load_and_merge_levels('era5_t', years)

    # Note: U/V in your list only have 850, 950, 1000. 
    # If you need them for shear calc, we load them. If not needed for CAPE, we skip to save RAM.
    # We will load them to be safe.
    print("Processing Wind (u/v pl)...")
    ds_u_pl = load_and_merge_levels('era5_u', years)
    ds_v_pl = load_and_merge_levels('era5_v', years)

    # 2. Load 2D Variables (Surface)
    # These usually contain all years in one file or split by year.
    # Your list shows: era5_d2m_2023_2024_2025.grib (Already merged years)
    print("Processing Surface variables...")
    
    sfc_files = [
        'era5_d2m_2023_2024_2025.grib',
        'era5_t2m_2023_2024_2025.grib',
        'era5_sp_2023_2024_2025.grib',
        'era5_u10m_2023_2024_2025.grib',
        'era5_v10m_2023_2024_2025.grib'
    ]
    
    sfc_datasets = []
    for f in sfc_files:
        path = os.path.join(INPUT_DIR, f)
        if os.path.exists(path):
            ds = xr.open_dataset(path, engine='cfgrib', chunks={'time': 24})
            sfc_datasets.append(ds)
        else:
            print(f"Warning: {f} not found.")

    ds_sfc = xr.merge(sfc_datasets)

    # 3. Merge Everything
    # We merge 3D vars first
    ds_3d = xr.merge([ds_q, ds_t]) # u_pl and v_pl might have different levels, merge carefully if needed
    
    # 4. Temporal Selection (Daily 6h range)
    # Select only 00, 06, 12, 18 UTC
    print(f"Filtering for hours: {TARGET_HOURS}...")
    ds_3d = ds_3d.sel(time=ds_3d.time.dt.hour.isin(TARGET_HOURS))
    ds_sfc = ds_sfc.sel(time=ds_sfc.time.dt.hour.isin(TARGET_HOURS))

    # 5. Final Merge
    # Combine surface and 3D data. xarray handles broadcasting (sfc applies to all levels)
    final_ds = xr.merge([ds_3d, ds_sfc])

    # 6. Save to Cache
    # Using float32 saves space. compression helps speed.
    encoding = {v: {'zlib': True, 'complevel': 5, 'dtype': 'float32'} for v in final_ds.data_vars}
    print(f"Saving to {CACHE_FILE}...")
    final_ds.to_netcdf(CACHE_FILE, encoding=encoding)
    print("Preprocessing Complete.")

if __name__ == "__main__":
    main()
