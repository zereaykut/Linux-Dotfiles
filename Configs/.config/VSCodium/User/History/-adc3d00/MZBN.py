# app.py
from __future__ import annotations

from pathlib import Path

import numpy as np
import xarray as xr
import dask
from dask.distributed import Client, LocalCluster

from src.io_zarr import open_zarr_store, pick_single_var, subset_space_time
from src.cai import compute_cai_base_dask
from src.instability import compute_convective_params, compute_classic_indices
from src.tracking_numpy import track_from_numpy
from src.plotting import plot_cai_map


# -----------------------------------------------------------------------------
# Paths
# -----------------------------------------------------------------------------
CACHE = Path("./cache_zarr")
OUT = Path("./out")
OUT.mkdir(exist_ok=True, parents=True)


# -----------------------------------------------------------------------------
# Performance knobs (tune these first)
# -----------------------------------------------------------------------------
CAI_MASK_THRESHOLD = 0.70        # mask threshold for instability
CAI_TRACK_THRESHOLD = 0.70       # threshold for tracking
MASK_DILATE_STEPS = 1            # 0–2. Expands mask to capture edges

INSTABILITY_TIME_STRIDE = 3      # 1 hourly, 3=3-hourly, 6=6-hourly (big speed)
INSTABILITY_SPATIAL_STRIDE = 2   # 1 full res, 2 every 2nd grid point (big speed)

COMPUTE_LFC_EL = False           # huge speed win; keep False unless you truly need LFC/EL
PARCEL_MODE = "mixed_layer"      # "surface" faster; "mixed_layer" more physical

BASE_CHUNKS = {"time": 96, "latitude": 200, "longitude": 200}

# Optional crop (recommended)
SUBSET = {"latitude": slice(45, 30), "longitude": slice(25, 45)}  # Turkey-ish
# SUBSET = None


# -----------------------------------------------------------------------------
# Dask setup
# -----------------------------------------------------------------------------
def start_dask() -> Client:
    cluster = LocalCluster(
        n_workers=8,
        threads_per_worker=1,     # MetPy is python-heavy; 1 thread often best
        processes=True,
        memory_limit="auto",
        dashboard_address=":8787",
    )
    client = Client(cluster)

    dask.config.set(
        {
            "distributed.worker.memory.target": 0.85,
            "distributed.worker.memory.spill": 0.90,
            "distributed.worker.memory.pause": 0.95,
            "distributed.worker.memory.terminate": 0.98,
        }
    )
    return client


# -----------------------------------------------------------------------------
# Helpers
# -----------------------------------------------------------------------------
def month_range(start: str, end: str):
    ts = xr.date_range(start, end, freq="MS")
    for i in range(len(ts) - 1):
        yield str(ts[i].date()), str(ts[i + 1].date())


def _year_from_datestr(s: str) -> int:
    return int(s.split("-")[0])


def _maybe_subset(da: xr.DataArray) -> xr.DataArray:
    return da.sel(**SUBSET) if SUBSET else da


def _mask_dilate_2d(mask: xr.DataArray, steps: int = 1) -> xr.DataArray:
    """Cheap dilation without scipy."""
    if steps <= 0:
        return mask
    out = mask
    for _ in range(steps):
        out = (
            out
            | out.shift(latitude=1, fill_value=False)
            | out.shift(latitude=-1, fill_value=False)
            | out.shift(longitude=1, fill_value=False)
            | out.shift(longitude=-1, fill_value=False)
        )
    return out


def open_yearly_pl(year: int, name: str, *, chunks):
    if name == "t_pl":
        return pick_single_var(open_zarr_store(CACHE / f"t_pl_{year}.zarr", chunks=chunks))
    if name == "q_pl":
        return pick_single_var(open_zarr_store(CACHE / f"q_pl_{year}.zarr", chunks=chunks))
    if name == "u_pl_low":
        return pick_single_var(open_zarr_store(CACHE / f"u_pl_low_{year}.zarr", chunks=chunks))
    if name == "v_pl_low":
        return pick_single_var(open_zarr_store(CACHE / f"v_pl_low_{year}.zarr", chunks=chunks))
    raise ValueError(f"Unknown yearly PL store: {name}")


# -----------------------------------------------------------------------------
# Main
# -----------------------------------------------------------------------------
def main():
    client = start_dask()
    print(client)

    # Surface stores (all years)
    t2m = _maybe_subset(pick_single_var(open_zarr_store(CACHE / "t2m.zarr", chunks=BASE_CHUNKS)))
    d2m = _maybe_subset(pick_single_var(open_zarr_store(CACHE / "d2m.zarr", chunks=BASE_CHUNKS)))
    u10 = _maybe_subset(pick_single_var(open_zarr_store(CACHE / "u10.zarr", chunks=BASE_CHUNKS)))
    v10 = _maybe_subset(pick_single_var(open_zarr_store(CACHE / "v10.zarr", chunks=BASE_CHUNKS)))

    for t0, t1 in month_range("2023-01-01", "2026-01-01"):
        year = _year_from_datestr(t0)
        print(f"\n=== Processing {t0} to {t1} (year={year}) ===")
        time_slice = slice(t0, t1)

        # --- subset surface first ---
        t2m_s = subset_space_time(t2m, time_slice=time_slice)
        d2m_s = subset_space_time(d2m, time_slice=time_slice)
        u10_s = subset_space_time(u10, time_slice=time_slice)
        v10_s = subset_space_time(v10, time_slice=time_slice)

        # --- open pressure-level stores ---
        pl_chunks = {**BASE_CHUNKS, "isobaricInhPa": -1, "level": -1}
        Tpl = _maybe_subset(open_yearly_pl(year, "t_pl", chunks=pl_chunks))
        qpl = _maybe_subset(open_yearly_pl(year, "q_pl", chunks=pl_chunks))
        upl = _maybe_subset(open_yearly_pl(year, "u_pl_low", chunks=pl_chunks))
        vpl = _maybe_subset(open_yearly_pl(year, "v_pl_low", chunks=pl_chunks))

        pcoord = "isobaricInhPa" if "isobaricInhPa" in Tpl.coords else "level"

        # --- subset PL first ---
        Tpl_s = subset_space_time(Tpl, time_slice=time_slice)
        qpl_s = subset_space_time(qpl, time_slice=time_slice)
        upl_s = subset_space_time(upl, time_slice=time_slice)
        vpl_s = subset_space_time(vpl, time_slice=time_slice)

        # CAI needs these:
        t850_s = Tpl_s.sel({pcoord: 850})
        t950_s = Tpl_s.sel({pcoord: 950})
        u850_s = upl_s.sel({pcoord: 850})
        v850_s = vpl_s.sel({pcoord: 850})

        # Align all
        t2m_s, d2m_s, u10_s, v10_s, Tpl_s, qpl_s, t950_s, t850_s, u850_s, v850_s = xr.align(
            t2m_s,
            d2m_s,
            u10_s,
            v10_s,
            Tpl_s,
            qpl_s,
            t950_s,
            t850_s,
            u850_s,
            v850_s,
            join="inner",
        )

        # ==========================================================
        # 1) CAI (keep full-res + full-time)
        # ==========================================================
        cai = compute_cai_base_dask(
            t2m=t2m_s,
            d2m=d2m_s,
            u10=u10_s,
            v10=v10_s,
            t950=t950_s,
            t850=t850_s,
            u850=u850_s,
            v850=v850_s,
            norm_dim=("time",),
        ).chunk(BASE_CHUNKS)

        cai_path = OUT / f"cai_{t0}_to_{t1}.zarr"
        cai.to_dataset(name="CAI").to_zarr(cai_path, mode="w")
        print(f"Saved CAI: {cai_path}")

        # ==========================================================
        # 2) FAST instability:
        #    - time stride
        #    - spatial stride
        #    - CAI mask (with dilation)
        #    - optionally skip LFC/EL
        # ==========================================================
        # (a) time stride
        if INSTABILITY_TIME_STRIDE > 1:
            Tpl_i = Tpl_s.isel(time=slice(None, None, INSTABILITY_TIME_STRIDE))
            qpl_i = qpl_s.isel(time=slice(None, None, INSTABILITY_TIME_STRIDE))
            cai_i = cai.isel(time=slice(None, None, INSTABILITY_TIME_STRIDE))
        else:
            Tpl_i, qpl_i, cai_i = Tpl_s, qpl_s, cai

        # (b) spatial stride
        if INSTABILITY_SPATIAL_STRIDE > 1:
            sl_lat = slice(None, None, INSTABILITY_SPATIAL_STRIDE)
            sl_lon = slice(None, None, INSTABILITY_SPATIAL_STRIDE)
            Tpl_i = Tpl_i.isel(latitude=sl_lat, longitude=sl_lon)
            qpl_i = qpl_i.isel(latitude=sl_lat, longitude=sl_lon)
            cai_i = cai_i.isel(latitude=sl_lat, longitude=sl_lon)

        # (c) CAI mask
        mask_i = (cai_i > CAI_MASK_THRESHOLD)
        mask_i = _mask_dilate_2d(mask_i, steps=MASK_DILATE_STEPS)

        # Align again
        mask_i, Tpl_i, qpl_i = xr.align(mask_i, Tpl_i, qpl_i, join="inner")

        # Convective params (expensive) -> masked
        ds_conv = compute_convective_params(
            Tpl_i,
            qpl_i,
            pcoord=pcoord,
            parcel=PARCEL_MODE,
            compute_lfc_el=COMPUTE_LFC_EL,
            mask=mask_i,
        )

        # Classic indices -> compute only where mask is true
        ds_idx = compute_classic_indices(Tpl_i, qpl_i, pcoord=pcoord, mask=mask_i)

        ds_instab = xr.merge([ds_conv, ds_idx])

        instab_path = OUT / f"instability_fast_{t0}_to_{t1}.zarr"
        ds_instab.to_zarr(instab_path, mode="w")
        print(f"Saved instability outputs: {instab_path}")

        # ==========================================================
        # 3) Tracking (NumPy only for this month)
        # ==========================================================
        cai_np = cai.compute().values
        lat = cai["latitude"].values
        lon = cai["longitude"].values

        tracks = track_from_numpy(
            cai_np,
            lat,
            lon,
            threshold=CAI_TRACK_THRESHOLD,
            min_area_cells=9,
            max_km_per_step=80.0,
        )
        print(f"Tracks found: {len(tracks)}")

        mid = cai.sizes["time"] // 2
        fig = plot_cai_map(
            cai.isel(time=mid).compute(),
            title=f"CAI + Tracks ({t0} to {t1})",
            tracks=tracks,
            t_index=mid,
        )
        fig.savefig(OUT / f"cai_tracks_{t0}_to_{t1}.png", dpi=150)

    client.close()


if __name__ == "__main__":
    main()
