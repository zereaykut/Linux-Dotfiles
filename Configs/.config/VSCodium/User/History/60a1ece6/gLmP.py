import xarray as xr
import glob
import os
import gc

# --- Configuration ---
INPUT_DIR = "/home/spidy/Projects/Data/mto/"  # Directory containing your .grib files

CACHE_DIR = "cache"
FINAL_CACHE_FILE = os.path.join(CACHE_DIR, "cache_oct2025.nc")

# Filter Settings
START_DATE = "2025-10-01"
END_DATE = "2025-10-30"
TARGET_HOURS = [0, 6, 12, 18]
TARGET_YEAR = "2025"


def process_and_save_variable(var_prefix, output_temp_path):
    """
    Loads raw GRIBs for ONE variable, filters dates immediately, and saves to a temporary NetCDF.
    This keeps RAM usage controlled.
    """
    print(f"--> Processing {var_prefix}...")

    pattern = os.path.join(INPUT_DIR, f"{var_prefix}*{TARGET_YEAR}*.grib")
    files = sorted(glob.glob(pattern))

    if not files:
        print(f"    Warning: No files found for {var_prefix}")
        return None

    datasets = []
    for f in files:
        try:
            ds = xr.open_dataset(f, engine="cfgrib", chunks={"time": 24})

            # Filter time early
            try:
                ds = ds.sel(time=slice(START_DATE, END_DATE))
                ds = ds.sel(time=ds.time.dt.hour.isin(TARGET_HOURS))
            except Exception:
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

    print(f"    Merging {len(datasets)} file chunks...")
    combined = xr.merge(datasets)

    if "isobaricInhPa" in combined.coords:
        combined = combined.sortby("isobaricInhPa")
    combined = combined.sortby("time")

    print(f"    Saving temp file: {output_temp_path}...")
    encoding = {v: {"zlib": True, "complevel": 1, "dtype": "float32"} for v in combined.data_vars}
    combined.to_netcdf(output_temp_path, encoding=encoding)

    combined.close()
    del combined
    del datasets
    gc.collect()

    return output_temp_path


def main():
    os.makedirs(CACHE_DIR, exist_ok=True)

    # Cleanup old run
    if os.path.exists(FINAL_CACHE_FILE):
        os.remove(FINAL_CACHE_FILE)

    temp_files = []

    # --- Step 1: Process each variable separately ---
    temp_files.append(process_and_save_variable("era5_q", os.path.join(CACHE_DIR, "temp_q.nc")))
    temp_files.append(process_and_save_variable("era5_t", os.path.join(CACHE_DIR, "temp_t.nc")))
    temp_files.append(process_and_save_variable("era5_u", os.path.join(CACHE_DIR, "temp_u.nc")))
    temp_files.append(process_and_save_variable("era5_v", os.path.join(CACHE_DIR, "temp_v.nc")))

    # --- Surface variables: explicit filenames (your list shows these are combined year files) ---
    print("--> Processing Surface Variables (explicit files)...")
    sfc_names = ["d2m", "t2m", "sp", "u10m", "v10m"]
    sfc_datasets = []

    for p in sfc_names:
        f_path = os.path.join(INPUT_DIR, f"era5_{p}_2023_2024_2025.grib")
        if os.path.exists(f_path):
            ds = xr.open_dataset(f_path, engine="cfgrib", chunks={"time": 24})
            ds = ds.sel(time=slice(START_DATE, END_DATE))
            ds = ds.sel(time=ds.time.dt.hour.isin(TARGET_HOURS))
            sfc_datasets.append(ds)
        else:
            print(f"    Warning: missing surface file: {f_path}")

    if sfc_datasets:
        ds_sfc = xr.merge(sfc_datasets)
        sfc_temp = os.path.join(CACHE_DIR, "temp_surface_all.nc")
        ds_sfc.to_netcdf(sfc_temp)
        temp_files.append(sfc_temp)
        ds_sfc.close()
        del ds_sfc
        gc.collect()

    # --- Step 2: Merge Intermediate Files ---
    print("\n--> Merging all temp files into Final Cache...")
    valid_files = [f for f in temp_files if f is not None and os.path.exists(f)]

    if not valid_files:
        print("Error: No valid data found.")
        return

    ds_final = xr.open_mfdataset(valid_files, chunks={"time": 24})

    encoding = {v: {"zlib": True, "complevel": 1, "dtype": "float32"} for v in ds_final.data_vars}
    ds_final.to_netcdf(FINAL_CACHE_FILE, encoding=encoding)

    print(f"\nSUCCESS! Data saved to {FINAL_CACHE_FILE}")

    # Cleanup temps
    print("Cleaning up temp files...")
    ds_final.close()
    for f in valid_files:
        try:
            os.remove(f)
        except Exception:
            pass


if __name__ == "__main__":
    main()
