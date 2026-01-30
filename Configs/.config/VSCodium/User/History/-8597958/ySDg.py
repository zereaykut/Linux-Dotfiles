# src/instability.py
from __future__ import annotations

import numpy as np
import xarray as xr

import metpy.calc as mpcalc
from metpy.units import units


# -----------------------------------------------------------------------------
# Small helpers (TOP-LEVEL -> picklable for dask.distributed)
# -----------------------------------------------------------------------------
def _to_float(x, unit: str | None = None) -> float:
    try:
        if hasattr(x, "magnitude"):
            if unit is not None:
                x = x.to(unit)
            val = x.magnitude
            if np.ma.is_masked(val):
                return float("nan")
            return float(np.asarray(val))
    except Exception:
        pass
    return float("nan")


def _has_level(da: xr.DataArray, pcoord: str, level: float | int) -> bool:
    if pcoord not in da.coords:
        return False
    vals = np.asarray(da[pcoord].values).astype(float)
    return np.any(np.isclose(vals, float(level)))


def _sel_level(da: xr.DataArray, pcoord: str, level: float | int) -> xr.DataArray:
    # exact selection is fine for ERA5 pressure levels when present
    return da.sel({pcoord: float(level)})


def _dewpoint_from_Tq_fixed_p_hpa(T_k: np.ndarray, q_kgkg: np.ndarray, p_hpa: float) -> np.ndarray:
    """Elementwise Td from (T,q) at fixed pressure. Output in K (float32)."""
    try:
        Td = mpcalc.dewpoint_from_specific_humidity(
            p_hpa * units.hPa,
            T_k * units.kelvin,
            q_kgkg * units("kg/kg"),
        )
        return np.asarray(Td.magnitude, dtype=np.float32)
    except Exception:
        return np.asarray(np.nan, dtype=np.float32)


def _li_from_850_to_500_safe(T850_k: np.ndarray, Td850_k: np.ndarray, T500_k: np.ndarray) -> np.ndarray:
    """
    Robust LI approximation without mpcalc.parcel_profile (avoids MetPy dimension bug
    under vectorized xr.apply_ufunc).
    Steps:
      1) LCL from 850 hPa
      2) Lift moist-adiabatically from LCL to 500 hPa using moist_lapse
      3) LI = Tenv(500) - Tparcel(500)
    Returns K (float32).
    """
    try:
        p850 = 850.0 * units.hPa
        T850 = T850_k * units.kelvin
        Td850 = Td850_k * units.kelvin

        lcl_p, lcl_T = mpcalc.lcl(p850, T850, Td850)

        # Lift from LCL pressure down to 500 hPa
        # moist_lapse expects pressure array with decreasing pressure
        p_path = np.array([float(lcl_p.magnitude), 500.0]) * units.hPa
        Tparcel_500 = mpcalc.moist_lapse(p_path, lcl_T)[-1]

        LI = (T500_k * units.kelvin) - Tparcel_500
        return np.asarray(LI.magnitude, dtype=np.float32)
    except Exception:
        return np.asarray(np.nan, dtype=np.float32)


# -----------------------------------------------------------------------------
# Parcel selection helpers (1D column)
# -----------------------------------------------------------------------------
def _mixed_layer_parcel_from_Tq(
    p: units.Quantity, T: units.Quantity, q: units.Quantity, depth_hpa: float = 100.0
) -> tuple[units.Quantity, units.Quantity, units.Quantity]:
    """
    Returns (p0, T0, Td0) for mixed-layer parcel.
    Assumes p sorted surface->top (high->low pressure).
    """
    p0 = p[0]
    p_top = (p0.magnitude - depth_hpa) * units.hPa
    layer = p >= p_top

    if np.count_nonzero(layer) < 2:
        Td_prof = mpcalc.dewpoint_from_specific_humidity(p, T, q)
        return p0, T[0], Td_prof[0]

    T0 = T[layer].mean()
    q0 = q[layer].mean()
    Td0 = mpcalc.dewpoint_from_specific_humidity(p0, T0, q0)
    return p0, T0, Td0


def _most_unstable_parcel_safe(
    p: units.Quantity, T: units.Quantity, q: units.Quantity, depth_hpa: float = 300.0
) -> tuple[units.Quantity, units.Quantity, units.Quantity]:
    """Try most_unstable_parcel; fallback to surface if sparse/unstable."""
    Td_prof = mpcalc.dewpoint_from_specific_humidity(p, T, q)
    try:
        p0, T0, Td0 = mpcalc.most_unstable_parcel(p, T, Td_prof, depth=depth_hpa * units.hPa)
        return p0, T0, Td0
    except Exception:
        return p[0], T[0], Td_prof[0]


# -----------------------------------------------------------------------------
# Column physics (1D profile) -> scalar outputs (expensive)
# -----------------------------------------------------------------------------
def _convective_params_column(
    p_hpa: np.ndarray,
    T_k: np.ndarray,
    q_kgkg: np.ndarray,
    parcel: str = "mixed_layer",
    compute_lfc_el: bool = True,
) -> tuple[float, float, float, float, float, float]:
    """
    Returns (CAPE, CIN, LCL_P, LCL_T, LFC_P, EL_P).
    If compute_lfc_el=False -> LFC_P and EL_P = NaN (much faster).
    """
    m = np.isfinite(p_hpa) & np.isfinite(T_k) & np.isfinite(q_kgkg)
    if m.sum() < 6:
        return (np.nan, np.nan, np.nan, np.nan, np.nan, np.nan)

    p = p_hpa[m] * units.hPa
    T = T_k[m] * units.kelvin
    q = q_kgkg[m] * units("kg/kg")

    # Sort surface->top (high->low pressure)
    order = np.argsort(p.magnitude)[::-1]
    p, T, q = p[order], T[order], q[order]

    Td_prof = mpcalc.dewpoint_from_specific_humidity(p, T, q)

    # Parcel selection
    if parcel == "surface":
        p0, T0, Td0 = p[0], T[0], Td_prof[0]
    elif parcel == "mixed_layer":
        p0, T0, Td0 = _mixed_layer_parcel_from_Tq(p, T, q, depth_hpa=100.0)
    elif parcel == "most_unstable":
        p0, T0, Td0 = _most_unstable_parcel_safe(p, T, q, depth_hpa=300.0)
    else:
        raise ValueError("parcel must be surface | mixed_layer | most_unstable")

    lcl_p, lcl_T = mpcalc.lcl(p0, T0, Td0)

    # CAPE/CIN require parcel profile
    parcel_prof = mpcalc.parcel_profile(p, T0, Td0)
    cape, cin = mpcalc.cape_cin(p, T, Td_prof, parcel_prof)

    if compute_lfc_el:
        lfc_p, _ = mpcalc.lfc(p, T, Td_prof, parcel_temperature_profile=parcel_prof)
        el_p, _ = mpcalc.el(p, T, Td_prof, parcel_temperature_profile=parcel_prof)
        lfc_val = _to_float(lfc_p, "hPa")
        el_val = _to_float(el_p, "hPa")
    else:
        lfc_val = np.nan
        el_val = np.nan

    return (
        _to_float(cape, "joule / kilogram"),
        _to_float(cin, "joule / kilogram"),
        _to_float(lcl_p, "hPa"),
        _to_float(lcl_T, "kelvin"),
        lfc_val,
        el_val,
    )


def _convective_params_column_masked(
    p_hpa: np.ndarray,
    T_k: np.ndarray,
    q_kgkg: np.ndarray,
    active: np.ndarray,  # scalar 0/1
    parcel: str = "mixed_layer",
    compute_lfc_el: bool = True,
) -> tuple[float, float, float, float, float, float]:
    if not bool(active):
        return (np.nan, np.nan, np.nan, np.nan, np.nan, np.nan)
    return _convective_params_column(
        p_hpa, T_k, q_kgkg, parcel=parcel, compute_lfc_el=compute_lfc_el
    )


# -----------------------------------------------------------------------------
# Public APIs
# -----------------------------------------------------------------------------
def compute_convective_params(
    T: xr.DataArray,
    q: xr.DataArray,
    *,
    pcoord: str = "isobaricInhPa",
    parcel: str = "mixed_layer",
    compute_lfc_el: bool = True,
    mask: xr.DataArray | None = None,
) -> xr.Dataset:
    """
    CAPE/CIN/LCL/LFC/EL over grid (dask-parallelized).

    Speed knobs:
      - mask: compute only where mask==True/1 (HUGE speedup)
      - compute_lfc_el=False: skip LFC/EL (BIG speedup)
      - parcel="surface": fastest, mixed_layer more physical

    IMPORTANT: core dim pcoord must be single chunk.
    """
    if pcoord not in T.coords:
        raise ValueError(f"Pressure coordinate '{pcoord}' not found in T.coords: {list(T.coords)}")
    if pcoord not in q.coords:
        raise ValueError(f"Pressure coordinate '{pcoord}' not found in q.coords: {list(q.coords)}")

    # Core dimension must be single chunk for dask gufunc
    if hasattr(T.data, "chunks"):
        T = T.chunk({pcoord: -1})
    if hasattr(q.data, "chunks"):
        q = q.chunk({pcoord: -1})

    p = T[pcoord]

    if mask is None:
        func = _convective_params_column
        inputs = (p, T, q)
        in_core = [[pcoord], [pcoord], [pcoord]]
    else:
        mask = mask.astype(np.uint8)
        mask, T, q = xr.align(mask, T, q, join="inner")
        func = _convective_params_column_masked
        inputs = (p, T, q, mask)
        in_core = [[pcoord], [pcoord], [pcoord], []]

    cape, cin, lclp, lclt, lfcp, elp = xr.apply_ufunc(
        func,
        *inputs,
        input_core_dims=in_core,
        output_core_dims=[[], [], [], [], [], []],
        vectorize=True,
        dask="parallelized",
        dask_gufunc_kwargs={"allow_rechunk": False},
        output_dtypes=[np.float32, np.float32, np.float32, np.float32, np.float32, np.float32],
        kwargs={"parcel": parcel, "compute_lfc_el": compute_lfc_el},
    )

    ds = xr.Dataset(
        {
            "CAPE": cape.astype("float32"),
            "CIN": cin.astype("float32"),
            "LCL_P": lclp.astype("float32"),
            "LCL_T": lclt.astype("float32"),
            "LFC_P": lfcp.astype("float32"),
            "EL_P": elp.astype("float32"),
        }
    )

    ds["CAPE"].attrs.update(units="J/kg", long_name=f"CAPE ({parcel})")
    ds["CIN"].attrs.update(units="J/kg", long_name=f"CIN ({parcel})")
    ds["LCL_P"].attrs.update(units="hPa", long_name=f"LCL pressure ({parcel})")
    ds["LCL_T"].attrs.update(units="K", long_name=f"LCL temperature ({parcel})")
    ds["LFC_P"].attrs.update(units="hPa", long_name=f"LFC pressure ({parcel})")
    ds["EL_P"].attrs.update(units="hPa", long_name=f"Equilibrium Level pressure ({parcel})")

    return ds


def compute_classic_indices(
    T: xr.DataArray,
    q: xr.DataArray,
    *,
    pcoord: str = "isobaricInhPa",
    mask: xr.DataArray | None = None,
) -> xr.Dataset:
    """
    TT, LI, KI (when possible).
    Robust + dask.distributed-safe (no lambdas).

    mask (optional): if provided, outputs are NaN where mask==False.
    Use this to compute indices only where CAI indicates convection.
    """
    if pcoord not in T.coords:
        raise ValueError(f"'{pcoord}' not in T.coords")
    if pcoord not in q.coords:
        raise ValueError(f"'{pcoord}' not in q.coords")

    ds_out = xr.Dataset()
    notes: list[str] = []

    has_T850 = _has_level(T, pcoord, 850)
    has_T700 = _has_level(T, pcoord, 700)
    has_T500 = _has_level(T, pcoord, 500)
    has_q850 = _has_level(q, pcoord, 850)
    has_q700 = _has_level(q, pcoord, 700)

    Td850 = None
    if has_T850 and has_q850:
        T850 = _sel_level(T, pcoord, 850)
        q850 = _sel_level(q, pcoord, 850)
        Td850 = xr.apply_ufunc(
            _dewpoint_from_Tq_fixed_p_hpa,
            T850,
            q850,
            input_core_dims=[[], []],
            output_core_dims=[[]],
            vectorize=True,
            dask="parallelized",
            output_dtypes=[np.float32],
            kwargs={"p_hpa": 850.0},
        )
    else:
        notes.append("Td850 not computable (need T850 and q850).")

    # TT + LI need T500 and Td850
    if has_T500 and (Td850 is not None):
        T500 = _sel_level(T, pcoord, 500)
        T850 = _sel_level(T, pcoord, 850)

        TT = (T850 + Td850 - 2.0 * T500).rename("TT").astype("float32")
        TT.attrs.update(units="K", long_name="Total Totals Index (approx)")
        ds_out["TT"] = TT

        LI = xr.apply_ufunc(
            _li_from_850_to_500_safe,
            T850,
            Td850,
            T500,
            input_core_dims=[[], [], []],
            output_core_dims=[[]],
            vectorize=True,
            dask="parallelized",
            output_dtypes=[np.float32],
        ).rename("LI").astype("float32")
        LI.attrs.update(units="K", long_name="Lifted Index (robust, parcel from 850 hPa)")
        ds_out["LI"] = LI
    else:
        notes.append("TT/LI skipped (need T500 plus Td850).")

    # KI needs Td700 as well
    if has_T850 and has_T700 and has_T500 and has_q850 and has_q700:
        T850 = _sel_level(T, pcoord, 850)
        T700 = _sel_level(T, pcoord, 700)
        T500 = _sel_level(T, pcoord, 500)

        q850 = _sel_level(q, pcoord, 850)
        q700 = _sel_level(q, pcoord, 700)

        Td850_ = xr.apply_ufunc(
            _dewpoint_from_Tq_fixed_p_hpa,
            T850,
            q850,
            input_core_dims=[[], []],
            output_core_dims=[[]],
            vectorize=True,
            dask="parallelized",
            output_dtypes=[np.float32],
            kwargs={"p_hpa": 850.0},
        )
        Td700 = xr.apply_ufunc(
            _dewpoint_from_Tq_fixed_p_hpa,
            T700,
            q700,
            input_core_dims=[[], []],
            output_core_dims=[[]],
            vectorize=True,
            dask="parallelized",
            output_dtypes=[np.float32],
            kwargs={"p_hpa": 700.0},
        )

        KI = ((T850 - T500) + Td850_ - (T700 - Td700)).rename("KI").astype("float32")
        KI.attrs.update(units="K", long_name="K Index (approx)")
        ds_out["KI"] = KI
    else:
        notes.append("KI skipped (needs T850/T700/T500 and q850/q700).")

    # Apply mask at the end (fast + simple)
    if mask is not None and len(ds_out.data_vars) > 0:
        mask = mask.astype(bool)
        for v in list(ds_out.data_vars):
            m2, vv = xr.align(mask, ds_out[v], join="inner")
            ds_out[v] = vv.where(m2)

    if notes:
        ds_out.attrs["notes"] = " | ".join(notes)

    return ds_out
