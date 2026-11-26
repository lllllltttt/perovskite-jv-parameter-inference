# -*- coding: utf-8 -*-
"""
Error-ranking comparison (EXP2 spec §11).

Per parameter:
  rho_current = Spearman(sigma_current,  |true - mu_current|)
  rho_head_MC = Spearman(sqrt(V_head),    |true - mu_total|)
  rho_latent  = Spearman(sqrt(V_latent),  |true - mu_total|)
  rho_total   = Spearman(sigma_total,     |true - mu_total|)

Primary question: does rho_total improve materially over rho_current?
Effect difference reported (no p-values as primary).

Writes results/error_ranking_comparison.csv
"""
import os, sys, csv
import numpy as np
from scipy.stats import spearmanr

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from exp2_lib import EXP2, PARAM_SHORT

RES = os.path.join(EXP2, "results")
d = np.load(os.path.join(RES, "sample_level_decomposition.npz"))
true = d["params_test"]
err_cur = d["abs_err_current"]
err_lat = d["abs_err_latent"]
sig_head = d["sigma_head"]
sig_lat = d["sigma_latent"]

rho = {}
for key, u in [("current", d["sigma_current"]), ("head_MC", sig_head),
               ("latent", sig_lat), ("total", d["sigma_total"])]:
    rho[key] = np.array([spearmanr(u[:, j], err_lat[:, j])[0] for j in range(9)])

rows = []
for i in range(9):
    rows.append([PARAM_SHORT[i], rho["current"][i], rho["head_MC"][i],
                 rho["latent"][i], rho["total"][i],
                 rho["total"][i] - rho["current"][i]])
with open(os.path.join(RES, "error_ranking_comparison.csv"), "w", newline="") as f:
    w = csv.writer(f)
    w.writerow(["parameter", "rho_current", "rho_head_MC", "rho_latent",
                "rho_total", "delta_total_vs_current"])
    for r in rows:
        w.writerow([r[0]] + ["%.6f" % v for v in r[1:]])
print("saved error_ranking_comparison.csv")

print("\nrho (current / head_MC / latent / total / delta):")
for r in rows:
    print("  %-8s  %.4f / %.4f / %.4f / %.4f  (delta %+.4f)"
          % (r[0], r[1], r[2], r[3], r[4], r[5]))
print("\nmean delta(total-current): %+.4f" % np.mean([r[5] for r in rows]))
