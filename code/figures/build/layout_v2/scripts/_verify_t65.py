# -*- coding: utf-8 -*-
"""Adjudicate SI Table T6.5 (compensation directions).

The archived Word prints seven same-sign fractions (0.62 / 0.88 / 0.50 / 0.25 /
0.25 / 0.38 / 0.25) under a caption that names the *closest-1%* tier, whose
archived size is n = 77.  None of those seven values is k/77 for any integer k.
All seven ARE exact multiples of 1/8, so the archived numbers cannot come from
the set the caption names.

This script recomputes the fraction on every candidate pair set and prints the
one that reproduces the archived row set, so the SI edit is decided by
arithmetic and not by assumption.

Read-only on the frozen project.
"""
import os
import sys

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

BASE = r"E:\project\work1"
EXP4 = os.path.join(BASE, "reviewer_experiments", "exp4_collision_metric_robustness")
sys.path.insert(0, os.path.join(EXP4, "scripts"))
import exp4_lib as E4                                     # noqa: E402

import lib_v2 as L                                        # noqa: E402

# the archived Word row order, T6.5
ARCHIVED = [0.62, 0.88, 0.50, 0.25, 0.25, 0.38, 0.25]
SAME_SIGN_PAIRS = [("mu_n_pvk", "mu_p_pvk"), ("tau_n_pvk", "tau_p_pvk"),
                   ("Nc_eff_pvk", "Nv_eff_pvk"), ("tau_n_pvk", "tau_ETL"),
                   ("tau_n_pvk", "tau_HTL"), ("rad_c", "tau_n_pvk"),
                   ("rad_c", "tau_ETL")]


def fractions(P, lo, hi, frac):
    """closest-`frac` tier by dJ, then the same-sign fraction per pair."""
    dJ = np.sqrt(np.mean((P[lo] - P[hi]) ** 2, axis=1)) - \
        np.sqrt(np.mean((P[lo] - P[hi]) ** 2, axis=1))    # placeholder
    return dJ


def same_sign(P, Xn, lo, hi, frac):
    dJ = np.sqrt(np.mean((Xn[lo] - Xn[hi]) ** 2, axis=1))
    order = np.argsort(dJ, kind="stable")
    k = max(1, int(round(lo.size * frac)))
    sel = order[:k]
    d_lo, d_hi = P[lo[sel]], P[hi[sel]]
    out = []
    for a, b in SAME_SIGN_PAIRS:
        ia, ib = L.PARAM_NAMES.index(a), L.PARAM_NAMES.index(b)
        da = d_lo[:, ia] - d_hi[:, ia]
        db = d_lo[:, ib] - d_hi[:, ib]
        v = float(np.mean(np.sign(da) == np.sign(db)))
        out.append((v, int(np.sum(np.sign(da) == np.sign(db))), k))
    return out


def show(tag, res):
    vals = " ".join("%.4f" % v[0] for v in res)
    ks = " ".join("%d/%d" % (v[1], v[2]) for v in res)
    hit = all(abs(v[0] - a) < 0.005 for v, a in zip(res, ARCHIVED))
    print("%-44s %s   %s%s" % (tag, vals, ks,
                               "   <== reproduces the archived Word" if hit
                               else ""))


def main():
    P = E4.P_test()
    Xn = E4.J_test()
    N = P.shape[0]
    nn, _ = E4.nn_for_metric("M1")

    # the derived dJ needs Xn at full 131 columns
    Xn = Xn[:, :131] if Xn.shape[1] > 131 else Xn

    lo_c, hi_c, _ = L.dedup_undirected(nn, N)
    mask = np.arange(N) < nn                       # the archived i < NN(i) rule
    lo_a, hi_a = np.arange(N)[mask], nn[mask]
    o = np.argsort(lo_a * N + hi_a)
    lo_a, hi_a = lo_a[o], hi_a[o]

    print("archived Word T6.5 rows:        %s\n" % " ".join(
        "%.2f" % a for a in ARCHIVED))
    for frac, name in ((0.01, "closest 1%"), (0.005, "closest 0.5%"),
                       (0.001, "closest 0.1%")):
        show("corrected set, %s" % name, same_sign(P, Xn, lo_c, hi_c, frac))
    for frac, name in ((0.01, "closest 1%"), (0.005, "closest 0.5%"),
                       (0.001, "closest 0.1%"), (0.10, "closest 10%")):
        show("ARCHIVED set (i<NN), %s" % name,
             same_sign(P, Xn, lo_a, hi_a, frac))
    print("\narchived set sizes: all %d; tiers %d / %d / %d / %d / %d"
          % (lo_a.size,) + tuple(max(1, int(round(lo_a.size * f)))
                                 for f in (0.10, 0.05, 0.01, 0.005, 0.001)))
    print("corrected set sizes: all %d; tiers %d / %d / %d / %d / %d"
          % (lo_c.size,) + tuple(max(1, int(round(lo_c.size * f)))
                                 for f in (0.10, 0.05, 0.01, 0.005, 0.001)))


if __name__ == "__main__":
    main()
