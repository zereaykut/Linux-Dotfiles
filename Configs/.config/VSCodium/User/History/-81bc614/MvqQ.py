# src/zarr_build.py
from __future__ import annotations

from pathlib import Path
from typing import Dict, Optional, Sequence

import numpy as np
import xarray as xr


def standardize_coords(ds: xr.Dataset) -> xr.Dataset:
    rename = {}
    if "lat" in ds.coords and "latitude" not in ds.coords:
        rename["lat"] = "latitude"
    if "lon" in ds.coords and "longitude" not in ds.coords:
        rename["lon"] = "longitude"
    if rename:
        ds = ds.rename(rename)
    return ds


def _open_grib_single(
    path: Path,
    *,
    chunks: Dict[str, int],
    filter_by_keys: Optional[dict] = None,
) -> xr.Dataset:
    backend_kwargs = {"indexpath": "auto"}  # persist cfgrib indexes (faster)
    if filter_by_keys:
        backend_kwargs["filter_by_keys"] = filter_by_keys

    ds = xr.open_dataset(
        str(path),
        engine="cfgrib",
        chunks=chunks,
        backend_kwargs=backend_kwargs,
    )
    return standardize_coords(ds)


def _combine_pressure_level_files(
    paths: Sequence[Path],
    *,
    chunks: Dict[str, int],
    filter_by_keys: Optional[dict] = None,
) -> xr.Dataset:
    """
    Safe combine for multiple pressure-level GRIB files (different level sets).
    Opens each file separately, concatenates along isobaricInhPa, sorts levels,
    drops duplicates, and returns a monotonic coordinate.
    """
    dss = [_open_grib_single(p, chunks=chunks, filter_by_keys=filter_by_keys) for p in paths]

    # Find pressure coordinate name
    pcoord = None
    for cand in ("isobaricInhPa", "level"):
        if cand in dss[0].coords:
            pcoord = cand
            break

    # If not pressure-level data, fallback to by_coords merge
    if pcoord is None:
        return xr.combine_by_coords(dss, combine_attrs="override")

    # Concat along pressure coord
    ds = xr.concat(dss, dim=pcoord, coords="minimal", compat="no_conflicts", combine_attrs="override")

    # Sort pressure coordinate to be monotonic increasing (e.g. 100,200,...1000) or decreasing
    # We'll sort increasing (monotonic). You can reverse later if you prefer.
    ds = ds.sortby(pcoord)

    # Drop duplicate levels if any (can happen if overlapping files exist)
    lev = ds[pcoord].values
    _, idx = np.unique(lev, return_index=True)
    idx_sorted = np.sort(idx)
    ds = ds.isel({pcoord: idx_sorted})

    # Rechunk to embed clean chunks in zarr
    ds = ds.chunk(chunks)
    return ds


def build_zarr(
    *,
    name: str,
    grib_paths: Sequence[str | Path],
    out_zarr: str | Path,
    chunks: Dict[str, int],
    filter_by_keys: Optional[dict] = None,
    subset: Optional[dict] = None,
) -> None:
    """
    One-time GRIB -> Zarr conversion.

    subset example:
      {"latitude": slice(45, 30), "longitude": slice(25, 45)}
    """
    out_zarr = Path(out_zarr)
    out_zarr.parent.mkdir(parents=True, exist_ok=True)

    paths = [Path(p) for p in grib_paths]

    # If multiple files, and they are pressure-level groups, combine safely by concat+sort.
    if len(paths) == 1:
        ds = _open_grib_single(paths[0], chunks=chunks, filter_by_keys=filter_by_keys)
    else:
        ds = _combine_pressure_level_files(paths, chunks=chunks, filter_by_keys=filter_by_keys)

    if subset:
        ds = ds.sel(**subset)

    ds = ds.chunk(chunks)

    print(f"[build_zarr] Writing {name} -> {out_zarr}")
    ds.to_zarr(out_zarr, mode="w")
    print(f"[build_zarr] Done: {out_zarr}")
