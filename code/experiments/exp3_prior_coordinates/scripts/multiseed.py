# -*- coding: utf-8 -*-
"""
EXP3 §13-14 — multi-seed and architecture robustness using the five EXP1
leakage-free checkpoints (never retrained here).

For every (family, seed) in {vae, det_ae, mlp} x 5 seeds:
  read eval_bundle.npz (param_mu, normalized test predictions)
  -> invert with THAT RUN's train-only param scaler -> log10 physical
  -> compute the six prior coordinates -> Pearson / MAE-decades / RMSE-decades

Outputs:
  results/exp1_seed_coordinate_recoverability.csv
  results/architecture_coordinate_summary.csv   (mean +/- SD Pearson per family)
Frozen Stage-I model stays the manuscript reference (not pooled with these runs).
"""
import os, sys, csv
import numpy as np
from scipy.stats import pearsonr

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from exp3_lib import (EXP3, EXP1, COORDS, FAMILIES, SEEDS, coords_from_log10,
                      lf_test_true_log10, lf_norm_to_log10, exp1_eval_bundle)

RES = os.path.join(EXP3, "results")

# ---- cross-check: marginal Pearson vs EXP1 per_seed_metrics.csv ---------
ref = {}
with open(os.path.join(EXP1, "results", "per_seed_metrics.csv"), newline="") as f:
    for r in csv.DictReader(f):
        ref[(r["model"], int(r["seed"]), r["parameter"])] = float(r["pearson_r"])

PARAM_MAP = {"mu_n": "mu_n", "mu_p": "mu_p", "tau_n": "tau_n", "tau_p": "tau_p",
             "Nc": "Nc", "Nv": "Nv"}
print("cross-check eval_bundle marginal Pearson vs EXP1 per_seed_metrics.csv:")
max_dev = 0.0
for family in FAMILIES:
    for seed in SEEDS:
        eb = exp1_eval_bundle(family, seed)
        pred = lf_norm_to_log10(eb["param_mu"].astype(np.float64))
        true = lf_test_true_log10()
        for j, name in enumerate(PARAM_MAP):
            r = pearsonr(true[:, j], pred[:, j])[0]
            dev = abs(r - ref[(family, seed, name)])
            max_dev = max(max_dev, dev)
print("  max |recomputed - reported| marginal Pearson = %.2e  -> %s"
      % (max_dev, "OK" if max_dev < 1e-4 else "CHECK"))

# ---- per-seed coordinate recoverability --------------------------------
true_L = lf_test_true_log10()
C_true = coords_from_log10(true_L)

rows = []
for family in FAMILIES:
    for seed in SEEDS:
        eb = exp1_eval_bundle(family, seed)
        pred_L = lf_norm_to_log10(eb["param_mu"].astype(np.float64))
        C_pred = coords_from_log10(pred_L)
        for ci, cname in enumerate(COORDS):
            t, p = C_true[:, ci], C_pred[:, ci]
            rows.append(dict(family=family, seed=seed, coordinate=cname,
                             pearson_r=float(pearsonr(t, p)[0]),
                             mae_decades=float(np.mean(np.abs(t - p))),
                             rmse_decades=float(np.sqrt(np.mean((t - p) ** 2)))))

with open(os.path.join(RES, "exp1_seed_coordinate_recoverability.csv"), "w", newline="") as f:
    w = csv.writer(f)
    w.writerow(["family", "seed", "coordinate", "pearson_r", "mae_decades", "rmse_decades"])
    for r in rows:
        w.writerow([r["family"], r["seed"], r["coordinate"],
                    "%.6f" % r["pearson_r"], "%.6f" % r["mae_decades"],
                    "%.6f" % r["rmse_decades"]])
print("saved exp1_seed_coordinate_recoverability.csv")

# ---- architecture summary (mean +/- SD Pearson across 5 seeds) ----------
with open(os.path.join(RES, "architecture_coordinate_summary.csv"), "w", newline="") as f:
    w = csv.writer(f)
    w.writerow(["family", "coordinate", "pearson_mean", "pearson_sd",
                "mae_decades_mean", "mae_decades_sd"])
    print("\narchitecture mean +/- SD Pearson over 5 seeds:")
    print("%-7s " % "coord" + "  ".join("%-8s" % fam for fam in FAMILIES))
    for ci, cname in enumerate(COORDS):
        line = "%-7s " % cname
        for family in FAMILIES:
            rs = [r["pearson_r"] for r in rows if r["family"] == family and r["coordinate"] == cname]
            ms = [r["mae_decades"] for r in rows if r["family"] == family and r["coordinate"] == cname]
            mn, sd = float(np.mean(rs)), float(np.std(rs))
            mn_m, sd_m = float(np.mean(ms)), float(np.std(ms))
            w.writerow([family, cname, "%.4f" % mn, "%.4f" % sd,
                        "%.4f" % mn_m, "%.4f" % sd_m])
            line += "  %-8s" % ("%.3f±%.3f" % (mn, sd))
        print(line)
print("saved architecture_coordinate_summary.csv")
