# -*- coding: utf-8 -*-
"""
EXP3 §4-6, 9-10 — frozen-model recoverability in the 6 natural prior
coordinates, the central paired-coordinate comparison, and the no-J-V
train-only prior baseline (Skill_RMSE, MAE_reduction).

All metrics in LOG10 PHYSICAL space (decades).
Baseline = predict the TRAINING-set mean/median per coordinate (train-only;
no val/test targets, no J-V inputs ever used to build it).

Outputs:
  results/frozen_coordinate_recoverability.csv
  results/paired_coordinate_comparison.csv
  results/original_param_baseline.csv   (no-J baseline for the 6 paired marginals)
"""
import os, sys, csv
import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from exp3_lib import (EXP3, COORDS, PARAM_NAMES, PAIR_ORDER, PAIRS,
                      coords_from_log10, coord_metrics, frozen_test,
                      frozen_norm_to_log10, frozen_train_params_log10,
                      frozen_pred_log10)

RES = os.path.join(EXP3, "results")
os.makedirs(RES, exist_ok=True)

# ---- predictions & truth (frozen, log10 physical) ----------------------
true_L = frozen_norm_to_log10(frozen_test()["params_test"])
pred_L = frozen_pred_log10()
C_true = coords_from_log10(true_L)
C_pred = coords_from_log10(pred_L)

# ---- train-only prior baseline (per coordinate) ------------------------
train_L = frozen_train_params_log10()          # (71432, 9) log10 physical
train_C = coords_from_log10(train_L)
base_mean = train_C.mean(axis=0)               # (6,)
base_median = np.median(train_C, axis=0)       # (6,)
print("train N = %d (train-only baseline)" % train_L.shape[0])

# ---- per-coordinate metrics + skill ------------------------------------
COORD_NAMES = ["a_mu", "r_mu", "a_tau", "r_tau", "a_D", "r_D"]
with open(os.path.join(RES, "frozen_coordinate_recoverability.csv"), "w", newline="") as f:
    w = csv.writer(f)
    w.writerow(["coordinate", "pearson_r", "spearman_rho", "mae_decades",
                "rmse_decades", "median_abs_log_error", "p90_abs_log_error",
                "median_abs_ratio_error_decades", "ratio_factor",
                "prior_mean_rmse", "prior_median_mae", "skill_rmse", "mae_reduction"])
    for ci, cname in enumerate(COORD_NAMES):
        t, p = C_true[:, ci], C_pred[:, ci]
        m = coord_metrics(t, p)
        mse_model = np.mean((t - p) ** 2)
        rmse_prior_mean = float(np.sqrt(np.mean((t - base_mean[ci]) ** 2)))
        mae_prior_median = float(np.mean(np.abs(t - base_median[ci])))
        skill = 1.0 - mse_model / (rmse_prior_mean ** 2)
        mae_red = 1.0 - m["mae_decades"] / mae_prior_median
        is_ratio = cname.startswith("r_")
        w.writerow([cname, "%.6f" % m["pearson_r"], "%.6f" % m["spearman_rho"],
                    "%.6f" % m["mae_decades"], "%.6f" % m["rmse_decades"],
                    "%.6f" % m["median_abs_log_error"], "%.6f" % m["p90_abs_log_error"],
                    "%.6f" % m["median_abs_ratio_error"] if is_ratio else "",
                    "%.4f" % m["ratio_factor"] if is_ratio else "",
                    "%.6f" % rmse_prior_mean, "%.6f" % mae_prior_median,
                    "%.6f" % skill, "%.6f" % mae_red])
        print("%-5s  r=%.4f  rho=%.4f  MAE=%.4f  RMSE=%.4f  med=%.4f  p90=%.4f  "
              "priorRMSE=%.4f  skill=%.3f  maeRed=%.3f%s" %
              (cname, m["pearson_r"], m["spearman_rho"], m["mae_decades"],
               m["rmse_decades"], m["median_abs_log_error"], m["p90_abs_log_error"],
               rmse_prior_mean, skill, mae_red,
               "  factor=%.3f" % m["ratio_factor"] if is_ratio else ""))
print("saved frozen_coordinate_recoverability.csv")

# ---- central paired-coordinate comparison (spec §6) ---------------------
with open(os.path.join(RES, "paired_coordinate_comparison.csv"), "w", newline="") as f:
    w = csv.writer(f)
    w.writerow(["pair", "marginal1", "r_marginal1", "marginal2", "r_marginal2",
                "shared_a", "r_shared", "mae_shared_decades",
                "ratio_r", "r_ratio", "mae_ratio_decades"])
    for pi, pname in enumerate(PAIR_ORDER):
        i_n, i_p = PAIRS[pname]
        ia, ir = 2 * pi, 2 * pi + 1
        r1 = coord_metrics(true_L[:, i_n], pred_L[:, i_n])["pearson_r"]
        r2 = coord_metrics(true_L[:, i_p], pred_L[:, i_p])["pearson_r"]
        ma = coord_metrics(C_true[:, ia], C_pred[:, ia])
        mr = coord_metrics(C_true[:, ir], C_pred[:, ir])
        w.writerow([pname, PARAM_NAMES[i_n], "%.4f" % r1, PARAM_NAMES[i_p],
                    "%.4f" % r2, COORD_NAMES[ia], "%.4f" % ma["pearson_r"],
                    "%.4f" % ma["mae_decades"], COORD_NAMES[ir],
                    "%.4f" % mr["pearson_r"], "%.4f" % mr["mae_decades"]])
        print("%-8s marg r=(%.3f, %.3f)  a r=%.3f MAE=%.3f  |  r_ratio r=%.3f MAE=%.3f"
              % (pname, r1, r2, ma["pearson_r"], ma["mae_decades"],
                 mr["pearson_r"], mr["mae_decades"]))
print("saved paired_coordinate_comparison.csv")

# ---- original-parameter no-J baseline (spec §10) ------------------------
with open(os.path.join(RES, "original_param_baseline.csv"), "w", newline="") as f:
    w = csv.writer(f)
    w.writerow(["parameter", "pearson_r", "prior_mean_rmse", "prior_median_mae",
                "skill_rmse", "mae_reduction"])
    for j in (0, 1, 2, 3, 4, 5):   # the six paired bulk parameters only
        t, p = true_L[:, j], pred_L[:, j]
        r = coord_metrics(t, p)["pearson_r"]
        rmse_pm = float(np.sqrt(np.mean((t - train_L[:, j].mean()) ** 2)))
        mae_pm = float(np.mean(np.abs(t - np.median(train_L[:, j]))))
        mae_model = float(np.mean(np.abs(t - p)))
        skill = 1.0 - np.mean((t - p) ** 2) / (rmse_pm ** 2)
        red = 1.0 - mae_model / mae_pm
        w.writerow([PARAM_NAMES[j], "%.4f" % r, "%.4f" % rmse_pm, "%.4f" % mae_pm,
                    "%.4f" % skill, "%.4f" % red])
        print("param %-6s r=%.4f  skill=%.3f  maeRed=%.3f" % (PARAM_NAMES[j], r, skill, red))
print("saved original_param_baseline.csv")
