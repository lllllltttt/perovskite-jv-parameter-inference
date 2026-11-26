# -*- coding: utf-8 -*-
"""
EXP3 §7-8 — effective-prior geometry after filtering + variance geometry.

For BOTH the original retained population (N=102046) and the test population
(N=15307), in log10 physical coordinates:
  * per-coordinate min/max/mean/SD/IQR           -> results/prior_geometry_retained.csv
  * per-pair (a, r) stats: SD(a), SD(0.5r), Var(a), Var(0.5r), Cov(a, 0.5r),
    Pearson/Spearman(a, r), marginal pair correlation -> results/pair_geometry.csv

Analysis-only. Never trains.
"""
import os, sys, csv
import numpy as np
from scipy.stats import pearsonr, spearmanr

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from exp3_lib import (EXP3, COORDS, PAIR_ORDER, PAIRS, coords_from_log10,
                      frozen_test, frozen_norm_to_log10, frozen_retained_params_log10)

RES = os.path.join(EXP3, "results")
os.makedirs(RES, exist_ok=True)

# ---- populations -------------------------------------------------------
ret_L = frozen_retained_params_log10()               # (102046, 9)
ret_C = coords_from_log10(ret_L)
tst_L = frozen_norm_to_log10(frozen_test()["params_test"])   # (15307, 9)
tst_C = coords_from_log10(tst_L)
N_ret, N_tst = ret_L.shape[0], tst_L.shape[0]
print("retained N = %d (must be 102046), test N = %d (must be 15307)" % (N_ret, N_tst))
assert N_ret == 102046 and N_tst == 15307

# ---- prior_geometry_retained.csv --------------------------------------
with open(os.path.join(RES, "prior_geometry_retained.csv"), "w", newline="") as f:
    w = csv.writer(f)
    w.writerow(["coordinate", "population", "min", "max", "mean", "sd", "q25", "median", "q75"])
    rows = []
    for pop_name, C in (("retained", ret_C), ("test", tst_C)):
        for ci, cname in enumerate(COORDS):
            c = C[:, ci]
            w.writerow([cname, pop_name, "%.6f" % c.min(), "%.6f" % c.max(),
                        "%.6f" % c.mean(), "%.6f" % c.std(),
                        "%.6f" % np.percentile(c, 25), "%.6f" % np.median(c),
                        "%.6f" % np.percentile(c, 75)])
            rows.append((cname, pop_name, c))
print("saved prior_geometry_retained.csv")

# print coordinate geometry summary
print("\ncoordinate geometry (log10 decades):")
print("%-6s %-8s %8s %8s %8s %8s" % ("coord", "pop", "min", "max", "mean", "sd"))
for cname, pop_name, c in rows:
    print("%-6s %-8s %8.3f %8.3f %8.3f %8.3f" % (cname, pop_name, c.min(), c.max(), c.mean(), c.std()))

# ---- pair_geometry.csv -------------------------------------------------
print("\nmanuscript marginal pair correlation reference: mu_n/mu_p ~0.94, tau ~0.99, Nc/Nv ~0.90")
with open(os.path.join(RES, "pair_geometry.csv"), "w", newline="") as f:
    w = csv.writer(f)
    w.writerow(["pair", "population", "sd_average", "sd_half_log_ratio",
                "variance_average", "variance_half_log_ratio", "covariance",
                "pearson_average_ratio", "spearman_average_ratio",
                "marginal_pair_pearson", "marginal_pair_spearman"])
    for pi, pname in enumerate(PAIR_ORDER):
        ia, ir = 2 * pi, 2 * pi + 1
        i_n, i_p = PAIRS[pname]
        for pop_name, C, L in (("retained", ret_C, ret_L), ("test", tst_C, tst_L)):
            a, r = C[:, ia], C[:, ir]
            half = 0.5 * r
            sd_a, sd_h = a.std(), half.std()
            var_a, var_h = a.var(), half.var()
            cov_ah = np.mean((a - a.mean()) * (half - half.mean()))
            r_ar, s_ar = pearsonr(a, r)[0], spearmanr(a, r)[0]
            r_mp = pearsonr(L[:, i_n], L[:, i_p])[0]
            s_mp = spearmanr(L[:, i_n], L[:, i_p])[0]
            w.writerow([pname, pop_name, "%.6f" % sd_a, "%.6f" % sd_h,
                        "%.6f" % var_a, "%.6f" % var_h, "%.6f" % cov_ah,
                        "%.6f" % r_ar, "%.6f" % s_ar, "%.6f" % r_mp, "%.6f" % s_mp])
            print("%-8s %-8s SD(a)=%.4f SD(0.5r)=%.4f ratio=%.3f | r(a,r)=%+.3f | "
                  "marginal r=%+.4f" % (pname, pop_name, sd_a, sd_h, sd_a / sd_h,
                                        r_ar, r_mp))
print("saved pair_geometry.csv")
