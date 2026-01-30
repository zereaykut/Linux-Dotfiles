# app.py
from __future__ import annotations

from pathlib import Path

import xarray as xr
from dask.distributed import Client, LocalCluster

from src.io_zarr import open_zarr_store, pick_single_var, subset_space_time
from src.cai import compute_cai_base_dask
from src.tracking_numpy import track_from_numpy
from src.plotting import plot_cai_map


CACHE = Path("./cache_zarr")
OUT = Path("./out")
OUT.mkdir(exist_ok=True)


def start_dask():
    cluster = LocalCluster(n_workers=8, threads_per_worker=1)
    return Client(cluster)


def month_range(start: str, end: str):
    """Yield month slices like ('2024-06-01','2024-07-01')"""
    ts = xr.date_range(start, end, freq="MS")
    for i in range(len(ts) - 1):
        yield str(ts[i].date()), str(ts[i + 1].date())


def main():
    client = start_dask()
    print(client)

    chunks = {"time": 96, "latitude": 200, "longitude": 200}

    # ---- Always open via open_zarr() ----
    t2m = pick_single_var(open_zarr_store(CACHE / "t2m.zarr", chunks=chunks))
    d2m = pick_single_var(open_zarr_store(CACHE / "d2m.zarr", chunks=chunks))
    u10 = pick_single_var(open_zarr_store(CACHE / "u10.zarr", chunks=chunks))
    v10 = pick_single_var(open_zarr_store(CACHE / "v10.zarr", chunks=chunks))

    ds_tpl = open_zarr_store(CACHE / "t_pl_low.zarr", chunks=chunks)
    ds_upl = open_zarr_store(CACHE / "u_pl_low.zarr", chunks=chunks)
    ds_vpl = open_zarr_store(CACHE / "v_pl_low.zarr", chunks=chunks)

    t_pl = pick_single_var(ds_tpl)
    u_pl = pick_single_var(ds_upl)
    v_pl = pick_single_var(ds_vpl)

    pcoord = "isobaricInhPa" if "isobaricInhPa" in t_pl.coords else "level"

    # ---- Loop by month: subset time first, compute CAI with dask, compute only subset for tracking ----
    for t0, t1 in month_range("2024-06-01", "2024-09-01"):
        print(f"\n=== Processing {t0} to {t1} ===")

        time_slice = slice(t0, t1)

        # Rule 3: subset time first (space already cropped if you cropped at Zarr build)
        t2m_s = subset_space_time(t2m, time_slice=time_slice)
        d2m_s = subset_space_time(d2m, time_slice=time_slice)
        u10_s = subset_space_time(u10, time_slice=time_slice)
        v10_s = subset_space_time(v10, time_slice=time_slice)

        t850_s = subset_space_time(t_pl.sel({pcoord: 850}), time_slice=time_slice)
        t950_s = subset_space_time(t_pl.sel({pcoord: 950}), time_slice=time_slice)
        u850_s = subset_space_time(u_pl.sel({pcoord: 850}), time_slice=time_slice)
        v850_s = subset_space_time(v_pl.sel({pcoord: 850}), time_slice=time_slice)

        # Align to ensure identical time axis
        t2m_s, d2m_s, u10_s, v10_s, t950_s, t850_s, u850_s, v850_s = xr.align(
            t2m_s, d2m_s, u10_s, v10_s, t950_s, t850_s, u850_s, v850_s, join="inner"
        )

        # Rule 4: compute CAI with dask (still lazy here)
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
        )

        # Save CAI for the month (lazy -> triggers compute during write)
        cai_ds = cai.to_dataset(name="CAI")
        cai_path = OUT / f"cai_{t0}_to_{t1}.zarr"
        cai_ds.to_zarr(cai_path, mode="w")
        print(f"Saved CAI Zarr: {cai_path}")

        # Rule 5: compute only subset period for tracking, then track in NumPy
        cai_np = cai.compute().values  # (time, lat, lon) for this month only
        lat = cai["latitude"].values
        lon = cai["longitude"].values

        tracks = track_from_numpy(
            cai_np,
            lat,
            lon,
            threshold=0.7,
            min_area_cells=9,
            max_km_per_step=80.0,
        )
        print(f"Tracks found: {len(tracks)}")

        # Example plot: mid-month timestep with track overlay
        mid = cai.sizes["time"] // 2
        fig = plot_cai_map(cai.isel(time=mid).compute(), title=f"CAI + Tracks ({t0} to {t1})", tracks=tracks, t_index=mid)
        fig.savefig(OUT / f"cai_tracks_{t0}_to_{t1}.png", dpi=150)

    client.close()


if __name__ == "__main__":
    main()
