# app.py
from __future__ import annotations

from pathlib import Path

import xarray as xr
from dask.distributed import Client, LocalCluster

from src.io_zarr import open_zarr_store, pick_single_var, subset_space_time
from src.cai import compute_cai_base_dask
from src.instability import compute_convective_params, compute_classic_indices
from src.tracking_numpy import track_from_numpy
from src.plotting import plot_cai_map


CACHE = Path("./cache_zarr")
OUT = Path("./out")
OUT.mkdir(exist_ok=True)


def start_dask():
    cluster = LocalCluster(n_workers=8, threads_per_worker=1)
    return Client(cluster)


def month_range(start: str, end: str):
    ts = xr.date_range(start, end, freq="MS")
    for i in range(len(ts) - 1):
        yield str(ts[i].date()), str(ts[i + 1].date())


def _year_from_datestr(s: str) -> int:
    return int(s.split("-")[0])


def open_yearly_pl(year: int, var: str, *, chunks):
    if var == "t_pl":
        return pick_single_var(open_zarr_store(CACHE / f"t_pl_{year}.zarr", chunks=chunks))
    if var == "q_pl":
        return pick_single_var(open_zarr_store(CACHE / f"q_pl_{year}.zarr", chunks=chunks))
    if var == "u_pl_low":
        return pick_single_var(open_zarr_store(CACHE / f"u_pl_low_{year}.zarr", chunks=chunks))
    if var == "v_pl_low":
        return pick_single_var(open_zarr_store(CACHE / f"v_pl_low_{year}.zarr", chunks=chunks))
    raise ValueError(f"Unknown var: {var}")


def main():
    client = start_dask()
    print(client)

    # Base chunks for lat/lon/time
    base_chunks = {"time": 96, "latitude": 200, "longitude": 200}

    # Surface stores (all years)
    t2m = pick_single_var(open_zarr_store(CACHE / "t2m.zarr", chunks=base_chunks))
    d2m = pick_single_var(open_zarr_store(CACHE / "d2m.zarr", chunks=base_chunks))
    u10 = pick_single_var(open_zarr_store(CACHE / "u10.zarr", chunks=base_chunks))
    v10 = pick_single_var(open_zarr_store(CACHE / "v10.zarr", chunks=base_chunks))

    for t0, t1 in month_range("2023-01-01", "2026-01-01"):
        year = _year_from_datestr(t0)
        print(f"\n=== Processing {t0} to {t1} (year={year}) ===")
        time_slice = slice(t0, t1)

        # ---- subset surface first ----
        t2m_s = subset_space_time(t2m, time_slice=time_slice)
        d2m_s = subset_space_time(d2m, time_slice=time_slice)
        u10_s = subset_space_time(u10, time_slice=time_slice)
        v10_s = subset_space_time(v10, time_slice=time_slice)

        # ---- open correct year pressure-level stores ----
        # Open PL stores with pcoord in a single chunk (critical for apply_ufunc core-dim)
        # zarr_build.py writes pcoord as single chunk, but we also keep it safe at read time.
        Tpl = open_yearly_pl(year, "t_pl", chunks={**base_chunks, "isobaricInhPa": -1, "level": -1})
        qpl = open_yearly_pl(year, "q_pl", chunks={**base_chunks, "isobaricInhPa": -1, "level": -1})
        upl = open_yearly_pl(year, "u_pl_low", chunks={**base_chunks, "isobaricInhPa": -1, "level": -1})
        vpl = open_yearly_pl(year, "v_pl_low", chunks={**base_chunks, "isobaricInhPa": -1, "level": -1})

        pcoord = "isobaricInhPa" if "isobaricInhPa" in Tpl.coords else "level"

        # ---- subset pressure-level data first ----
        Tpl_s = subset_space_time(Tpl, time_slice=time_slice)
        qpl_s = subset_space_time(qpl, time_slice=time_slice)
        upl_s = subset_space_time(upl, time_slice=time_slice)
        vpl_s = subset_space_time(vpl, time_slice=time_slice)

        # CAI needs low-level temperature + 850 winds
        t850_s = Tpl_s.sel({pcoord: 850})
        t950_s = Tpl_s.sel({pcoord: 950})
        u850_s = upl_s.sel({pcoord: 850})
        v850_s = vpl_s.sel({pcoord: 850})

        # Align on common time grid
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

        # =========================
        # 1) CAI (dask)
        # =========================
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
        ).chunk(base_chunks)

        cai_path = OUT / f"cai_{t0}_to_{t1}.zarr"
        cai.to_dataset(name="CAI").to_zarr(cai_path, mode="w")
        print(f"Saved CAI: {cai_path}")

        # =========================
        # 2) Instability outputs (dask)
        # With q now including 700 hPa, KI becomes computable.
        # =========================
        ds_conv = compute_convective_params(Tpl_s, qpl_s, pcoord=pcoord, parcel="mixed_layer")
        ds_idx = compute_classic_indices(Tpl_s, qpl_s, pcoord=pcoord)

        ds_instab = xr.merge([ds_conv, ds_idx]).chunk(base_chunks)

        instab_path = OUT / f"instability_{t0}_to_{t1}.zarr"
        ds_instab.to_zarr(instab_path, mode="w")
        print(f"Saved instability outputs: {instab_path}")

        # =========================
        # 3) Tracking (compute only this month -> NumPy)
        # =========================
        cai_np = cai.compute().values
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
