import xarray as xr
import glob
import os
import gc

# --- Configuration ---
INPUT_DIR = './'
FINAL_CACHE_FILE = 'cache_oct2025.nc'

# Filter Settings
START_DATE = '2025-10-01'
END_DATE = '2025-10-30'
TARGET_HOURS = [0, 6, 12, 18]
TARGET_YEAR = '2025'

def process_and_save_variable(var_prefix, output_temp_name):
    """
    Loads raw GRIBs for ONE variable, filters dates immediately, 
    and saves to a temporary NetCDF to free RAM.
    """
    print(f"--> Processing {var_prefix}...")
    
    # 1. Find files for target year only
    pattern = os.path.join(INPUT_DIR, f"{var_prefix}*{TARGET_YEAR}*.grib")
    files = glob.glob(pattern)
    
    if not files:
        print(f"    Warning: No files found for {var_prefix}")
        return None

    # 2. Load and Filter individually (Iterative approach to save RAM)
    datasets = []
    for f in files:
        try:
            # Load lazily
            ds = xr.open_dataset(f, engine='cfgrib', chunks={'time': 24})
            
            # PRE-FILTER TIME (Crucial for RAM)
            # We must handle cases where the file doesn't cover the target range
            try:
                ds = ds.sel(time=slice(START_DATE, END_DATE))
                ds = ds.sel(time=ds.time.dt.hour.isin(TARGET_HOURS))
            except:
                # If file contains no relevant dates, skip it
                ds.close()
                continue
            
            if ds.time.size > 0:
                datasets.append(ds)
            else:
                ds.close()
                
        except Exception as e:
            print(f"    Skipping {f}: {e}")

    if not datasets:
        return None

    # 3. Merge files for this specific variable
    # (e.g., merge 100-300hPa with 500-700hPa)
    print(f"    Merging {len(datasets)} file chunks...")
    combined = xr.merge(datasets)
    
    # Sort just in case
    if 'isobaricInhPa' in combined.coords:
        combined = combined.sortby('isobaricInhPa')
    combined = combined.sortby('time')

    # 4. Save to Intermediate File
    print(f"    Saving temp file: {output_temp_name}...")
    encoding = {v: {'zlib': True, 'complevel': 1, 'dtype': 'float32'} for v in combined.data_vars}
    combined.to_netcdf(output_temp_name, encoding=encoding)
    
    # 5. Cleanup
    combined.close()
    del combined
    del datasets
    gc.collect() # Force RAM release
    
    return output_temp_name

def main():
    # Cleanup old run
    if os.path.exists(FINAL_CACHE_FILE):
        os.remove(FINAL_CACHE_FILE)

    temp_files = []

    # --- Step 1: Process each variable separately ---
    # 3D Variables
    temp_files.append(process_and_save_variable('era5_q', 'temp_q.nc'))
    temp_files.append(process_and_save_variable('era5_t', 'temp_t.nc'))
    temp_files.append(process_and_save_variable('era5_u', 'temp_u.nc'))
    temp_files.append(process_and_save_variable('era5_v', 'temp_v.nc'))
    
    # Surface Variables (Usually one file group)
    # We treat surface vars as one group since they are usually small
    temp_files.append(process_and_save_variable('era5_*10m', 'temp_sfc.nc'))
    # Note: 'era5_*10m' pattern might miss sp/d2m/t2m if naming differs. 
    # Let's be explicit for surface files:
    
    print("--> Processing Surface Variables...")
    sfc_patterns = ['d2m', 't2m', 'sp', 'u10m', 'v10m']
    sfc_datasets = []
    
    for p in sfc_patterns:
        # Looking for files like era5_d2m_2023_2024_2025.grib
        f_path = f"era5_{p}_2023_2024_2025.grib"
        if os.path.exists(f_path):
            ds = xr.open_dataset(f_path, engine='cfgrib', chunks={'time': 24})
            ds = ds.sel(time=slice(START_DATE, END_DATE))
            ds = ds.sel(time=ds.time.dt.hour.isin(TARGET_HOURS))
            sfc_datasets.append(ds)
            
    if sfc_datasets:
        ds_sfc = xr.merge(sfc_datasets)
        ds_sfc.to_netcdf('temp_surface_all.nc')
        temp_files.append('temp_surface_all.nc')
        ds_sfc.close()
        del ds_sfc
        gc.collect()

    # --- Step 2: Merge Intermediate Files ---
    print("\n--> Merging all temp files into Final Cache...")
    valid_files = [f for f in temp_files if f is not None and os.path.exists(f)]
    
    if not valid_files:
        print("Error: No valid data found.")
        return

    # Open all temp files simultaneously (lazy loading)
    ds_final = xr.open_mfdataset(valid_files, chunks={'time': 24})
    
    # Save final cache
    # We use a lower compression level to write faster since we just want it done
    encoding = {v: {'zlib': True, 'complevel': 1, 'dtype': 'float32'} for v in ds_final.data_vars}
    ds_final.to_netcdf(FINAL_CACHE_FILE, encoding=encoding)
    
    print(f"\nSUCCESS! Data saved to {FINAL_CACHE_FILE}")
    
    # Optional: Delete temp files
    print("Cleaning up temp files...")
    ds_final.close()
    for f in valid_files:
        os.remove(f)

if __name__ == "__main__":
    main()