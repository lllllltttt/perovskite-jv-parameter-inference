# -*- coding: utf-8 -*-
"""
Calibration comparison (EXP2 spec §9, §10).

Three interval constructions, all per-parameter empirical coverage at
nominal 50/80/90/95%:
  A. current        : mu_current ± z * sigma_current
  B. moment-matched : mu_total   ± z * sigma_total
  C. MC mixture     : empirical [mi_lo, mi_hi] quantiles of the
                      Monte-Carlo model-implied predictive distribution
                      (1000 predictive samples per (sample, param))

Writes results/calibration_comparison.csv
"""
import os, sys, csv
import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from exp2_lib import (EXP2, NOMINAL, PARAM_SHORT)

RES = os.path.join(EXP2, "results")
d = np.load(os.path.join(RES, "sample_level_decomposition.npz"))
true = d["params_test"]
levels = sorted(NOMINAL.keys())
L = np.array(levels)

# ---- current ----
cov_cur = np.zeros((9, 4))
# ---- moment-matched ----
cov_mom = np.zeros((9, 4))
# ---- mixture ----
cov_mix = np.zeros((9, 4))
for j, lvl in enumerate(levels):
    zz = NOMINAL[lvl]
    cov_cur[:, j] = np.mean((true >= d["mu_current"] - zz * d["sigma_current"]) &
                            (true <= d["mu_current"] + zz * d["sigma_current"]), axis=0)
    cov_mom[:, j] = np.mean((true >= d["mu_total"] - zz * d["sigma_total"]) &
                            (true <= d["mu_total"] + zz * d["sigma_total"]), axis=0)
    cov_mix[:, j] = np.mean((true >= d["mi_lo"][:, :, j]) &
                            (true <= d["mi_hi"][:, :, j]), axis=0)

rows = []
for i in range(9):
    for j, lvl in enumerate(levels):
        rows.append([PARAM_SHORT[i], "%.2f" % lvl,
                     cov_cur[i, j], cov_mom[i, j], cov_mix[i, j],
                     cov_mom[i, j] - cov_cur[i, j],
                     cov_mix[i, j] - cov_cur[i, j]])

with open(os.path.join(RES, "calibration_comparison.csv"), "w", newline="") as f:
    w = csv.writer(f)
    w.writerow(["parameter", "nominal_level", "coverage_current",
                "coverage_moment_matched", "coverage_mixture",
                "delta_moment_vs_current", "delta_mixture_vs_current"])
    for r in rows:
        w.writerow([r[0], r[1]] + ["%.6f" % v for v in r[2:]])
print("saved calibration_comparison.csv")

# ---- print summary ----
print("\ncoverage 95% (current / moment / mixture):")
for i in range(9):
    print("  %-8s  %.4f / %.4f / %.4f" % (PARAM_SHORT[i], cov_cur[i, -1], cov_mom[i, -1], cov_mix[i, -1]))
print("\n95%% deltas: moment-cur: min %.4f max %.4f | mix-cur: min %.4f max %.4f"
      % (cov_mom[:, -1].min() - cov_cur[:, -1].min(),
         (cov_mom - cov_cur)[:, -1].max(),
         (cov_mix - cov_cur)[:, -1].min(),
         (cov_mix - cov_cur)[:, -1].max()))
md = np.abs(cov_mom - cov_mix)
print("max |moment - mixture| over all params/levels: %.4f (%.4f at 95%% level)"
      % (md.max(), np.abs(cov_mom[:, -1] - cov_mix[:, -1]).max()))
