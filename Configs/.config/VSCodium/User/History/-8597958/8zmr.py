# src/instability.py
from __future__ import annotations

import numpy as np
import xarray as xr

from metpy.units import units
import metpy.calc as mpcalc


# -----------------------------------------------------------------------------
# Helper: robust scalar extraction from MetPy quantities (handles masked values)
# -----------------------------------------------------------------------------
def _to_float(x, unit: str | None = None) -> float:
    try:
        if hasattr(x, "magnitude"):
            if unit is not None:
                x = x.to(unit)
            val = x.magnitude
            # MetPy sometimes returns masked quantities
            if np.ma.is_masked(val):
                return float("nan")
            # magnitude can be 0-d array
            return float(np.asarray(val))
    except Exception:
        pass
    return float("nan")


# -----------------------------------------------------------------------------
# Column physics (1D profile) -> scalar outputs
# -----------------------------------------------------------------------------
def _convective_params_column(
    p_hpa: np.ndarray,
    T_k: np.ndarray,
    q_kgkg: np.ndarray,
    parcel: str = "mixed_layer",
) -> tuple[float, float, float, float, float, float]:
    """
    Compute CAPE, CIN, LCL, LFC, EL for ONE vertical column.

    Inputs (1D arrays):
      p_hpa  : pressure levels [hPa]
      T_k    : temperature [K]
      q_kgkg : specific humidity [kg/kg]

    Returns (scalars):
      CAPE [J/kg], CIN [J/kg],
      LCL_P [hPa], LCL_T [K],
      LFC_P [hPa], EL_P [hPa]

    Notes:
    - With sparse pressure levels, CAPE/LFC/EL are approximate.
    - If LFC/EL do not exist, they return NaN.
    """
    m = np.isfinite(p_hpa) & np.isfinite(T_k) & np.isfinite(q_kgkg)
    if m.sum() < 6:
        return (np.nan, np.nan, np.nan, np.nan, np.nan, np.nan)

    p = p_hpa[m] * units.hPa
    T = T_k[m] * units.kelvin
    q = q_kgkg[m] * units("kg/kg")

    # Ensure sorted from high->low pressure (1000 -> 100) for parcel calcs
    order = np.argsort(p.magnitude)[::-1]
    p, T, q = p[order], T[order], q[order]

    # Dewpoint profile from specific humidity
    Td = mpcalc.dewpoint_from_specific_humidity(p, T, q)

    # ---- Choose parcel (p0, T0, Td0) ----
    if parcel == "surface":
        p0, T0, Td0 = p[0], T[0], Td[0]
    elif parcel == "mixed_layer":
        # average over lowest 100 hPa
        p0, T0, Td0 = mpcalc.mixed_layer(p, T, Td, depth=100 * units.hPa)
    elif parcel == "most_unstable":
        p0, T0, Td0 = mpcalc.most_unstable_parcel(p, T, Td, depth=300 * units.hPa)
    else:
        raise ValueError("parcel must be surface | mixed_layer | most_unstable")

    # ---- LCL ----
    lcl_p, lcl_T = mpcalc.lcl(p0, T0, Td0)

    # ---- Parcel temperature profile (needed for CAPE/CIN/LFC/EL) ----
    parcel_prof = mpcalc.parcel_profile(p, T0, Td0)

    # ---- CAPE/CIN ----
    cape, cin = mpcalc.cape_cin(p, T, Td, parcel_prof)

    # ---- LFC/EL (may not exist) ----
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


# -----------------------------------------------------------------------------
# Dask-parallelized grid computation
# -----------------------------------------------------------------------------
def compute_convective_params(
    T: xr.DataArray,
    q: xr.DataArray,
    *,
    pcoord: str = "isobaricInhPa",
    parcel: str = "mixed_layer",
) -> xr.Dataset:
    """
    Compute CAPE/CIN/LCL/LFC/EL over a grid.

    Inputs:
      T, q dims: (time, level, latitude, longitude)
      pcoord: pressure coord name ('isobaricInhPa' or 'level')
      parcel: surface | mixed_layer | most_unstable

    Returns Dataset with vars (time, latitude, longitude):
      CAPE [J/kg]
      CIN  [J/kg]
      LCL_P [hPa]
      LCL_T [K]
      LFC_P [hPa]
      EL_P  [hPa]
    """
    if pcoord not in T.coords:
        raise ValueError(f"Pressure coordinate '{pcoord}' not found in T.coords: {list(T.coords)}")
    if pcoord not in q.coords:
        raise ValueError(f"Pressure coordinate '{pcoord}' not found in q.coords: {list(q.coords)}")

    # Important: apply_ufunc passes the 1D pressure coordinate values for each column
    p = T[pcoord]

    cape, cin, lclp, lclt, lfcp, elp = xr.apply_ufunc(
        _convective_params_column,
        p, T, q,
        input_core_dims=[[pcoord], [pcoord], [pcoord]],
        output_core_dims=[[], [], [], [], [], []],
        vectorize=True,
        dask="parallelized",
        output_dtypes=[np.float32, np.float32, np.float32, np.float32, np.float32, np.float32],
        kwargs={"parcel": parcel},
    )

    ds = xr.Dataset(
        data_vars={
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
# Classic instability indices (fast, level-based)
# -----------------------------------------------------------------------------
def compute_classic_indices(T: xr.DataArray, q: xr.DataArray, *, pcoord: str = "isobaricInhPa") -> xr.Dataset:
    """
    Computes TT, KI, LI using available levels (850/700/500).
    Requires those levels exist in T and q.
    """
    # Select levels
    T850 = T.sel({pcoord: 850})
    T700 = T.sel({pcoord: 700})
    T500 = T.sel({pcoord: 500})

    q850 = q.sel({pcoord: 850})
    q700 = q.sel({pcoord: 700})

    # Dewpoint at fixed levels from q
    Td850 = xr.apply_ufunc(
        lambda T_k, q_kgkg: mpcalc.dewpoint_from_specific_humidity(
            850 * units.hPa, T_k * units.kelvin, q_kgkg * units("kg/kg")
        ).magnitude,
        T850, q850,
        dask="parallelized",
        vectorize=True,
        output_dtypes=[np.float32],
    )
    Td700 = xr.apply_ufunc(
        lambda T_k, q_kgkg: mpcalc.dewpoint_from_specific_humidity(
            700 * units.hPa, T_k * units.kelvin, q_kgkg * units("kg/kg")
        ).magnitude,
        T700, q700,
        dask="parallelized",
        vectorize=True,
        output_dtypes=[np.float32],
    )

    # Total Totals (approx, in K)
    TT = (T850 + Td850 - 2.0 * T500).rename("TT").assign_attrs(units="K", long_name="Total Totals Index (approx)")

    # K Index (approx, in K)
    KI = ((T850 - T500) + Td850 - (T700 - Td700)).rename("KI").assign_attrs(units="K", long_name="K Index (approx)")

    # Lifted Index (very approximate): parcel lifted from 850 to 500
    LI = xr.apply_ufunc(
        lambda T850_k, Td850_k, T500_k: (
            (T500_k * units.kelvin)
            - mpcalc.parcel_profile(
                np.array([850, 500]) * units.hPa,
                T850_k * units.kelvin,
                Td850_k * units.kelvin,
            )[-1]
        ).magnitude,
        T850, Td850, T500,
        vectorize=True,
        dask="parallelized",
        output_dtypes=[np.float32],
    ).rename("LI").assign_attrs(units="K", long_name="Lifted Index (approx)")

    return xr.Dataset(
        {
            "TT": TT.astype("float32"),
            "KI": KI.astype("float32"),
            "LI": LI.astype("float32"),
        }
    )
