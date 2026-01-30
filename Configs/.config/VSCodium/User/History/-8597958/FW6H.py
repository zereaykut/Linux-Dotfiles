# src/instability.py
from __future__ import annotations

import numpy as np
import xarray as xr

import metpy.calc as mpcalc
from metpy.units import units


# -----------------------------------------------------------------------------
# Small helpers (must be TOP-LEVEL to be picklable by dask.distributed)
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
    return da.sel({pcoord: float(level)})


def _dewpoint_from_Tq_fixed_p_hpa(T_k: np.ndarray, q_kgkg: np.ndarray, p_hpa: float) -> np.ndarray:
    """
    Vectorized elementwise dewpoint from (T, q) at fixed pressure.
    Returns dewpoint in K (float32).
    """
    Td = mpcalc.dewpoint_from_specific_humidity(
        p_hpa * units.hPa,
        T_k * units.kelvin,
        q_kgkg * units("kg/kg"),
    )
    return np.asarray(Td.magnitude, dtype=np.float32)


def _li_from_850_to_500(T850_k: np.ndarray, Td850_k: np.ndarray, T500_k: np.ndarray) -> np.ndarray:
    """
    Lifted Index approx: LI = T_env(500) - T_parcel(500), parcel from 850.
    Returns K (float32).
    """
    prof = mpcalc.parcel_profile(
        np.array([850.0, 500.0]) * units.hPa,
        T850_k * units.kelvin,
        Td850_k * units.kelvin,
    )
    Tparcel_500 = prof[-1]
    LI = (T500_k * units.kelvin) - Tparcel_500
    return np.asarray(LI.magnitude, dtype=np.float32)


# -----------------------------------------------------------------------------
# Column physics (1D profile) -> scalar outputs
# -----------------------------------------------------------------------------
def _convective_params_column(
    p_hpa: np.ndarray,
    T_k: np.ndarray,
    q_kgkg: np.ndarray,
    parcel: str = "mixed_layer",
) -> tuple[float, float, float, float, float, float]:
    m = np.isfinite(p_hpa) & np.isfinite(T_k) & np.isfinite(q_kgkg)
    if m.sum() < 6:
        return (np.nan, np.nan, np.nan, np.nan, np.nan, np.nan)

    p = p_hpa[m] * units.hPa
    T = T_k[m] * units.kelvin
    q = q_kgkg[m] * units("kg/kg")

    # Sort high->low pressure (1000 -> 100)
    order = np.argsort(p.magnitude)[::-1]
    p, T, q = p[order], T[order], q[order]

    Td = mpcalc.dewpoint_from_specific_humidity(p, T, q)

    if parcel == "surface":
        p0, T0, Td0 = p[0], T[0], Td[0]
    elif parcel == "mixed_layer":
        p0, T0, Td0 = mpcalc.mixed_layer(p, T, Td, depth=100 * units.hPa)
    elif parcel == "most_unstable":
        p0, T0, Td0 = mpcalc.most_unstable_parcel(p, T, Td, depth=300 * units.hPa)
    else:
        raise ValueError("parcel must be surface | mixed_layer | most_unstable")

    lcl_p, lcl_T = mpcalc.lcl(p0, T0, Td0)
    parcel_prof = mpcalc.parcel_profile(p, T0, Td0)

    cape, cin = mpcalc.cape_cin(p, T, Td, parcel_prof)

    lfc_p, _ = mpcalc.lfc(p, T, Td, parcel_temperature_profile=parcel_prof)
    el_p, _ = mpcalc.el(p, T, Td, parcel_temperature_profile=parcel_prof)

    return (
        _to_float(cape, "joule / kilogram"),
        _to_float(cin, "joule / kilogram"),
        _to_float(lcl_p, "hPa"),
        _to_float(lcl_T, "kelvin"),
        _to_float(lfc_p, "hPa"),
        _to_float(el_p, "hPa"),
    )


def compute_convective_params(
    T: xr.DataArray,
    q: xr.DataArray,
    *,
    pcoord: str = "isobaricInhPa",
    parcel: str = "mixed_layer",
) -> xr.Dataset:
    """
    CAPE/CIN/LCL/LFC/EL over grid (dask-parallelized).
    Core dim pcoord must be single chunk -> enforced here.
    """
    if pcoord not in T.coords:
        raise ValueError(f"Pressure coordinate '{pcoord}' not found in T.coords: {list(T.coords)}")
    if pcoord not in q.coords:
        raise ValueError(f"Pressure coordinate '{pcoord}' not found in q.coords: {list(q.coords)}")

    # Core dimension must be single chunk for dask='parallelized'
    if hasattr(T.data, "chunks"):
        T = T.chunk({pcoord: -1})
    if hasattr(q.data, "chunks"):
        q = q.chunk({pcoord: -1})

    p = T[pcoord]

    cape, cin, lclp, lclt, lfcp, elp = xr.apply_ufunc(
        _convective_params_column,
        p, T, q,
        input_core_dims=[[pcoord], [pcoord], [pcoord]],
        output_core_dims=[[], [], [], [], [], []],
        vectorize=True,
        dask="parallelized",
        dask_gufunc_kwargs={"allow_rechunk": False},
        output_dtypes=[np.float32, np.float32, np.float32, np.float32, np.float32, np.float32],
        kwargs={"parcel": parcel},
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


# -----------------------------------------------------------------------------
# Classic indices (no lambdas -> dask.distributed-safe)
# -----------------------------------------------------------------------------
def compute_classic_indices(
    T: xr.DataArray,
    q: xr.DataArray,
    *,
    pcoord: str = "isobaricInhPa",
) -> xr.Dataset:
    """
    Computes TT, KI, LI when possible with available levels.
    Dask-distributed safe: NO lambdas inside apply_ufunc.
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

    # ---- Td850 ----
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

    # ---- TT: T850 + Td850 - 2*T500 ----
    if has_T500 and (Td850 is not None):
        T500 = _sel_level(T, pcoord, 500)
        T850 = _sel_level(T, pcoord, 850)
        TT = (T850 + Td850 - 2.0 * T500).rename("TT").astype("float32")
        TT.attrs.update(units="K", long_name="Total Totals Index (approx)")
        ds_out["TT"] = TT
    else:
        notes.append("TT skipped (need T500 plus Td850).")

    # ---- LI: parcel from 850 to 500 ----
    if has_T500 and (Td850 is not None):
        T500 = _sel_level(T, pcoord, 500)
        T850 = _sel_level(T, pcoord, 850)
        LI = xr.apply_ufunc(
            _li_from_850_to_500,
            T850,
            Td850,
            T500,
            input_core_dims=[[], [], []],
            output_core_dims=[[]],
            vectorize=True,
            dask="parallelized",
            output_dtypes=[np.float32],
        ).rename("LI").astype("float32")
        LI.attrs.update(units="K", long_name="Lifted Index (approx, parcel from 850 hPa)")
        ds_out["LI"] = LI
    else:
        notes.append("LI skipped (need T500 plus Td850).")

    # ---- KI: (T850 - T500) + Td850 - (T700 - Td700) ----
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

    if notes:
        ds_out.attrs["notes"] = " | ".join(notes)

    return ds_out
