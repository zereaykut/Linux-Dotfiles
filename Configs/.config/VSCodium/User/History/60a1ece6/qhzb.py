import xarray as xr
import glob
import os
import numpy as np

# --- Configuration ---
INPUT_DIR = '/home/spidy/Projects/Data/mto/'  # Directory containing your .grib files
CACHE_FILE = 'cache_oct2025.nc'

# Filter Settings
START_DATE = '2025-10-01'
END_DATE = '2025-10-30'
TARGET_HOURS = [0, 6, 12, 18]
TARGET_YEARS = ['2025'] # Only load 2025 files since range is within 2025

def load_and_merge_levels(var_prefix):
    """Loads split-level files for the target year and merges vertical levels."""
    full_ds_list = []
    
    for year in TARGET_YEARS:
        # Pattern match for specific variable and year
        pattern = os.path.join(INPUT_DIR, f"{var_prefix}_{year}_*_hPa.grib")
        files = glob.glob(pattern)
        
        if not files:
            print(f"  Warning: No files found for {var_prefix} {year}")
            continue
            
        level_chunks = []
        for f in files:
            try:
                # Load with time chunking for memory efficiency
                ds = xr.open_dataset(f, engine='cfgrib', chunks={'time': 48})
                level_chunks.append(ds)
            except Exception as e:
                print(f"  Error loading {f}: {e}")
        
        if level_chunks:
            # Merge vertical levels for this year
            year_ds = xr.merge(level_chunks)
            full_ds_list.append(year_ds)

    if not full_ds_list:
        return None
        
    combined = xr.concat(full_ds_list, dim='time')
    return combined.sortby('time').sortby('isobaricInhPa')

def main():
    if os.path.exists(CACHE_FILE):
        os.remove(CACHE_FILE) # Force rebuild for new date range

    print(f"--- Processing Data for {START_DATE} to {END_DATE} ---")

    # 1. Load 3D Variables (Pressure Levels)
    print("Loading Humidity (q)...")
    ds_q = load_and_merge_levels('era5_q')
    
    print("Loading Temperature (t)...")
    ds_t = load_and_merge_levels('era5_t')

    # Load Wind (u/v) for shear calc
    print("Loading Wind (u/v)...")
    ds_u = load_and_merge_levels('era5_u')
    ds_v = load_and_merge_levels('era5_v')

    # 2. Load 2D Variables (Surface)
    # Note: Surface files usually contain all years (2023-2025). We load them and slice later.
    print("Loading Surface variables...")
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
            ds = xr.open_dataset(path, engine='cfgrib', chunks={'time': 48})
            sfc_datasets.append(ds)
    
    if sfc_datasets:
        ds_sfc = xr.merge(sfc_datasets)
    else:
        raise FileNotFoundError("No surface files found!")

    # 3. Merge 3D vars
    # We allow loose alignment here in case some vars have different levels
    ds_3d = xr.merge([ds_q, ds_t, ds_u, ds_v])

    # 4. Filter DATE and HOUR
    print(f"Slicing time range: {START_DATE} -> {END_DATE}")
    
    # Slice 3D
    ds_3d = ds_3d.sel(time=slice(START_DATE, END_DATE))
    ds_3d = ds_3d.sel(time=ds_3d.time.dt.hour.isin(TARGET_HOURS))
    
    # Slice Surface
    ds_sfc = ds_sfc.sel(time=slice(START_DATE, END_DATE))
    ds_sfc = ds_sfc.sel(time=ds_sfc.time.dt.hour.isin(TARGET_HOURS))

    # 5. Final Merge & Save
    final_ds = xr.merge([ds_3d, ds_sfc])
    
    print(f"Final dataset shape: {final_ds.time.size} time steps")
    print(f"Saving to {CACHE_FILE}...")
    
    # Compression encoding
    encoding = {v: {'zlib': True, 'complevel': 5, 'dtype': 'float32'} for v in final_ds.data_vars}
    final_ds.to_netcdf(CACHE_FILE, encoding=encoding)
    print("Done.")

if __name__ == "__main__":
    main()