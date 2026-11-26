# -*- coding: utf-8 -*-
"""
Phase 4 + 6 + 7 — PRIMARY REPLICATION METRICS, CALIBRATION, UNCERTAINTY-ERROR
Independent dataset validation of frozen VAE-v6.

All metrics in NORMALIZED LOG10 PARAMETER SPACE, exactly the locked-manuscript
convention (VAE_v6_eval_fixed.py).

Reference (original test set, N=15307) values are hard-coded from the verified
evaluation_fixed/*.csv outputs (see FROZEN_ARTIFACT_MANIFEST.md) and are never
overwritten.

Outputs:
  independent_validation/independent_parameter_metrics.csv
  independent_validation/independent_calibration.csv
  independent_validation/independent_uncertainty_error.csv
"""
import os, csv
import numpy as np
from scipy.stats import pearsonr, spearmanr

BASE = r"E:\project\work1"
OUT = os.path.join(BASE, "independent_validation")

PARAM_NAMES = ["mu_n_pvk", "mu_p_pvk", "tau_n_pvk", "tau_p_pvk",
               "Nc_eff_pvk", "Nv_eff_pvk", "tau_ETL", "tau_HTL", "rad_c"]
SHORT = ["mu_n", "mu_p", "tau_n", "tau_p", "Nc", "Nv", "tau_ETL", "tau_HTL", "rad_c"]

NOMINAL = {0.50: 0.67448975, 0.80: 1.28155157, 0.90: 1.64485363, 0.95: 1.95996398}

# ----------------------------------------------------------------------
# Verified ORIGINAL test-set reference values (locked manuscript / eval_fixed)
# ----------------------------------------------------------------------
ORIG_PEARSON = [0.906268, 0.919434, 0.878266, 0.880803, 0.909047,
                0.895604, 0.593605, 0.719923, 0.559174]
ORIG_MAE = [0.074727, 0.070350, 0.090849, 0.092136, 0.058824,
            0.064946, 0.188106, 0.157899, 0.191807]
ORIG_RMSE = [0.101433, 0.095013, 0.128383, 0.127054, 0.079434,
             0.084025, 0.234346, 0.202061, 0.240335]
ORIG_CAL95 = [0.947475, 0.952244, 0.958320, 0.959692, 0.946364,
              0.949892, 0.969164, 0.966682, 0.966421]
ORIG_SPEARMAN = [0.398191, 0.334319, 0.645906, 0.621839, 0.353014,
                 0.244391, 0.377232, 0.464704, 0.414716]

# ----------------------------------------------------------------------
# Load independent normalized data + predictions
# ----------------------------------------------------------------------
d = np.load(os.path.join(OUT, "preprocessed_independent.npz"))
P_norm = d["P_norm"].astype(np.float64)
J_norm = d["J_norm"].astype(np.float32)

# predictions were stored in the big CSV; reload compactly from it
import pandas as pd
pred_df = pd.read_csv(os.path.join(OUT, "independent_predictions.csv"))
mu_norm = pred_df[[("pred_norm_%s" % c) for c in PARAM_NAMES]].values.astype(np.float64)
sigma = pred_df[[("sigma_%s" % c) for c in PARAM_NAMES]].values.astype(np.float64)
N = len(pred_df)
print("independent N =", N)
assert P_norm.shape[0] == N == mu_norm.shape[0] == sigma.shape[0]

true = P_norm
error = np.abs(true - mu_norm)

# =====================================================================
# PHASE 4 — point metrics
# =====================================================================
pearson = np.zeros(9)
mae = np.zeros(9)
rmse = np.zeros(9)
for i in range(9):
    r, _ = pearsonr(true[:, i], mu_norm[:, i])
    pearson[i] = r
    mae[i] = float(np.mean(error[:, i]))
    rmse[i] = float(np.sqrt(np.mean((true[:, i] - mu_norm[:, i]) ** 2)))

print("\n===== PHASE 4 — POINT PREDICTION (normalized log10 space) =====")
print("%-10s %8s %8s %8s   %8s %8s %8s" % ("param", "orig r", "indep r", "delta r",
                                             "orig MAE", "indep MAE", "orig RMSE"))
with open(os.path.join(OUT, "independent_parameter_metrics.csv"), "w", newline="") as f:
    w = csv.writer(f)
    w.writerow(["parameter", "short", "original_test_pearson", "independent_pearson",
                "delta_pearson", "original_mae", "independent_mae",
                "original_rmse", "independent_rmse"])
    for i in range(9):
        w.writerow([PARAM_NAMES[i], SHORT[i],
                    "%.6f" % ORIG_PEARSON[i], "%.6f" % pearson[i],
                    "%.6f" % (pearson[i] - ORIG_PEARSON[i]),
                    "%.6f" % ORIG_MAE[i], "%.6f" % mae[i],
                    "%.6f" % ORIG_RMSE[i], "%.6f" % rmse[i]])
        print("%-10s %8.4f %8.4f %+8.4f   %8.4f %8.4f %8.4f"
              % (SHORT[i], ORIG_PEARSON[i], pearson[i], pearson[i] - ORIG_PEARSON[i],
                 ORIG_MAE[i], mae[i], ORIG_RMSE[i]))
    # mean row
    w.writerow(["MEAN", "mean", "%.6f" % np.mean(ORIG_PEARSON), "%.6f" % np.mean(pearson),
                "%.6f" % (np.mean(pearson) - np.mean(ORIG_PEARSON)),
                "%.6f" % np.mean(ORIG_MAE), "%.6f" % np.mean(mae),
                "%.6f" % np.mean(ORIG_RMSE), "%.6f" % np.mean(rmse)])
print("%-10s %8.4f %8.4f %+8.4f" % ("mean", np.mean(ORIG_PEARSON), np.mean(pearson),
                                     np.mean(pearson) - np.mean(ORIG_PEARSON)))

# =====================================================================
# PHASE 6 — predictive calibration (frozen sigma, no recalibration)
# =====================================================================
levels = sorted(NOMINAL.keys())
emp_cov = np.zeros((9, len(levels)))
for j, lvl in enumerate(levels):
    zz = NOMINAL[lvl]
    lo = mu_norm - zz * sigma
    hi = mu_norm + zz * sigma
    emp_cov[:, j] = np.mean((true >= lo) & (true <= hi), axis=0)

print("\n===== PHASE 6 — CALIBRATION (frozen sigma, no recalibration) =====")
print("%-10s %8s %8s %8s %8s   %8s %8s" % ("param", "50%", "80%", "90%", "95%",
                                             "orig95", "delta95"))
with open(os.path.join(OUT, "independent_calibration.csv"), "w", newline="") as f:
    w = csv.writer(f)
    w.writerow(["parameter", "short", "nominal", "z", "independent_coverage",
                "original_95_coverage"])
    for i in range(9):
        for j, lvl in enumerate(levels):
            w.writerow([PARAM_NAMES[i], SHORT[i], "%.2f" % lvl, "%.8f" % NOMINAL[lvl],
                        "%.6f" % emp_cov[i, j],
                        "%.6f" % ORIG_CAL95[i] if lvl == 0.95 else ""])
        print("%-10s %8.4f %8.4f %8.4f %8.4f   %8.4f %+8.4f"
              % (SHORT[i], emp_cov[i, 0], emp_cov[i, 1], emp_cov[i, 2], emp_cov[i, 3],
                 ORIG_CAL95[i], emp_cov[i, 3] - ORIG_CAL95[i]))
mean95_orig = float(np.mean(ORIG_CAL95))
mean95_ind = float(np.mean(emp_cov[:, levels.index(0.95)]))
print("%-10s %8s %8s %8s %8.4f   %8.4f %+8.4f"
      % ("mean", "", "", "", mean95_ind, mean95_orig, mean95_ind - mean95_orig))

# =====================================================================
# PHASE 7 — uncertainty-error association
# =====================================================================
spearman = np.zeros(9)
spearman_p = np.zeros(9)
for i in range(9):
    rho, p = spearmanr(sigma[:, i], error[:, i])
    spearman[i] = rho
    spearman_p[i] = p

print("\n===== PHASE 7 — SPEARMAN(sigma, |error|) =====")
print("%-10s %8s %8s %8s" % ("param", "orig rho", "indep rho", "delta"))
with open(os.path.join(OUT, "independent_uncertainty_error.csv"), "w", newline="") as f:
    w = csv.writer(f)
    w.writerow(["parameter", "short", "original_spearman", "independent_spearman",
                "delta_spearman", "p_value"])
    for i in range(9):
        w.writerow([PARAM_NAMES[i], SHORT[i], "%.6f" % ORIG_SPEARMAN[i],
                    "%.6f" % spearman[i], "%.6f" % (spearman[i] - ORIG_SPEARMAN[i]),
                    "%.3e" % spearman_p[i]])
        print("%-10s %8.4f %8.4f %+8.4f" % (SHORT[i], ORIG_SPEARMAN[i], spearman[i],
                                            spearman[i] - ORIG_SPEARMAN[i]))
    w.writerow(["MEAN", "mean", "%.6f" % np.mean(ORIG_SPEARMAN), "%.6f" % np.mean(spearman),
                "%.6f" % (np.mean(spearman) - np.mean(ORIG_SPEARMAN)), ""])
print("%-10s %8.4f %8.4f %+8.4f" % ("mean", np.mean(ORIG_SPEARMAN), np.mean(spearman),
                                     np.mean(spearman) - np.mean(ORIG_SPEARMAN)))

print("\nPhase 4/6/7 complete.")
