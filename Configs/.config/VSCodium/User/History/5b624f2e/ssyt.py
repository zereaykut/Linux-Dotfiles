#!/usr/bin/env python3
import xarray as xr
import numpy as np
import os

CACHE_DIR = "cache"
DERIVED_FILE = os.path.join(CACHE_DIR, "derived.nc")
MASK_FILE = os.path.join(CACHE_DIR, "mask.nc")

# Threshold percentiles
P_HIGH = 75   # for CAI, convergence, vorticity
P_LOW  = 25   # for dewpoint depression

# Minimum number of satisfied conditions
MIN_SCORE = 3


def percentile_threshold(da, p):
    """Compute percentile threshold ignoring NaNs."""
    return np.nanpercentile(da.values, p)


def main():
    if not os.path.exists(DERIVED_FILE):
        raise FileNotFoundError(f"Missing {DERIVED_FILE}")

    ds = xr.open_dataset(DERIVED_FILE)

    # Required fields
    required = [
        "CAI",
        "Convergence_mean",
        "Convergence_10m",
        "DD_LowMean_1000_850",
        "Vorticity_mean",
        "Vorticity_10m",
    ]
    for v in required:
        if v not in ds:
            raise ValueError(f"Missing variable: {v}")

    print("Computing adaptive thresholds...")

    thr_cai   = percentile_threshold(ds["CAI"], P_HIGH)
    thr_convM = percentile_threshold(ds["Convergence_mean"], P_HIGH)
    thr_conv10 = percentile_threshold(ds["Convergence_10m"], P_HIGH)
    thr_vortM = percentile_threshold(ds["Vorticity_mean"], P_HIGH)
    thr_vort10 = percentile_threshold(ds["Vorticity_10m"], P_HIGH)
    thr_dd    = percentile_threshold(ds["DD_LowMean_1000_850"], P_LOW)

    print("Building binary condition fields...")

    C1 = (ds["CAI"] >= thr_cai)
    C2 = (ds["Convergence_mean"] >= thr_convM)
    C3 = (ds["Convergence_10m"] >= thr_conv10)

    # NEW: vorticity condition (mean OR 10m)
    C4 = (ds["Vorticity_mean"] >= thr_vortM) | (ds["Vorticity_10m"] >= thr_vort10)

    # Moist boundary layer → low dewpoint depression
    C5 = (ds["DD_LowMean_1000_850"] <= thr_dd)

    print("Computing composite score...")

    score = (
        C1.astype("int8")
        + C2.astype("int8")
        + C3.astype("int8")
        + C4.astype("int8")
        + C5.astype("int8")
    )

    mask = (score >= MIN_SCORE).astype("int8")

    ds_out = xr.Dataset(
        {
            "Mask": mask,
            "Score": score,
        },
        coords={
            "time": ds.time,
            "latitude": ds.latitude,
            "longitude": ds.longitude,
        },
        attrs={
            "description": (
                "Composite cumulus-favorable mask using CAI, "
                "low-level convergence, relative vorticity, "
                "and boundary-layer moisture."
            ),
            "thresholds": (
                f"CAI >= P{P_HIGH}, "
                f"Convergence_mean >= P{P_HIGH}, "
                f"Convergence_10m >= P{P_HIGH}, "
                f"Vorticity_mean or Vorticity_10m >= P{P_HIGH}, "
                f"DD_LowMean_1000_850 <= P{P_LOW}, "
                f"MIN_SCORE={MIN_SCORE}"
            ),
        },
    )

    print(f"Saving mask → {MASK_FILE}")
    ds_out.to_netcdf(MASK_FILE, encoding={"Mask": {"dtype": "int8"}, "Score": {"dtype": "int8"}})


if __name__ == "__main__":
    main()
