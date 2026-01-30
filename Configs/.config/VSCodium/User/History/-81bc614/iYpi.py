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
    backend_kwargs = {"indexpath": "auto"}  # persistent cfgrib indexes
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
    Opens each file separately, concatenates along isobaricInhPa/level, sorts levels,
    drops duplicates, returns a monotonic coordinate, and enforces single chunk on pcoord.
    """
    dss = [_open_grib_single(p, chunks=chunks, filter_by_keys=filter_by_keys) for p in paths]

    # Find pressure coordinate name
    pcoord = None
    for cand in ("isobaricInhPa", "level"):
        if cand in dss[0].coords:
            pcoord = cand
            break

    # If not pressure-level data, fallback
    if pcoord is None:
        return xr.combine_by_coords(dss, combine_attrs="override")

    # Concat along pressure coord
    ds = xr.concat(
        dss,
        dim=pcoord,
        coords="minimal",
        compat="no_conflicts",
        combine_attrs="override",
    )

    # Sort pressure coordinate monotonic increasing
    ds = ds.sortby(pcoord)

    # Drop duplicate levels if any
    lev = np.asarray(ds[pcoord].values).astype(float)
    _, idx = np.unique(lev, return_index=True)
    ds = ds.isel({pcoord: np.sort(idx)})

    # IMPORTANT: pcoord must be a single chunk for dask gufunc core-dim usage
    chunks_pl = dict(chunks)
    chunks_pl[pcoord] = -1
    ds = ds.chunk(chunks_pl)

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
    """
    out_zarr = Path(out_zarr)
    out_zarr.parent.mkdir(parents=True, exist_ok=True)

    paths = [Path(p) for p in grib_paths]

    if len(paths) == 1:
        ds = _open_grib_single(paths[0], chunks=chunks, filter_by_keys=filter_by_keys)
    else:
        ds = _combine_pressure_level_files(paths, chunks=chunks, filter_by_keys=filter_by_keys)

    if subset:
        ds = ds.sel(**subset)

    # If pressure coord exists, enforce single chunk there too (covers single-file PL case)
    pcoord = "isobaricInhPa" if "isobaricInhPa" in ds.coords else ("level" if "level" in ds.coords else None)
    if pcoord is not None:
        chunks_pl = dict(chunks)
        chunks_pl[pcoord] = -1
        ds = ds.chunk(chunks_pl)
    else:
        ds = ds.chunk(chunks)

    print(f"[build_zarr] Writing {name} -> {out_zarr}")
    ds.to_zarr(out_zarr, mode="w")
    print(f"[build_zarr] Done: {out_zarr}")
