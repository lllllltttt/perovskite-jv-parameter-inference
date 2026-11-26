# -*- coding: utf-8 -*-
"""
_verify_review_findings.py — independently check each finding in the review
===========================================================================
Read-only. Checks, from frozen sources, the four claims the review makes:

  F1  fig3_sketch.py panel (d) applies log10 a SECOND time
      (np.log10(L[i,q]/L[j,q]) where L is already log10), and the resulting
      values are not |log10(theta_i/theta_j)|.
  F2  panel (d)'s bar values run parameter 0..8 while its tick labels run
      8..0, so every label sits against the wrong parameter.
  F3  fig3_pair_analysis.py's distribution preview truncates at 2.0 and
      re-normalises the density; report the true share of values above 2.
  F4  the tier subsets are not disjoint sample sets; report pairs, distinct
      samples and repeated samples per tier.

Prints only. Writes nothing.
"""
import os
import sys
import pickle

import numpy as np
import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
BASE = r"E:\project\work1"
DATA_NPZ = os.path.join(BASE, "data", "dataset_normalized.npz")
SCALER_PKL = os.path.join(BASE, "data", "param_scaler.pkl")
PAIRS_CSV = os.path.join(
    BASE, "20261006", "figure_revision_phase1", "source_data",
    "fig3_pairs_new.csv")
RAND_CSV = os.path.join(
    BASE, "20261006", "figure_revision_phase1", "source_data",
    "fig3_random_baseline.csv")

PARAM_NAMES = ["mu_n_pvk", "mu_p_pvk", "tau_n_pvk", "tau_p_pvk",
               "Nc_eff_pvk", "Nv_eff_pvk", "tau_ETL", "tau_HTL", "rad_c"]


def main():
    d = np.load(DATA_NPZ)
    with open(SCALER_PKL, "rb") as fh:
        sc = pickle.load(fh)["scaler"]
    RAW = d["params_test_raw"].astype(np.float64)      # physical parameters
    L = np.log10(RAW)                                  # physical log10
    P = pd.read_csv(PAIRS_CSV)
    R = pd.read_csv(RAND_CSV).set_index("coordinate")["median_absd_random"]

    # ---- sanity: L really is log10 of the raw physical parameters ---------
    Lref = d["params_test"].astype(np.float64) * sc.data_range_ + sc.data_min_
    print("[sanity] max|log10(raw) - inverse_scaler(normalized)| = %.3e"
          % np.max(np.abs(L - Lref)))

    # ================================================== F1 + F2 ============
    print("\n" + "=" * 78)
    print("F1/F2  fig3_sketch.py panel (d)")
    print("=" * 78)
    ex = {("A", "mobility"): (2890, 5067), ("B", "lifetime"): (500, 4560)}
    for (tag, which), (i, j) in ex.items():
        buggy = np.array([abs(np.log10(L[i, q] / L[j, q])) for q in range(9)])
        fixed = np.abs(L[i] - L[j])
        print("\n  pair %s  (test index %d, %d)" % (tag, i, j))
        print("  %-12s %14s %14s %14s %10s"
              % ("parameter", "buggy", "fixed", "ratio", "ratio/buggy"))
        for q in range(9):
            ratio = fixed[q] / buggy[q] if buggy[q] else np.nan
            print("  %-12s %14.5f %14.5f %14.5f %10.3f"
                  % (PARAM_NAMES[q], buggy[q], fixed[q], ratio, ratio))
        # how often does the buggy transform even agree in ordering?
        print("  argmax: buggy -> %s | fixed -> %s"
              % (PARAM_NAMES[int(np.argmax(buggy))],
                 PARAM_NAMES[int(np.argmax(fixed))]))
        print("  max buggy = %.5f   max fixed = %.5f"
              % (buggy.max(), fixed.max()))

    # what the buggy value actually equals
    i, j = ex[("A", "mobility")]
    q = 0
    print("\n  what the buggy expression computes for (%d,%d) param %s:" % (i, j, PARAM_NAMES[q]))
    print("     raw values        : %.6g , %.6g" % (RAW[i, q], RAW[j, q]))
    print("     log10 values      : %.6f , %.6f" % (L[i, q], L[j, q]))
    print("     L_i / L_j         : %.6f" % (L[i, q] / L[j, q]))
    print("     log10(L_i / L_j)  = %.6f   <- the buggy value" % buggy[q])
    print("     |L_i - L_j|       = %.6f   <- log10(theta_i/theta_j)" % fixed[q])
    print("     NOTE: log10(L_i/L_j) = log10(L_i) - log10(L_j) is log10 of a")
    print("           ratio OF LOGARITHMS; it is not a log-ratio of parameters.")

    # ---- F2: label mapping actually used in the sketch --------------------
    ks = np.arange(9)[::-1]
    print("\n  F2 label map as written:")
    print("     bar positions ks = %s" % ks.tolist())
    print("     labels drawn    = [PARAM_LABELS[q] for q in ks]")
    for pos, q in enumerate(ks):
        print("       tick %d carries label of param %d (%s) but plots "
              "vals[%d] = param %d (%s)"
              % (ks[pos], q, PARAM_NAMES[q], pos, pos, PARAM_NAMES[pos]))

    # ================================================== F3 ================
    print("\n" + "=" * 78)
    print("F3  distribution-preview truncation at 2.0")
    print("=" * 78)
    coords = ["a_mu", "r_mu", "a_tau", "r_tau", "a_D", "r_D"]
    print("  %-8s %10s %10s %12s %12s" % ("coord", "median", "p95", "max",
                                           "share > 2.0"))
    for c in coords:
        v = (P["absd_" + c] / R[c]).values
        print("  %-8s %10.3f %10.3f %12.3f %11.2f%%"
              % (c, np.median(v), np.percentile(v, 95), v.max(),
                 100.0 * np.mean(v > 2.0)))

    # ================================================== F4 ================
    print("\n" + "=" * 78)
    print("F4  dependence inside the closest tiers (corrected pair set)")
    print("=" * 78)
    order = np.argsort(P["dJ_rmse"].values, kind="stable")
    i_all = P["i"].values
    j_all = P["j"].values
    print("  %-12s %7s %9s %9s %9s %9s"
          % ("tier", "pairs", "samples", "repeated", "max deg", "indep?"))
    tier_rows = []
    for name, frac in [("closest 1%", 0.01), ("closest 0.5%", 0.005),
                       ("closest 0.1%", 0.001)]:
        k = max(1, int(round(len(P) * frac)))
        sel = order[:k]
        si, sj = i_all[sel], j_all[sel]
        cnt = np.bincount(np.concatenate([si, sj]), minlength=15307)
        deg = cnt[cnt > 0]
        n_samp = int(deg.size)
        n_rep = int(np.sum(cnt > 1))
        print("  %-12s %7d %9d %9d %9d %9s"
              % (name, k, n_samp, n_rep, int(deg.max()) if deg.size else 0,
                 "no"))
        tier_rows.append(dict(tier=name, n_pairs=k, distinct_samples=n_samp,
                              repeated_samples=n_rep))

    print("\n  a pair shares a sample with another pair whenever a sample sits")
    print("  in more than one edge; for 'closest 1%%' %.1f%% of the pairs are"
          % (100.0 * np.mean(np.bincount(
              np.concatenate([i_all[order[:112]], j_all[order[:112]]]),
              minlength=15307)[np.concatenate(
                  [i_all[order[:112]], j_all[order[:112]]])] > 1)))
    print("  built on a repeated sample.")


if __name__ == "__main__":
    main()
