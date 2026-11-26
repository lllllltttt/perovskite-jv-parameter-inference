# -*- coding: utf-8 -*-
"""
Point-prediction comparison (EXP2 spec §12).

mu_current (z_mean) vs mu_total (latent-averaged E_z[mu_theta(z)]) on the
frozen test set, normalized log-parameter space.

Pearson r, normalized MAE, normalized RMSE — same conventions as the frozen
evaluation. This is NOT a new model: it is a different inference rule for the
same frozen weights.

Writes results/point_prediction_comparison.csv
"""
import os, sys, csv
import numpy as np
from scipy.stats import pearsonr

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from exp2_lib import EXP2, PARAM_SHORT

RES = os.path.join(EXP2, "results")
d = np.load(os.path.join(RES, "sample_level_decomposition.npz"))
true = d["params_test"]

def metrics(true, pred):
    r = [pearsonr(true[:, j], pred[:, j])[0] for j in range(9)]
    mae = np.abs(true - pred).mean(axis=0)
    rmse = np.sqrt(((true - pred) ** 2).mean(axis=0))
    return np.array(r), mae, rmse

r_cur, mae_cur, rmse_cur = metrics(true, d["mu_current"])
r_lat, mae_lat, rmse_lat = metrics(true, d["mu_total"])

rows = []
for i in range(9):
    rows.append([PARAM_SHORT[i], r_cur[i], r_lat[i],
                 mae_cur[i], mae_lat[i], rmse_cur[i], rmse_lat[i]])
rows.append(["ALL", r_cur.mean(), r_lat.mean(),
             mae_cur.mean(), mae_lat.mean(), rmse_cur.mean(), rmse_lat.mean()])
with open(os.path.join(RES, "point_prediction_comparison.csv"), "w", newline="") as f:
    w = csv.writer(f)
    w.writerow(["parameter", "pearson_current", "pearson_latent_mean",
                "mae_current", "mae_latent_mean", "rmse_current", "rmse_latent_mean"])
    for r in rows:
        w.writerow([r[0]] + ["%.6f" % v for v in r[1:]])
print("saved point_prediction_comparison.csv")

print("\npearson (current / latent-mean):")
for r in rows:
    print("  %-8s  %.4f / %.4f" % (r[0], r[1], r[2]))
print("\nmean delta Pearson (latent-current): %+.4f" % (r_lat.mean() - r_cur.mean()))
