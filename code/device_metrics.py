# -*- coding: utf-8 -*-
"""Canonical device-metric extraction used by every released analysis.

This module reproduces, exactly, the extractor behind the published device
metrics (Figure 4e and Table S8, and the per-case tables of Supplementary
Table S18d).  It is the single official entry point in this repository; old
copies that implement a different convention are listed in
``docs/REPRODUCE.md`` and must not be used for reported numbers.

Conventions
-----------
Grid
    V = linspace(0, 1.3, 131) V, 0.01 V step.  J in mA cm^-2.

Jsc
    ``|J(V = 0)|``.  Defined whenever the curve is finite, even if no
    open-circuit point exists.

Voc -- downward zero crossing only
    A crossing is counted when ``sign(J[k+1]) < sign(J[k])``, i.e. the current
    goes from positive to zero or from positive to negative.  A purely upward
    change (negative to positive), which occurs on the reverse-bias tail of
    some simulated curves, is **not** an open-circuit crossing and is skipped.

    The zero is located by linear interpolation between the two bracketing
    grid points::

        Voc = V[k] - J[k] * (V[k+1] - V[k]) / (J[k+1] - J[k])

    which is the unique root of the straight line through ``(V[k], J[k])`` and
    ``(V[k+1], J[k+1])``.  It does not rely on the direction of J (the
    argument of ``numpy.interp`` must increase -- here J decreases, so
    ``np.interp`` cannot be used directly).

    * exactly zero at a node (``J[k] == 0``) gives ``Voc = V[k]``;
    * no downward crossing in [0, 1.3] V gives ``Voc = NaN``;
    * a non-finite current anywhere in the curve gives ``NaN`` for every
      metric and sets ``finite = False``;
    * the first crossing is used when several exist.

FF and PCE -- NaN propagation
    ``Pmax`` and ``Vmp`` are the discrete maximum of ``V*J`` over the
    generating quadrant (``V <= Voc`` and ``J >= 0``; ``J >= 0`` only when Voc
    is undefined).  ``FF = Pmax / (Jsc * Voc)`` and ``PCE = Jsc * Voc * FF``
    are computed only when Jsc, Voc, Pmax and FF are finite and positive;
    otherwise they are ``NaN``.  A maximum-power point sitting on the first or
    last node of the generating quadrant sets ``pmax_at_edge = True``
    (a diagnostic, not an exclusion).

Units
    Jsc mA cm^-2, Voc V, FF dimensionless, PCE in percent (mA cm^-2 * V =
    mW cm^-2, which is numerically the same number as a percentage).
"""
import numpy as np

V_GRID = np.linspace(0.0, 1.3, 131)


def first_downward_crossing(J):
    """Index k of the first downward zero crossing, or None.

    A crossing at index k means the sign of J changes between k and k+1 and
    the change is downward (positive -> zero, zero -> negative, or positive ->
    negative).  Ties are impossible here: the sign change is strict.
    """
    J = np.asarray(J, np.float64).ravel()
    s = np.diff(np.sign(J))
    down = np.where(s < 0)[0]
    return int(down[0]) if down.size else None


def linear_zero(k, J, V=V_GRID):
    """Root of the straight line through (V[k], J[k]) and (V[k+1], J[k+1])."""
    j0, j1 = float(J[k]), float(J[k + 1])
    v0, v1 = float(V[k]), float(V[k + 1])
    if j1 == j0:                      # cannot happen for a sign change
        return v0
    return v0 - j0 * (v1 - v0) / (j1 - j0)


def device_metrics(J, V=V_GRID, voc_mode="interp"):
    """Device metrics of one J-V curve.

    Parameters
    ----------
    J : array_like, shape (131,)
        Current density in mA cm^-2 on ``V``.
    V : array_like, optional
        Voltage grid; defaults to the frozen 0-1.3 V, 131-point grid.
    voc_mode : {"interp", "grid"}
        ``"interp"`` (default, the paper convention) uses the linearly
        interpolated downward crossing.  ``"grid"`` returns the first grid node
        with ``J <= 0`` -- kept only to reproduce the legacy store.

    Returns
    -------
    dict with keys Jsc, Voc, Vmp, Pmax, FF, PCE, n_down_cross,
    pmax_at_edge, finite.
    """
    V = np.asarray(V, np.float64).ravel()
    J = np.asarray(J, np.float64).ravel()
    out = dict(Jsc=np.nan, Voc=np.nan, Vmp=np.nan, Pmax=np.nan,
               FF=np.nan, PCE=np.nan, n_down_cross=0,
               pmax_at_edge=False, finite=True)

    if J.size != V.size:
        out["finite"] = False
        out["mismatch_len"] = (J.size, V.size)
        return out
    if not np.all(np.isfinite(J)):
        out["finite"] = False
        return out

    out["Jsc"] = float(abs(J[0]))

    k = first_downward_crossing(J)
    out["n_down_cross"] = int(np.sum(np.diff(np.sign(J)) < 0))
    if k is not None:
        out["Voc"] = (float(linear_zero(k, J, V)) if voc_mode == "interp"
                      else float(V[k + 1]))

    if np.isfinite(out["Voc"]) and out["Voc"] > 0:
        gen = (V <= out["Voc"]) & (J >= 0)
    else:
        gen = J >= 0
    p = np.where(gen, J * V, np.nan)
    if np.isfinite(np.nanmax(p)):
        i = int(np.nanargmax(p))
        out["Pmax"] = float(p[i])
        out["Vmp"] = float(V[i])
        idx = np.where(gen)[0]
        if idx.size and i in (idx[0], idx[-1]):
            out["pmax_at_edge"] = True

    if (np.isfinite(out["Voc"]) and out["Voc"] > 0
            and np.isfinite(out["Jsc"]) and out["Jsc"] > 0
            and np.isfinite(out["Pmax"])):
        out["FF"] = float(out["Pmax"] / (out["Jsc"] * out["Voc"]))

    if (np.isfinite(out["FF"]) and out["FF"] > 0
            and np.isfinite(out["Voc"]) and np.isfinite(out["Jsc"])):
        out["PCE"] = float(out["Jsc"] * out["Voc"] * out["FF"])

    return out


def device_metrics_arrays(J_matrix, V=V_GRID):
    """Vectorised wrapper: dict of four arrays for an (n, 131) stack."""
    res = [device_metrics(j, V) for j in np.asarray(J_matrix)]
    return {k: np.array([r[k] for r in res]) for k in ("Jsc", "Voc", "FF", "PCE")}
